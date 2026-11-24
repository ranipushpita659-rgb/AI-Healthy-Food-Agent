"""Deterministic meal planning with hard preference and exclusion filters."""

import re
from collections.abc import Sequence

from app.data.food_repository import load_foods
from app.schemas.food import FoodItem
from app.schemas.meals import (
    AvailableFood,
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
MEAL_COMPONENTS = {
    "breakfast": (
        ("grain", 0.40),
        ("protein", 0.30),
        ("fruit", 0.20),
        ("dairy", 0.10),
        ("nuts", 0.10),
    ),
    "lunch": (
        ("grain", 0.52),
        ("protein", 0.25),
        ("legume", 0.13),
        ("vegetable", 0.10),
    ),
    "dinner": (
        ("grain", 0.52),
        ("protein", 0.25),
        ("legume", 0.13),
        ("vegetable", 0.10),
    ),
    "snack": (
        ("fruit", 0.80),
        ("dairy", 0.30),
        ("nuts", 0.20),
        ("grain", 0.20),
    ),
}
MAX_COMPONENTS = {"breakfast": 3, "lunch": 4, "dinner": 4, "snack": 2}
MAX_SERVINGS_BY_CATEGORY = {
    "grain": 3.5,
    "protein": 1.2,
    "legume": 1.5,
    "vegetable": 2.5,
    "fruit": 2.0,
    "dairy": 1.5,
    "nuts": 0.3,
}
AVAILABLE_FOOD_TERMS = {
    AvailableFood.RICE: {"rice"},
    AvailableFood.BREAD: {"bread"},
    AvailableFood.OATS: {"oat", "oats"},
    AvailableFood.EGG: {"egg", "eggs"},
    AvailableFood.CHICKEN: {"chicken"},
    AvailableFood.FISH: {"fish"},
    AvailableFood.POTATO: {"potato", "potatoes"},
    AvailableFood.TOMATO: {"tomato", "tomatoes"},
    AvailableFood.CARROT: {"carrot", "carrots"},
    AvailableFood.SPINACH: {"spinach"},
    AvailableFood.MILK: {"milk"},
    AvailableFood.YOGURT: {"yogurt", "yoghurt"},
    AvailableFood.BANANA: {"banana", "bananas"},
    AvailableFood.APPLE: {"apple", "apples"},
    AvailableFood.ORANGE: {"orange", "oranges"},
    AvailableFood.LENTILS: {"lentil", "lentils"},
    AvailableFood.BEANS: {"bean", "beans"},
    AvailableFood.NUTS: {
        "almond",
        "cashew",
        "hazelnut",
        "nut",
        "nuts",
        "peanut",
        "pecan",
        "pistachio",
        "walnut",
    },
}


class NoMealCandidatesError(ValueError):
    """Raised when constraints leave one or more requested meal slots empty."""

    def __init__(self, missing_slots: list[str]) -> None:
        self.missing_slots = missing_slots
        slots = ", ".join(missing_slots)
        super().__init__(f"No eligible foods are available for: {slots}.")


def _food_matches_preferences(food: FoodItem, preferences: set[str]) -> bool:
    """Require a supported dataset classification for each preference."""
    tagged_preferences = preferences - {"halal"}
    if not tagged_preferences.issubset(set(food.tags)):
        return False
    return "halal" not in preferences or food.halal_status in {
        "ingredient_permissible",
        "verified",
    }


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


def _food_matches_availability(
    food: FoodItem,
    available_foods: set[AvailableFood],
    available_food_ids: set[str] | None = None,
) -> bool:
    if not available_foods and not available_food_ids:
        return True
    if available_food_ids and food.id in available_food_ids:
        return True

    name_words = set(re.findall(r"[a-z0-9]+", food.name.casefold()))
    return any(
        name_words.intersection(AVAILABLE_FOOD_TERMS[item])
        for item in available_foods
    )


def _eligible_foods(
    foods: Sequence[FoodItem],
    profile: ProfileRequest,
    available_foods: set[AvailableFood],
    available_food_ids: set[str],
) -> list[FoodItem]:
    preferences = {preference.casefold() for preference in profile.food_preferences}
    exclusions = {exclusion.casefold() for exclusion in profile.excluded_foods}

    return [
        food
        for food in foods
        if _food_matches_preferences(food, preferences)
        and _food_matches_availability(food, available_foods, available_food_ids)
        and not _food_is_excluded(food, exclusions)
    ]


def _meal_target(daily_target: float, slot: str) -> float:
    return daily_target * MEAL_CALORIE_SHARES[slot]


def _select_food(
    candidates: list[FoodItem],
    category: str,
    prior_ids: set[str],
) -> FoodItem:
    """Choose a varied, locally familiar food for a meal component."""
    category_candidates = [
        food for food in candidates if food.category.casefold() == category
    ]
    return min(
        category_candidates,
        key=lambda food: (
            int("bangladesh" not in food.tags),
            int(food.id in prior_ids),
            food.id,
        ),
    )


def _serving_count(food: FoodItem, target_calories: float) -> float:
    if food.calories_kcal == 0:
        return 1.0
    return max(0.1, round(target_calories / food.calories_kcal, 2))


def _build_slot(
    foods: Sequence[FoodItem],
    slot: str,
    daily_target: float,
) -> MealPlanSlot:
    items: list[MealPlanItem] = []
    for food in foods:
        component_weight = next(
            weight
            for category, weight in MEAL_COMPONENTS[slot]
            if category == food.category.casefold()
        )
        serving_target = _meal_target(daily_target, slot) * component_weight
        servings = min(
            _serving_count(food, serving_target),
            MAX_SERVINGS_BY_CATEGORY.get(food.category.casefold(), 1.5),
        )
        items.append(
            MealPlanItem(
                food_id=food.id,
                name=food.name,
                servings=servings,
                serving_g=food.serving_g,
            )
        )
    nutrition = analyze_nutrition(
        [FoodServing(food_id=item.food_id, servings=item.servings) for item in items],
        foods=list(foods),
    )
    return MealPlanSlot(
        meal=slot,
        items=items,
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

    User availability, preference, and exclusion filters are applied before
    meal-slot selection. An empty availability selection keeps the full
    catalog eligible. No plan is returned if any slot has no eligible food.
    """
    catalog = list(foods) if foods is not None else load_foods()
    profile = request.profile
    available_food_ids = set(request.available_food_ids)
    catalog_ids = {food.id for food in catalog}
    unknown_food_ids = available_food_ids - catalog_ids
    if unknown_food_ids:
        raise ValueError(
            "Selected foods are not in the food catalog: "
            + ", ".join(sorted(unknown_food_ids))
        )
    eligible_foods = _eligible_foods(
        catalog,
        profile,
        set(request.available_foods),
        available_food_ids,
    )

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
        chosen_foods: list[FoodItem] = []
        for category, _ in MEAL_COMPONENTS[slot]:
            category_candidates = [
                food
                for food in candidates_by_slot[slot]
                if food.category.casefold() == category
            ]
            if not category_candidates:
                continue
            chosen_food = _select_food(
                category_candidates,
                category,
                selected_ids,
            )
            chosen_foods.append(chosen_food)
            selected_ids.add(chosen_food.id)
            if len(chosen_foods) == MAX_COMPONENTS[slot]:
                break
        meals.append(_build_slot(chosen_foods, slot, daily_target))

    return MealPlanResponse(
        meals=meals,
        daily_nutrition=_sum_totals(meals),
        daily_calorie_target_kcal=daily_target,
        goal=profile.health_goal.value,
        notice=(
            "This estimated plan uses the selected foods and serving assumptions. "
            "It is not a prescribed diet. Verify ingredients and allergens."
        ),
    )
