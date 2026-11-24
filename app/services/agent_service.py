"""Grounded LLM explanations for deterministic meal-plan recommendations."""

import json
import logging

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.core.config import settings
from app.data.food_repository import load_foods
from app.schemas.agent import (
    AgentFoodReason,
    AgentRecommendationRequest,
    AgentRecommendationResponse,
)
from app.schemas.meals import MealPlanResponse
from app.schemas.nutrition import CalorieResponse
from app.services.bmi_service import calculate_bmi
from app.services.calorie_service import calculate_calorie_need
from app.services.meal_plan_service import generate_meal_plan

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = (
    "AI explanation is unavailable; the deterministic meal plan is shown instead."
)
SAFETY_NOTE = (
    "This is general information, not diagnosis or treatment. "
    "For diabetes, high blood pressure, PCOS, allergies, or other medical "
    "concerns, consult a qualified clinician or dietitian."
)
SYSTEM_INSTRUCTION = (
    "You explain a healthy-food plan using only the supplied profile summary, "
    "calculated values, and candidate food records. Do not invent nutrition "
    "values, ingredients, foods, or medical effects. The candidates have "
    "already passed availability, preference, and exclusion filters. Do not diagnose, "
    "prescribe treatment, or claim that food cures a condition. Return only "
    "JSON with a concise 'summary' string and a 'reasons' array containing "
    "exactly one object per supplied food ID, each with 'food_id' and 'reason'."
)


class _LLMFoodReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    food_id: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=500)


class _LLMExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    reasons: list[_LLMFoodReason] = Field(min_length=1)


def _fallback_reasons(plan: MealPlanResponse) -> list[AgentFoodReason]:
    reasons_by_food: dict[str, AgentFoodReason] = {}
    for meal in plan.meals:
        for item in meal.items:
            reasons_by_food.setdefault(
                item.food_id,
                AgentFoodReason(
                    food_id=item.food_id,
                    reason="Selected from the foods available for your plan.",
                ),
            )
    return list(reasons_by_food.values())


def _build_context(
    request: AgentRecommendationRequest,
    plan: MealPlanResponse,
) -> tuple[dict[str, object], list[str]]:
    foods_by_id = {food.id: food for food in load_foods()}
    candidate_foods: list[dict[str, object]] = []
    selected_ids: list[str] = []

    for meal in plan.meals:
        for item in meal.items:
            food = foods_by_id[item.food_id]
            candidate_foods.append(
                {
                    "food_id": food.id,
                    "name": food.name,
                    "meal": meal.meal,
                    "servings": item.servings,
                    "serving_g": food.serving_g,
                    "calories_kcal_per_serving": food.calories_kcal,
                    "protein_g_per_serving": food.protein_g,
                    "carbohydrates_g_per_serving": food.carbs_g,
                    "fat_g_per_serving": food.fat_g,
                    "fibre_g_per_serving": food.fibre_g,
                }
            )
            if item.food_id not in selected_ids:
                selected_ids.append(item.food_id)

    calorie_estimate = calculate_calorie_need(request.profile)
    context: dict[str, object] = {
        "goal": request.profile.health_goal.value,
        "available_foods": [
            food.value for food in request.available_foods
        ],
        "available_food_ids": request.available_food_ids,
        "food_preferences": request.profile.food_preferences,
        "bmi": calculate_bmi(request.profile.height_cm, request.profile.weight_kg),
        "planned_daily_calorie_target_kcal": plan.daily_calorie_target_kcal,
        "planned_daily_nutrition": plan.daily_nutrition.model_dump(mode="json"),
        "calorie_target_range_kcal": {
            "minimum": calorie_estimate.goal_target_calories_min_kcal,
            "maximum": calorie_estimate.goal_target_calories_max_kcal,
        },
        "candidate_foods": candidate_foods,
    }
    return context, selected_ids


