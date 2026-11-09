"""Schemas for nutrition and calculation API requests and responses."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.profile import ProfileRequest


class BmiRequest(BaseModel):
    """Inputs for a BMI calculation; BMI is not interpreted here."""

    model_config = ConfigDict(extra="forbid")

    height_cm: float = Field(gt=0, description="Height in centimeters")
    weight_kg: float = Field(gt=0, description="Weight in kilograms")


class CalorieRequest(BaseModel):
    """Adult profile input for an estimated-calorie calculation."""

    model_config = ConfigDict(extra="forbid")

    profile: ProfileRequest

    @model_validator(mode="after")
    def require_adult_profile(self) -> "CalorieRequest":
        """Do not apply adult calorie equations to children or adolescents."""
        if self.profile.age < 18:
            raise ValueError(
                "Calorie estimates in this version are for adults age 18 and older."
            )
        return self


class BmiResponse(BaseModel):
    """BMI value with a general-education limitation notice."""

    bmi: float = Field(gt=0)
    note: str


class CalorieResponse(BaseModel):
    """Estimated resting, maintenance, and goal-adjusted calorie ranges."""

    resting_calories_min_kcal: int = Field(gt=0)
    resting_calories_max_kcal: int = Field(gt=0)
    maintenance_calories_min_kcal: int = Field(gt=0)
    maintenance_calories_max_kcal: int = Field(gt=0)
    goal_target_calories_min_kcal: int = Field(gt=0)
    goal_target_calories_max_kcal: int = Field(gt=0)
    activity_multiplier: float = Field(gt=0)
    goal_adjustment_kcal: int
    formula: str
    assumptions: list[str]


class FoodServing(BaseModel):
    """A selected food and the number of servings to analyze."""

    model_config = ConfigDict(extra="forbid")

    food_id: str = Field(min_length=1)
    servings: float = Field(gt=0)

    @field_validator("food_id")
    @classmethod
    def clean_food_id(cls, food_id: str) -> str:
        """Reject whitespace-only food identifiers."""
        cleaned = food_id.strip()
        if not cleaned:
            raise ValueError("Food ID must not be empty.")
        return cleaned


class NutritionAnalysisRequest(BaseModel):
    """Selected servings to include in a future nutrition analysis."""

    model_config = ConfigDict(extra="forbid")

    items: list[FoodServing] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_food_ids(self) -> "NutritionAnalysisRequest":
        """Require one entry per food so servings stay easy to interpret."""
        food_ids = [item.food_id for item in self.items]
        if len(food_ids) != len(set(food_ids)):
            raise ValueError(
                "Each food ID must appear once; combine its servings in one item."
            )
        return self


class NutritionTotals(BaseModel):
    """Nutrition totals returned by a future analysis endpoint."""

    calories_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbohydrates_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    fibre_g: float = Field(ge=0)
