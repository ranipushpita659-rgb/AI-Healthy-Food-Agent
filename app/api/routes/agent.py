"""Grounded AI meal recommendation endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.data.database_repository import save_profile_and_meal_plan
from app.data.food_repository import FoodDataError
from app.db.session import get_session
from app.schemas.agent import (
    AgentRecommendationRequest,
    AgentRecommendationResponse,
)
from app.services.agent_service import recommend_meals
from app.services.meal_plan_service import NoMealCandidatesError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agent/recommend", response_model=AgentRecommendationResponse)
def post_recommendation(
    request: AgentRecommendationRequest,
    session: Session = Depends(get_session),
) -> AgentRecommendationResponse:
    """Return a deterministic plan with an optional constrained LLM explanation."""
    try:
        recommendation = recommend_meals(request)
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
        logger.exception("Could not load foods while preparing an agent recommendation.")
        raise HTTPException(
            status_code=500,
            detail="Food data could not be loaded. Check the server logs.",
        ) from error

    try:
        _, saved_plan = save_profile_and_meal_plan(
            session,
            request.profile,
            recommendation.meal_plan,
        )
    except SQLAlchemyError as error:
        session.rollback()
        logger.exception("Could not persist an agent recommendation.")
        raise HTTPException(
            status_code=500,
            detail="Recommendation could not be saved. Check the server logs.",
        ) from error

    return recommendation.model_copy(
        update={
            "meal_plan": recommendation.meal_plan.model_copy(
                update={
                    "profile_id": saved_plan.profile_id,
                    "meal_plan_id": saved_plan.id,
                }
            )
        }
    )