def _request_explanation(context: dict[str, object]) -> _LLMExplanation:
    if not settings.llm_api_key or not settings.llm_model:
        raise ValueError("LLM credentials or model are not configured.")

    provider = settings.llm_provider.strip().lower()
    prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Actual recommendation context:\n"
        f"{json.dumps(context, separators=(',', ':'))}"
    )

    if provider == "gemini":
        if genai is None or types is None:
            raise RuntimeError("The Google Gen AI SDK is not installed.")
        client = genai.Client(api_key=settings.llm_api_key)
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=_LLMExplanation,
                http_options=types.HttpOptions(
                    timeout=int(settings.llm_timeout_seconds * 1000),
                ),
            ),
        )
        content = getattr(response, "text", None)
    elif provider == "openai":
        response = httpx.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {
                        "role": "user",
                        "content": json.dumps(context, separators=(",", ":")),
                    },
                ],
            },
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. Use 'gemini' or 'openai'."
        )

    if not isinstance(content, str):
        raise ValueError("The LLM returned a non-text response.")
    return _LLMExplanation.model_validate(json.loads(content))


def _llm_error_category(error: Exception) -> str:
    message = str(error).lower()
    status = getattr(error, "status_code", None)
    code = getattr(error, "code", None)
    combined = f"{status or ''} {code or ''} {message}"

    if "api key" in combined or "api_key" in combined or "unauth" in combined:
        return "invalid API key"
    if "quota" in combined or "resource exhausted" in combined or "429" in combined:
        return "API quota exhausted"
    if "model" in combined and (
        "not found" in combined or "unsupported" in combined or "404" in combined
    ):
        return "unsupported or unavailable model"
    if isinstance(error, (httpx.TimeoutException, TimeoutError)):
        return "network timeout"
    if isinstance(error, httpx.HTTPError):
        return "network or HTTP provider error"
    if isinstance(error, (ConnectionError, OSError)):
        return "network connection error"
    return "provider request or response error"


def recommend_meals(
    request: AgentRecommendationRequest,
) -> AgentRecommendationResponse:
    """Calculate and plan deterministically, using an LLM only for explanation."""
    plan = generate_meal_plan(request)
    calorie_result = calculate_calorie_need(request.profile)
    calorie_response = CalorieResponse.model_validate(calorie_result.__dict__)
    bmi = calculate_bmi(request.profile.height_cm, request.profile.weight_kg)
    context, selected_ids = _build_context(request, plan)
    assumptions = [
        *calorie_result.assumptions,
        "Meal nutrient values come from the structured food dataset and are scaled by servings.",
    ]

    try:
        explanation = _request_explanation(context)
        reason_ids = [reason.food_id for reason in explanation.reasons]
        if (
            len(reason_ids) != len(set(reason_ids))
            or set(reason_ids) != set(selected_ids)
        ):
            raise ValueError("The LLM response referenced unexpected food IDs.")
    except Exception as error:
        logger.warning(
            "LLM explanation unavailable; using deterministic result (%s).",
            _llm_error_category(error),
        )
        goal_label = {
            "lose_weight": "weight loss",
            "maintain_weight": "weight maintenance",
            "gain_weight": "weight gain",
        }[request.profile.health_goal.value]
        return AgentRecommendationResponse(
            summary=(
                f"Your plan is ready, with {goal_label} in mind."
            ),
            meal_plan=plan,
            bmi=bmi,
            calorie_estimate=calorie_response,
            reasons=_fallback_reasons(plan),
            assumptions=assumptions,
            safety_note=SAFETY_NOTE,
            source="deterministic",
            message=FALLBACK_MESSAGE,
        )

    return AgentRecommendationResponse(
        summary=explanation.summary,
        meal_plan=plan,
        bmi=bmi,
        calorie_estimate=calorie_response,
        reasons=[
            AgentFoodReason(food_id=reason.food_id, reason=reason.reason)
            for reason in explanation.reasons
        ],
        assumptions=assumptions,
        safety_note=SAFETY_NOTE,
        source="llm",
    )
