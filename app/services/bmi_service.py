"""Deterministic BMI calculation."""

import math


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate BMI as kg/m^2 and round the result to one decimal place.

    BMI = weight in kilograms / (height in meters squared). This function
    returns the numeric value only; it does not interpret BMI for age or health.
    """
    if not math.isfinite(height_cm) or height_cm <= 0:
        raise ValueError("Height must be a finite number greater than zero.")
    if not math.isfinite(weight_kg) or weight_kg <= 0:
        raise ValueError("Weight must be a finite number greater than zero.")

    height_m = height_cm / 100
    return round(weight_kg / (height_m**2), 1)
