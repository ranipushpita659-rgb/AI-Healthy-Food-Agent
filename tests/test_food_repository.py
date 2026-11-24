"""Tests for loading and filtering the structured food dataset."""

import json
import re
from pathlib import Path

import pytest

from app.data.food_repository import FoodDataError, list_foods, load_foods
from app.schemas.meals import AvailableFood
from app.services.meal_plan_service import AVAILABLE_FOOD_TERMS, _food_matches_availability


def test_loads_valid_food_records() -> None:
    foods = load_foods()

    assert len(foods) == 18
    assert foods[0].id == "banana_raw"
    assert next(food for food in foods if food.id == "egg_whole_boiled").allergens == [
        "egg"
    ]


def test_every_ui_food_option_has_a_verified_catalog_record() -> None:
    foods = load_foods()
    assert set(AVAILABLE_FOOD_TERMS) == set(AvailableFood)
    html = (
        Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    ).read_text(encoding="utf-8")
    ui_options = set(
        re.findall(r'name="available_foods"\s+value="([^"]+)"', html)
    )
    assert ui_options == {food.value for food in AvailableFood}

    for available_food in AvailableFood:
        assert any(
            _food_matches_availability(food, {available_food})
            for food in foods
        ), f"No catalog record matches {available_food.value}"


def test_every_catalog_food_has_complete_nutrition_and_source_data() -> None:
    for food in load_foods():
        assert food.serving_g == 100
        assert all(
            value >= 0
            for value in (
                food.calories_kcal,
                food.protein_g,
                food.carbs_g,
                food.fat_g,
                food.fibre_g,
            )
        )
        assert food.source_dataset.startswith("USDA FoodData Central")
        assert str(food.fdc_id) in str(food.source_url)


def test_filters_foods_by_category_and_tag() -> None:
    foods = list_foods(category="FRUIT", tag="Vegan")

    assert {food.id for food in foods} == {
        "banana_raw",
        "apple_raw_skin",
        "orange_raw",
    }


def test_missing_food_file_reports_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FoodDataError, match="was not found"):
        load_foods(tmp_path / "missing.json")


def test_invalid_json_reports_clear_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "foods.json"
    invalid_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(FoodDataError, match="invalid JSON"):
        load_foods(invalid_file)


def test_invalid_food_record_reports_validation_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "foods.json"
    invalid_file.write_text(json.dumps([{"id": "missing-fields"}]), encoding="utf-8")

    with pytest.raises(FoodDataError, match="validation failed"):
        load_foods(invalid_file)


def test_duplicate_food_ids_are_rejected(tmp_path: Path) -> None:
    source = load_foods()[0].model_dump(mode="json")
    duplicate_file = tmp_path / "foods.json"
    duplicate_file.write_text(json.dumps([source, source]), encoding="utf-8")

    with pytest.raises(FoodDataError, match="duplicate food IDs"):
        load_foods(duplicate_file)
