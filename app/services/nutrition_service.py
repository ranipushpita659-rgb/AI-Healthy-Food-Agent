"""Deterministic nutrition totals based on the validated food dataset."""

from collections.abc import Sequence

from app.data.food_repository import load_foods
from app.schemas.food import FoodItem
from app.schemas.nutrition import FoodServing, NutritionTotals


class UnknownFoodError(LookupError):
    """Raised when an analysis requests a food ID absent from the dataset."""


def analyze_nutrition(
    items: Sequence[FoodServing],
    foods: Sequence[FoodItem] | None = None,
) -> NutritionTotals:
    """Sum nutrient values for food servings from the structured dataset.

    Each food record gives nutrients for one stated serving. The requested
    `servings` value scales that record; it is not a gram measurement.
    """
    if not items:
        raise ValueError("At least one food serving is required.")

    catalog = list(foods) if foods is not None else load_foods()
    foods_by_id = {food.id: food for food in catalog}
    totals = {
        "calories_kcal": 0.0,
        "protein_g": 0.0,
        "carbohydrates_g": 0.0,
        "fat_g": 0.0,
        "fibre_g": 0.0,
    }

    for item in items:
        food = foods_by_id.get(item.food_id)
        if food is None:
            raise UnknownFoodError(f"Unknown food ID: {item.food_id}")
        totals["calories_kcal"] += food.calories_kcal * item.servings
        totals["protein_g"] += food.protein_g * item.servings
        totals["carbohydrates_g"] += food.carbs_g * item.servings
        totals["fat_g"] += food.fat_g * item.servings
        totals["fibre_g"] += food.fibre_g * item.servings

    return NutritionTotals.model_validate(
        {name: round(value, 2) for name, value in totals.items()}
    )
