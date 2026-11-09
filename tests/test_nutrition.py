"""Tests for deterministic nutrition totals."""

import pytest

from app.schemas.nutrition import FoodServing
from app.services.nutrition_service import UnknownFoodError, analyze_nutrition


def test_analyze_nutrition_sums_servings() -> None:
    totals = analyze_nutrition(
        [
            FoodServing(food_id="banana_raw", servings=1),
            FoodServing(food_id="apple_raw_skin", servings=2),
        ]
    )

    assert totals.calories_kcal == 193
    assert totals.protein_g == 1.61
    assert totals.carbohydrates_g == 50.46
    assert totals.fat_g == 0.67
    assert totals.fibre_g == 7.4


def test_analyze_nutrition_rejects_unknown_food_id() -> None:
    with pytest.raises(UnknownFoodError, match="Unknown food ID"):
        analyze_nutrition([FoodServing(food_id="not-in-dataset", servings=1)])
