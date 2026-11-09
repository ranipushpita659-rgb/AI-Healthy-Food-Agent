"""Tests for adult calorie estimates."""

import pytest

from app.schemas.profile import ProfileRequest
from app.services.calorie_service import calculate_calorie_need


def make_profile(**overrides: object) -> ProfileRequest:
    values: dict[str, object] = {
        "age": 30,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 70,
        "activity_level": "sedentary",
        "health_goal": "maintain_weight",
    }
    values.update(overrides)
    return ProfileRequest.model_validate(values)


def test_calculate_calorie_need_for_adult_man() -> None:
    result = calculate_calorie_need(make_profile())

    assert result.resting_calories_min_kcal == 1649
    assert result.resting_calories_max_kcal == 1649
    assert result.maintenance_calories_min_kcal == 1979
    assert result.maintenance_calories_max_kcal == 1979
    assert result.goal_adjustment_kcal == 0


def test_calculate_calorie_need_applies_activity_and_goal_assumptions() -> None:
    result = calculate_calorie_need(
        make_profile(
            activity_level="moderate",
            health_goal="lose_weight",
        )
    )

    assert result.activity_multiplier == 1.55
    assert result.goal_adjustment_kcal == -300
    assert result.goal_target_calories_min_kcal == 2256


def test_unspecified_formula_group_returns_range() -> None:
    result = calculate_calorie_need(make_profile(gender="other"))

    assert result.resting_calories_min_kcal == 1483
    assert result.resting_calories_max_kcal == 1649
    assert result.maintenance_calories_min_kcal < result.maintenance_calories_max_kcal


def test_calorie_request_rejects_under_18_profile() -> None:
    from pydantic import ValidationError

    from app.schemas.nutrition import CalorieRequest

    profile = make_profile(age=17)
    with pytest.raises(ValidationError, match="adults age 18 and older"):
        CalorieRequest.model_validate({"profile": profile.model_dump()})


def test_service_rejects_under_18_profile() -> None:
    with pytest.raises(ValueError, match="adults age 18 and older"):
        calculate_calorie_need(make_profile(age=17))
