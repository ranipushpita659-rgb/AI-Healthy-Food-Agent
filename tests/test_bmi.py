"""Tests for BMI calculations."""

import math

import pytest

from app.services.bmi_service import calculate_bmi


def test_calculate_bmi_for_known_measurements() -> None:
    assert calculate_bmi(height_cm=175, weight_kg=70) == 22.9


@pytest.mark.parametrize(
    ("height_cm", "weight_kg"),
    [(0, 70), (-1, 70), (175, 0), (175, -1), (math.nan, 70), (175, math.inf)],
)
def test_calculate_bmi_rejects_invalid_measurements(
    height_cm: float,
    weight_kg: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_bmi(height_cm=height_cm, weight_kg=weight_kg)
