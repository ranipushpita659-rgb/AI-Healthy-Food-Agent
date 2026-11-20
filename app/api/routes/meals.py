"""Meal plan generation endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.data.food_repository import FoodDataError
from app.data.database_repository import save_profile_and_meal_plan
from app.db.session import get_session
from app.schemas.meals import MealPlanRequest, MealPlanResponse
from app.services.meal_plan_service import (
    NoMealCandidatesError,
    generate_meal_plan,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/meals/generate", response_model=MealPlanResponse)
def post_generate_meal_plan(
    request: MealPlanRequest,
    session: Session = Depends(get_session),
) -> MealPlanResponse:
    """Generate a deterministic plan using only eligible structured foods."""
    try:
        plan = generate_meal_plan(request)
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

    try:
        _, saved_plan = save_profile_and_meal_plan(session, request.profile, plan)
    except SQLAlchemyError as error:
        session.rollback()
        logger.exception("Could not persist a generated meal plan.")
        raise HTTPException(
            status_code=500,
            detail="Meal plan could not be saved. Check the server logs.",
        ) from error
    return plan.model_copy(
        update={
            "profile_id": saved_plan.profile_id,
            "meal_plan_id": saved_plan.id,
        }
    )
