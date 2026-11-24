"""Schemas for meal-plan API requests and responses."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.nutrition import NutritionTotals
from app.schemas.profile import ProfileRequest


class AvailableFood(StrEnum):
    """Available food groups selectable for a meal plan."""

    RICE = "rice"
    BREAD = "bread"
    OATS = "oats"
    EGG = "egg"
    CHICKEN = "chicken"
    FISH = "fish"
    POTATO = "potato"
    TOMATO = "tomato"
    CARROT = "carrot"
    SPINACH = "spinach"
    MILK = "milk"
    YOGURT = "yogurt"
    BANANA = "banana"
    APPLE = "apple"
    ORANGE = "orange"
    LENTILS = "lentils"
    BEANS = "beans"
    NUTS = "nuts"


class MealPlanRequest(BaseModel):
    """Profile and food constraints for a meal-plan request."""

    model_config = ConfigDict(extra="forbid")

    profile: ProfileRequest
    available_foods: list[AvailableFood] = Field(default_factory=list)
    available_food_ids: list[str] = Field(default_factory=list, max_length=100)
    daily_calorie_target: float | None = Field(default=None, ge=500, le=10000)

    @model_validator(mode="after")
    def require_adult_profile(self) -> "MealPlanRequest":
        """Avoid applying this adult-oriented meal planner to minors."""
        if self.profile.age < 18:
            raise ValueError(
                "Meal plans in this version are for adults age 18 and older."
            )
        return self


class MealPlanItem(BaseModel):
    """A food selected for one meal-plan slot."""

    food_id: str
    name: str
    servings: float = Field(gt=0)
    serving_g: float = Field(gt=0)


class MealPlanSlot(BaseModel):
    """Foods and nutrition totals for one meal slot."""

    meal: str
    items: list[MealPlanItem]
    nutrition: NutritionTotals


class MealPlanResponse(BaseModel):
    """Structured meal plan and target with a clear general-education notice."""

    meals: list[MealPlanSlot]
    daily_nutrition: NutritionTotals
    daily_calorie_target_kcal: float = Field(gt=0)
    goal: str
    notice: str
    profile_id: str | None = None
    meal_plan_id: str | None = None
