"""Repository functions for persisted profiles, plans, and weight records."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MealPlanRecord, ProfileRecord, WeightRecord
from app.schemas.meals import MealPlanResponse
from app.schemas.profile import ProfileRequest


class ProfileNotFoundError(LookupError):
    """Raised when an operation references an unknown saved profile."""


def _new_profile_record(profile: ProfileRequest) -> ProfileRecord:
    return ProfileRecord(
        id=str(uuid4()),
        age=profile.age,
        gender=profile.gender.value,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level.value,
        health_goal=profile.health_goal.value,
        food_preferences=list(profile.food_preferences),
        excluded_foods=list(profile.excluded_foods),
    )


def save_profile(session: Session, profile: ProfileRequest) -> ProfileRecord:
    """Persist one validated profile."""
    record = _new_profile_record(profile)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def save_profile_and_meal_plan(
    session: Session,
    profile: ProfileRequest,
    plan: MealPlanResponse,
) -> tuple[ProfileRecord, MealPlanRecord]:
    """Atomically persist a profile and its generated meal-plan snapshot."""
    profile_record = _new_profile_record(profile)
    meal_plan_id = str(uuid4())
    plan_with_ids = plan.model_copy(
        update={
            "profile_id": profile_record.id,
            "meal_plan_id": meal_plan_id,
        }
    )
    meal_plan_record = MealPlanRecord(
        id=meal_plan_id,
        profile_id=profile_record.id,
        daily_calorie_target_kcal=plan.daily_calorie_target_kcal,
        plan_json=plan_with_ids.model_dump(mode="json"),
    )
    session.add_all([profile_record, meal_plan_record])
    session.commit()
    session.refresh(profile_record)
    session.refresh(meal_plan_record)
    return profile_record, meal_plan_record


def get_profile(session: Session, profile_id: str) -> ProfileRecord:
    """Return a saved profile or raise a typed not-found error."""
    record = session.get(ProfileRecord, profile_id)
    if record is None:
        raise ProfileNotFoundError(f"Profile not found: {profile_id}")
    return record


def list_meal_plans(
    session: Session,
    profile_id: str,
) -> list[MealPlanRecord]:
    """Return a profile's meal plans from newest to oldest."""
    get_profile(session, profile_id)
    statement = (
        select(MealPlanRecord)
        .where(MealPlanRecord.profile_id == profile_id)
        .order_by(MealPlanRecord.created_at.desc())
    )
    return list(session.scalars(statement))


def add_weight_record(
    session: Session,
    profile_id: str,
    weight_kg: float,
    measured_at: datetime | None = None,
) -> WeightRecord:
    """Save an optional weight measurement for an existing profile."""
    get_profile(session, profile_id)
    record = WeightRecord(
        id=str(uuid4()),
        profile_id=profile_id,
        weight_kg=weight_kg,
    )
    if measured_at is not None:
        record.measured_at = measured_at
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_weight_records(session: Session, profile_id: str) -> list[WeightRecord]:
    """Return a profile's weight records in measurement order."""
    get_profile(session, profile_id)
    statement = (
        select(WeightRecord)
        .where(WeightRecord.profile_id == profile_id)
        .order_by(WeightRecord.measured_at.asc())
    )
    return list(session.scalars(statement))
