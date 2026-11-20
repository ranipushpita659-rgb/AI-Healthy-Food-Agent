"""Tests for constrained AI explanations and deterministic fallbacks."""

import json

import httpx

from app.core.config import settings
from app.schemas.agent import AgentRecommendationRequest
from app.services.agent_service import recommend_meals


def make_request() -> AgentRecommendationRequest:
    return AgentRecommendationRequest.model_validate(
        {
            "profile": {
                "age": 30,
                "gender": "female",
                "height_cm": 165,
                "weight_kg": 60,
                "activity_level": "moderate",
                "health_goal": "maintain_weight",
            },
            "daily_calorie_target": 2000,
        }
    )


def test_missing_llm_credentials_returns_deterministic_recommendation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.setattr(settings, "llm_model", None)

    result = recommend_meals(make_request())

    assert result.source == "deterministic"
    assert result.meal_plan.meals
    assert result.message and "unavailable" in result.message
    assert {reason.food_id for reason in result.reasons} == {
        item.food_id
        for meal in result.meal_plan.meals
        for item in meal.items
    }
    assert all("slot" not in reason.reason for reason in result.reasons)


def test_llm_timeout_returns_deterministic_recommendation(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "test-model")

    def timeout(url, **request_options):
        assert url.endswith("/chat/completions")
        assert request_options["timeout"] == settings.llm_timeout_seconds
        raise httpx.ReadTimeout("request timed out")

    monkeypatch.setattr("app.services.agent_service.httpx.post", timeout)

    result = recommend_meals(make_request())

    assert result.source == "deterministic"
    assert result.meal_plan.daily_nutrition.calories_kcal > 0
    assert result.message is not None


def test_llm_cannot_return_unselected_food_ids(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "test-model")
    response = httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"summary":"A plan","reasons":['
                            '{"food_id":"not-in-plan","reason":"Try this."}]}'
                        )
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://llm.test/chat/completions"),
    )

    def return_response(url, **request_options):
        assert url.endswith("/chat/completions")
        assert request_options["json"]["model"] == settings.llm_model
        return response

    monkeypatch.setattr(
        "app.services.agent_service.httpx.post",
        return_response,
    )

    result = recommend_meals(make_request())

    assert result.source == "deterministic"
    allowed_ids = {
        item.food_id
        for meal in result.meal_plan.meals
        for item in meal.items
    }
    assert {reason.food_id for reason in result.reasons} == allowed_ids


def test_llm_explanation_is_accepted_when_it_uses_only_plan_foods(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "test-model")

    def explain(url, **request_kwargs):
        assert url.endswith("/chat/completions")
        messages = request_kwargs["json"]["messages"]
        context = json.loads(messages[1]["content"])
        assert "age" not in context
        assert "gender" not in context
        assert context["planned_daily_calorie_target_kcal"] == 2000
        food_ids = list(
            dict.fromkeys(
                food["food_id"] for food in context["candidate_foods"]
            )
        )
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "summary": "A data-grounded meal plan.",
                                "reasons": [
                                    {
                                        "food_id": food_id,
                                        "reason": "Selected from the supplied data.",
                                    }
                                    for food_id in food_ids
                                ],
                            }
                        )
                    }
                }
            ]
        }
        return httpx.Response(
            200,
            json=body,
            request=httpx.Request("POST", "https://llm.test/chat/completions"),
        )

    monkeypatch.setattr("app.services.agent_service.httpx.post", explain)

    result = recommend_meals(make_request())

    assert result.source == "llm"
    assert result.summary == "A data-grounded meal plan."
    assert result.message is None
