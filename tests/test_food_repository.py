"""Tests for loading and filtering the structured food dataset."""

import json
from pathlib import Path

import pytest

from app.data.food_repository import FoodDataError, list_foods, load_foods


def test_loads_valid_food_records() -> None:
    foods = load_foods()

    assert len(foods) == 4
    assert foods[0].id == "banana_raw"
    assert foods[3].allergens == ["egg"]


def test_filters_foods_by_category_and_tag() -> None:
    foods = list_foods(category="FRUIT", tag="Vegan")

    assert {food.id for food in foods} == {"banana_raw", "apple_raw_skin"}


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
