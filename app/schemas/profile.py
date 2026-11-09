"""Schemas for user profile input and validation."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Gender(StrEnum):
    """Gender values collected by the profile form."""

    FEMALE = "female"
    MALE = "male"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ActivityLevel(StrEnum):
    """Supported descriptions of a user's usual activity level."""

    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class HealthGoal(StrEnum):
    """Weight-management goals available in the profile form."""

    LOSE_WEIGHT = "lose_weight"
    MAINTAIN_WEIGHT = "maintain_weight"
    GAIN_WEIGHT = "gain_weight"


class ProfileRequest(BaseModel):
    """Validated profile details; these fields do not diagnose health conditions."""

    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=1, le=120, description="Age in years")
    gender: Gender
    height_cm: float = Field(gt=0, description="Height in centimeters")
    weight_kg: float = Field(gt=0, description="Current weight in kilograms")
    activity_level: ActivityLevel
    health_goal: HealthGoal
    food_preferences: list[str] = Field(default_factory=list)
    excluded_foods: list[str] = Field(default_factory=list)

    @field_validator("food_preferences", "excluded_foods")
    @classmethod
    def clean_food_names(cls, foods: list[str]) -> list[str]:
        """Trim food labels and reject blank entries."""
        cleaned = [food.strip() for food in foods]
        if any(not food for food in cleaned):
            raise ValueError("Food names must not be empty.")
        return cleaned


class ProfileValidationResponse(BaseModel):
    """Response from validating a profile without saving it."""

    valid: bool
    message: str
