"""Schemas for grounded, backend-mediated AI recommendations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.meals import MealPlanRequest, MealPlanResponse
from app.schemas.nutrition import CalorieResponse


class AgentRecommendationRequest(MealPlanRequest):
    """Validated profile and optional calorie target for a recommendation."""


class AgentFoodReason(BaseModel):
    """A short explanation tied to one food selected by the planner."""

    model_config = ConfigDict(extra="forbid")

    food_id: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=500)


class AgentRecommendationResponse(BaseModel):
    """Plan, calculations, grounded explanations, and provider status."""

    summary: str
    meal_plan: MealPlanResponse
    bmi: float = Field(gt=0)
    calorie_estimate: CalorieResponse
    reasons: list[AgentFoodReason]
    assumptions: list[str]
    safety_note: str
    source: Literal["llm", "deterministic"]
    message: str | None = None
