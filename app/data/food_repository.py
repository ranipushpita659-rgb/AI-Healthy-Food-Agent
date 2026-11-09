"""Load and filter validated foods from the version-controlled JSON dataset."""

import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas.food import FoodItem

FOODS_FILE = Path(__file__).with_name("foods.json")


class FoodDataError(RuntimeError):
    """Raised when the food dataset is missing, malformed, or invalid."""


def load_foods(path: Path | None = None) -> list[FoodItem]:
    """Load and validate every food record from the JSON dataset."""
    data_path = path or FOODS_FILE

    try:
        with data_path.open(encoding="utf-8") as food_file:
            raw_foods = json.load(food_file)
    except FileNotFoundError as error:
        raise FoodDataError(f"Food data file was not found: {data_path}") from error
    except json.JSONDecodeError as error:
        raise FoodDataError(
            f"Food data file contains invalid JSON at line {error.lineno}."
        ) from error
    except OSError as error:
        raise FoodDataError(f"Food data file could not be read: {data_path}") from error

    if not isinstance(raw_foods, list):
        raise FoodDataError("Food data must be a JSON list of food records.")
    if not raw_foods:
        raise FoodDataError("Food data must contain at least one food record.")

    try:
        foods = [FoodItem.model_validate(record) for record in raw_foods]
    except ValidationError as error:
        raise FoodDataError(f"Food data record validation failed: {error}") from error

    ids = [food.id for food in foods]
    if len(ids) != len(set(ids)):
        raise FoodDataError("Food data contains duplicate food IDs.")

    return foods


def list_foods(
    category: str | None = None,
    tag: str | None = None,
    path: Path | None = None,
) -> list[FoodItem]:
    """Return all foods or filter by an exact category or tag."""
    foods = load_foods(path)
    normalized_category = category.strip().casefold() if category else None
    normalized_tag = tag.strip().casefold() if tag else None

    if normalized_category == "":
        raise ValueError("Category filter must not be empty.")
    if normalized_tag == "":
        raise ValueError("Tag filter must not be empty.")

    return [
        food
        for food in foods
        if (normalized_category is None or food.category.casefold() == normalized_category)
        and (normalized_tag is None or normalized_tag in food.tags)
    ]
