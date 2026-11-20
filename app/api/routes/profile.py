"""User profile validation endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.data.database_repository import (
    ProfileNotFoundError,
    add_weight_record,
    list_meal_plans,
    list_weight_records,
    save_profile,
)
from app.db.session import get_session
from app.schemas.meals import MealPlanResponse
from app.schemas.persistence import (
    SavedMealPlanResponse,
    SavedProfileResponse,
    WeightRecordRequest,
    WeightRecordResponse,
)
from app.schemas.profile import ProfileRequest, ProfileValidationResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/profile/validate", response_model=ProfileValidationResponse)
def validate_profile(_: ProfileRequest) -> ProfileValidationResponse:
    """Validate profile fields without saving them or making health claims."""
    return ProfileValidationResponse(
        valid=True,
        message="Profile details are valid.",
    )


@router.post(
    "/profiles",
    response_model=SavedProfileResponse,
    status_code=201,
)
def post_save_profile(
    profile: ProfileRequest,
    session: Session = Depends(get_session),
) -> SavedProfileResponse:
    """Save a validated profile and return its opaque identifier."""
    try:
        record = save_profile(session, profile)
    except SQLAlchemyError as error:
        session.rollback()
        logger.exception("Could not save a user profile.")
        raise HTTPException(
            status_code=500,
            detail="Profile could not be saved. Check the server logs.",
        ) from error
    return SavedProfileResponse(profile_id=record.id, created_at=record.created_at)


@router.get(
    "/profiles/{profile_id}/meal-plans",
    response_model=list[SavedMealPlanResponse],
)
def get_saved_meal_plans(
    profile_id: str,
    session: Session = Depends(get_session),
) -> list[SavedMealPlanResponse]:
    """Return meal-plan snapshots for one saved profile."""
    try:
        records = list_meal_plans(session, profile_id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SQLAlchemyError as error:
        logger.exception("Could not load saved meal plans.")
        raise HTTPException(
            status_code=500,
            detail="Meal plans could not be loaded. Check the server logs.",
        ) from error
    return [
        SavedMealPlanResponse(
            meal_plan_id=record.id,
            profile_id=record.profile_id,
            created_at=record.created_at,
            plan=MealPlanResponse.model_validate(record.plan_json),
        )
        for record in records
    ]


@router.post(
    "/profiles/{profile_id}/weight-records",
    response_model=WeightRecordResponse,
    status_code=201,
)
def post_weight_record(
    profile_id: str,
    request: WeightRecordRequest,
    session: Session = Depends(get_session),
) -> WeightRecordResponse:
    """Save an optional weight measurement for a saved profile."""
    try:
        record = add_weight_record(
            session,
            profile_id,
            request.weight_kg,
            request.measured_at,
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SQLAlchemyError as error:
        session.rollback()
        logger.exception("Could not save a weight record.")
        raise HTTPException(
            status_code=500,
            detail="Weight record could not be saved. Check the server logs.",
        ) from error
    return WeightRecordResponse(
        record_id=record.id,
        profile_id=record.profile_id,
        weight_kg=record.weight_kg,
        measured_at=record.measured_at,
    )


@router.get(
    "/profiles/{profile_id}/weight-records",
    response_model=list[WeightRecordResponse],
)
def get_weight_records(
    profile_id: str,
    session: Session = Depends(get_session),
) -> list[WeightRecordResponse]:
    """List optional weight measurements in chronological order."""
    try:
        records = list_weight_records(session, profile_id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SQLAlchemyError as error:
        logger.exception("Could not load saved weight records.")
        raise HTTPException(
            status_code=500,
            detail="Weight records could not be loaded. Check the server logs.",
        ) from error
    return [
        WeightRecordResponse(
            record_id=record.id,
            profile_id=record.profile_id,
            weight_kg=record.weight_kg,
            measured_at=record.measured_at,
        )
        for record in records
    ]
