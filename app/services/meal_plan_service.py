"""Deterministic meal planning with hard preference and exclusion filters."""

from collections.abc import Sequence

from app.data.food_repository import load_foods
from app.schemas.food import FoodItem
from app.schemas.meals import (
    MealPlanItem,
    MealPlanRequest,
    MealPlanResponse,
    MealPlanSlot,
)
from app.schemas.nutrition import FoodServing, NutritionTotals
from app.schemas.profile import ProfileRequest
from app.services.calorie_service import calculate_calorie_need
from app.services.nutrition_service import analyze_nutrition

MEAL_SLOTS = ("breakfast", "lunch", "dinner", "snack")
MEAL_CALORIE_SHARES = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.30,
    "snack": 0.10,
}


class NoMealCandidatesError(ValueError):
    """Raised when constraints leave one or more requested meal slots empty."""

    def __init__(self, missing_slots: list[str]) -> None:
        self.missing_slots = missing_slots
        slots = ", ".join(missing_slots)
        super().__init__(f"No eligible foods are available for: {slots}.")


def _food_matches_preferences(food: FoodItem, preferences: set[str]) -> bool:
    """Require a dataset tag for every selected dietary preference."""
    return preferences.issubset(set(food.tags))


def _food_is_excluded(food: FoodItem, exclusions: set[str]) -> bool:
    """Match exclusions against food IDs, names, tags, and allergen labels."""
    searchable_values = (
        food.id.casefold(),
        food.name.casefold(),
        *food.tags,
        *food.allergens,
    )
    return any(
        exclusion in searchable_value or searchable_value in exclusion
        for exclusion in exclusions
        for searchable_value in searchable_values
    )


def _eligible_foods(
    foods: Sequence[FoodItem],
    profile: ProfileRequest,
) -> list[FoodItem]:
    preferences = {preference.casefold() for preference in profile.food_preferences}
    exclusions = {exclusion.casefold() for exclusion in profile.excluded_foods}

    return [
        food
        for food in foods
        if _food_matches_preferences(food, preferences)
        and not _food_is_excluded(food, exclusions)
    ]


def _meal_target(daily_target: float, slot: str) -> float:
    return daily_target * MEAL_CALORIE_SHARES[slot]


def _select_food(
    candidates: list[FoodItem],
    slot: str,
    daily_target: float,
    prior_ids: set[str],
) -> FoodItem:
    """Choose one deterministic food close to one serving, preferring variety."""
    target_calories = _meal_target(daily_target, slot)

    def score(food: FoodItem) -> tuple[float, int, str]:
        servings = _serving_count(food, target_calories)
        variety_penalty = int(food.id in prior_ids)
        return (
            abs(servings - 1),
            variety_penalty,
            food.id,
        )

    return min(candidates, key=score)


def _serving_count(food: FoodItem, target_calories: float) -> float:
    if food.calories_kcal == 0:
        return 1.0
    return max(0.1, round(target_calories / food.calories_kcal, 2))


def _build_slot(
    food: FoodItem,
    slot: str,
    daily_target: float,
) -> MealPlanSlot:
    servings = _serving_count(food, _meal_target(daily_target, slot))
    nutrition = analyze_nutrition(
        [FoodServing(food_id=food.id, servings=servings)],
        foods=[food],
    )
    return MealPlanSlot(
        meal=slot,
        items=[
            MealPlanItem(
                food_id=food.id,
                name=food.name,
                servings=servings,
                serving_g=food.serving_g,
            )
        ],
        nutrition=nutrition,
    )


def _sum_totals(meals: Sequence[MealPlanSlot]) -> NutritionTotals:
    return NutritionTotals.model_validate(
        {
            "calories_kcal": round(
                sum(meal.nutrition.calories_kcal for meal in meals), 2
            ),
            "protein_g": round(sum(meal.nutrition.protein_g for meal in meals), 2),
            "carbohydrates_g": round(
                sum(meal.nutrition.carbohydrates_g for meal in meals), 2
            ),
            "fat_g": round(sum(meal.nutrition.fat_g for meal in meals), 2),
            "fibre_g": round(sum(meal.nutrition.fibre_g for meal in meals), 2),
        }
    )


def generate_meal_plan(
    request: MealPlanRequest,
    foods: Sequence[FoodItem] | None = None,
) -> MealPlanResponse:
    """Generate four deterministic meal slots from permitted dataset foods.

    User exclusions and all selected food-preference tags are applied before
    meal-slot selection. No plan is returned if any of the four slots has no
    eligible candidate.
    """
    catalog = list(foods) if foods is not None else load_foods()
    profile = request.profile
    eligible_foods = _eligible_foods(catalog, profile)

    candidates_by_slot = {
        slot: [
            food
            for food in eligible_foods
            if slot in food.tags or food.category.casefold() == slot
        ]
        for slot in MEAL_SLOTS
    }
    missing_slots = [
        slot for slot, candidates in candidates_by_slot.items() if not candidates
    ]
    if missing_slots:
        raise NoMealCandidatesError(missing_slots)

    if request.daily_calorie_target is not None:
        daily_target = request.daily_calorie_target
    else:
        estimate = calculate_calorie_need(profile)
        daily_target = round(
            (
                estimate.goal_target_calories_min_kcal
                + estimate.goal_target_calories_max_kcal
            )
            / 2
        )

    selected_ids: set[str] = set()
    meals: list[MealPlanSlot] = []
    for slot in MEAL_SLOTS:
        selected_food = _select_food(
            candidates_by_slot[slot],
            slot,
            daily_target,
            selected_ids,
        )
        selected_ids.add(selected_food.id)
        meals.append(_build_slot(selected_food, slot, daily_target))

    return MealPlanResponse(
        meals=meals,
        daily_nutrition=_sum_totals(meals),
        daily_calorie_target_kcal=daily_target,
        goal=profile.health_goal.value,
        notice=(
            "This is an illustrative plan built from the available food dataset "
            "and calorie assumptions. It is not medical advice or a prescribed "
            "diet. Dataset coverage is limited; verify ingredients and allergens."
        ),
    )
