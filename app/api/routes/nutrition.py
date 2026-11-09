"""BMI and calorie calculation endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from app.data.food_repository import FoodDataError
from app.schemas.nutrition import (
    BmiRequest,
    BmiResponse,
    CalorieRequest,
    CalorieResponse,
    NutritionAnalysisRequest,
    NutritionTotals,
)
from app.services.bmi_service import calculate_bmi
from app.services.calorie_service import calculate_calorie_need
from app.services.nutrition_service import UnknownFoodError, analyze_nutrition

router = APIRouter(prefix="/nutrition")
logger = logging.getLogger(__name__)


@router.post("/bmi", response_model=BmiResponse)
def post_bmi(request: BmiRequest) -> BmiResponse:
    """Return BMI without assigning an age-based category or diagnosis."""
    bmi = calculate_bmi(request.height_cm, request.weight_kg)
    return BmiResponse(
        bmi=bmi,
        note=(
            "BMI is a general screening measure, not a diagnosis. This response "
            "does not interpret BMI for age, pregnancy, or individual health."
        ),
    )


@router.post("/calories", response_model=CalorieResponse)
def post_calories(request: CalorieRequest) -> CalorieResponse:
    """Return adult calorie estimates with formula assumptions included."""
    return CalorieResponse.model_validate(
        calculate_calorie_need(request.profile).__dict__
    )


@router.post("/analyze", response_model=NutritionTotals)
def post_nutrition_analysis(request: NutritionAnalysisRequest) -> NutritionTotals:
    """Sum nutrition values for selected foods and serving counts."""
    try:
        return analyze_nutrition(request.items)
    except UnknownFoodError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except FoodDataError as error:
        logger.exception("Could not load foods while analyzing nutrition.")
        raise HTTPException(
            status_code=500,
            detail="Food data could not be loaded. Check the server logs.",
        ) from error
