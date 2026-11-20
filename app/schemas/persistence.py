"""API schemas for persisted profiles and optional progress records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.meals import MealPlanResponse


class SavedProfileResponse(BaseModel):
    """Opaque identifier and timestamp returned after saving a profile."""

    profile_id: str
    created_at: datetime


class WeightRecordRequest(BaseModel):
    """Optional weight measurement associated with a saved profile."""

    model_config = ConfigDict(extra="forbid")

    weight_kg: float = Field(gt=0)
    measured_at: datetime | None = None


class WeightRecordResponse(BaseModel):
    """Saved measurement without exposing unrelated profile fields."""

    record_id: str
    profile_id: str
    weight_kg: float
    measured_at: datetime


class SavedMealPlanResponse(BaseModel):
    """Persisted meal plan and its creation time."""

    meal_plan_id: str
    profile_id: str
    created_at: datetime
    plan: MealPlanResponse
