"""Tests for deterministic meal planning and hard food exclusions."""

import pytest

from app.data.food_repository import load_foods
from app.schemas.meals import MealPlanRequest
from app.services.meal_plan_service import (
    MEAL_SLOTS,
    NoMealCandidatesError,
    generate_meal_plan,
)


def make_request(**profile_overrides: object) -> MealPlanRequest:
    profile: dict[str, object] = {
        "age": 30,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 70,
        "activity_level": "sedentary",
        "health_goal": "maintain_weight",
    }
    profile.update(profile_overrides)
    return MealPlanRequest.model_validate(
        {
            "profile": profile,
            "daily_calorie_target": 2000,
        }
    )


def test_generates_four_meals_and_nutrition_totals() -> None:
    plan = generate_meal_plan(make_request())

    assert [meal.meal for meal in plan.meals] == list(MEAL_SLOTS)
    assert plan.daily_calorie_target_kcal == 2000
    assert plan.daily_nutrition.calories_kcal > 0
    assert all(meal.items for meal in plan.meals)


def test_missing_calorie_target_uses_profile_goal_estimate() -> None:
    request = MealPlanRequest.model_validate(
        {
            "profile": {
                "age": 30,
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 70,
                "activity_level": "sedentary",
                "health_goal": "lose_weight",
            }
        }
    )

    plan = generate_meal_plan(request)

    assert plan.daily_calorie_target_kcal == 1679
    assert plan.goal == "lose_weight"


def test_excluded_allergen_is_never_recommended() -> None:
    plan = generate_meal_plan(make_request(excluded_foods=["egg"]))

    recommended_ids = {
        item.food_id for meal in plan.meals for item in meal.items
    }
    assert "egg_whole_boiled" not in recommended_ids


def test_selected_preferences_are_hard_constraints() -> None:
    plan = generate_meal_plan(make_request(food_preferences=["vegan"]))

    foods_by_id = {food.id: food for food in load_foods()}
    for meal in plan.meals:
        for item in meal.items:
            assert "vegan" in foods_by_id[item.food_id].tags


def test_missing_candidates_are_reported_instead_of_returning_partial_plan() -> None:
    with pytest.raises(NoMealCandidatesError) as error:
        generate_meal_plan(make_request(food_preferences=["halal"]))

    assert error.value.missing_slots == list(MEAL_SLOTS)


def test_meal_plan_rejects_minor_profiles() -> None:
    with pytest.raises(ValueError, match="adults age 18 and older"):
        make_request(age=17)
