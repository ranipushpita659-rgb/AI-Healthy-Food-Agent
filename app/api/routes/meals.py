"""Meal plan generation endpoint."""

import logging

from fastapi import APIRouter, HTTPException

from app.data.food_repository import FoodDataError
from app.schemas.meals import MealPlanRequest, MealPlanResponse
from app.services.meal_plan_service import (
    NoMealCandidatesError,
    generate_meal_plan,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/meals/generate", response_model=MealPlanResponse)
def post_generate_meal_plan(request: MealPlanRequest) -> MealPlanResponse:
    """Generate a deterministic plan using only eligible structured foods."""
    try:
        return generate_meal_plan(request)
    except NoMealCandidatesError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(error),
                "missing_meals": error.missing_slots,
            },
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FoodDataError as error:
        logger.exception("Could not load foods while generating a meal plan.")
        raise HTTPException(
            status_code=500,
            detail="Food data could not be loaded. Check the server logs.",
        ) from error
