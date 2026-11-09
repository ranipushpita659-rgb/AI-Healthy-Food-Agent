"""Adult estimated energy calculations using documented assumptions."""

import math
from dataclasses import dataclass

from app.schemas.profile import ActivityLevel, Gender, HealthGoal, ProfileRequest

ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

GOAL_ADJUSTMENTS_KCAL: dict[HealthGoal, int] = {
    HealthGoal.LOSE_WEIGHT: -300,
    HealthGoal.MAINTAIN_WEIGHT: 0,
    HealthGoal.GAIN_WEIGHT: 300,
}

FORMULA_DESCRIPTION = (
    "Mifflin-St Jeor: male RMR = 10*weight_kg + 6.25*height_cm - "
    "5*age_years + 5; female RMR = 10*weight_kg + 6.25*height_cm - "
    "5*age_years - 161. Estimated maintenance calories = RMR * activity factor."
)


@dataclass(frozen=True)
class CalorieEstimate:
    """Calculated ranges and assumptions for one validated adult profile."""

    resting_calories_min_kcal: int
    resting_calories_max_kcal: int
    maintenance_calories_min_kcal: int
    maintenance_calories_max_kcal: int
    goal_target_calories_min_kcal: int
    goal_target_calories_max_kcal: int
    activity_multiplier: float
    goal_adjustment_kcal: int
    formula: str
    assumptions: list[str]


def _round_calories(value: float) -> int:
    """Round positive calorie estimates to the nearest whole calorie."""
    return math.floor(value + 0.5)


def calculate_calorie_need(profile: ProfileRequest) -> CalorieEstimate:
    """Estimate adult resting and daily calories from a validated profile.

    The Mifflin-St Jeor equations use sex-specific constants. For profiles
    recorded as female or male, the corresponding equation is used as a broad
    model assumption. For other or undisclosed gender values, both equations
    are evaluated and returned as a range rather than silently selecting one.

    Activity multipliers and the +/-300 kcal goal adjustment are transparent
    educational assumptions, not an individualized medical prescription.
    These estimates are not intended for people under 18, pregnant, or
    breastfeeding.
    """
    if profile.age < 18:
        raise ValueError(
            "Calorie estimates in this version are for adults age 18 and older."
        )

    measurements = (profile.height_cm, profile.weight_kg)
    if not all(math.isfinite(value) and value > 0 for value in measurements):
        raise ValueError("Height and weight must be finite values greater than zero.")

    resting_by_equation = {
        Gender.FEMALE: (
            10 * profile.weight_kg
            + 6.25 * profile.height_cm
            - 5 * profile.age
            - 161
        ),
        Gender.MALE: (
            10 * profile.weight_kg
            + 6.25 * profile.height_cm
            - 5 * profile.age
            + 5
        ),
    }

    if profile.gender == Gender.FEMALE:
        resting_values = [resting_by_equation[Gender.FEMALE]]
    elif profile.gender == Gender.MALE:
        resting_values = [resting_by_equation[Gender.MALE]]
    else:
        resting_values = list(resting_by_equation.values())

    activity_multiplier = ACTIVITY_MULTIPLIERS[profile.activity_level]
    goal_adjustment = GOAL_ADJUSTMENTS_KCAL[profile.health_goal]
    resting_min = min(resting_values)
    resting_max = max(resting_values)
    maintenance_min = resting_min * activity_multiplier
    maintenance_max = resting_max * activity_multiplier
    goal_min = maintenance_min + goal_adjustment
    goal_max = maintenance_max + goal_adjustment

    if goal_min <= 0:
        raise ValueError(
            "The selected profile produces an invalid calorie estimate. "
            "Check the profile details."
        )

    assumptions = [
        "Adult-only estimate; not intended for people under 18, pregnant, or breastfeeding.",
        "The equation uses weight in kg, height in cm, and age in years.",
        "Female/male profile values select the corresponding equation constant; "
        "other or undisclosed values return the range from both constants.",
        "Activity factors are approximate: sedentary 1.2, light 1.375, "
        "moderate 1.55, active 1.725, very active 1.9.",
        "Goal targets apply an illustrative -300 kcal/day for weight loss, "
        "0 for maintenance, or +300 kcal/day for weight gain.",
        "Results are estimates for general education, not medical advice or a prescription.",
    ]

    return CalorieEstimate(
        resting_calories_min_kcal=_round_calories(resting_min),
        resting_calories_max_kcal=_round_calories(resting_max),
        maintenance_calories_min_kcal=_round_calories(maintenance_min),
        maintenance_calories_max_kcal=_round_calories(maintenance_max),
        goal_target_calories_min_kcal=_round_calories(goal_min),
        goal_target_calories_max_kcal=_round_calories(goal_max),
        activity_multiplier=activity_multiplier,
        goal_adjustment_kcal=goal_adjustment,
        formula=FORMULA_DESCRIPTION,
        assumptions=assumptions,
    )
