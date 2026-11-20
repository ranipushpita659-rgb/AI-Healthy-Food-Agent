"""Tests for persisted profiles, plans, and optional weight records."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.database_repository import (
    add_weight_record,
    list_meal_plans,
    list_weight_records,
    save_profile_and_meal_plan,
)
from app.db.models import Base, ProfileRecord
from app.schemas.meals import MealPlanRequest
from app.schemas.profile import ProfileRequest
from app.services.meal_plan_service import generate_meal_plan


@pytest.fixture
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
    engine.dispose()


def make_profile() -> ProfileRequest:
    return ProfileRequest.model_validate(
        {
            "age": 30,
            "gender": "female",
            "height_cm": 165,
            "weight_kg": 60,
            "activity_level": "moderate",
            "health_goal": "maintain_weight",
            "food_preferences": ["vegetarian"],
        }
    )


def test_saves_profile_plan_and_optional_weight_record(session: Session) -> None:
    profile = make_profile()
    request = MealPlanRequest.model_validate(
        {
            "profile": profile.model_dump(mode="json"),
            "daily_calorie_target": 2000,
        }
    )
    plan = generate_meal_plan(request)

    profile_record, plan_record = save_profile_and_meal_plan(
        session,
        profile,
        plan,
    )
    weight_record = add_weight_record(
        session,
        profile_record.id,
        59.5,
    )

    assert profile_record.id
    assert plan_record.profile_id == profile_record.id
    assert plan_record.plan_json["meal_plan_id"] == plan_record.id
    assert list_meal_plans(session, profile_record.id)[0].id == plan_record.id
    assert list_weight_records(session, profile_record.id)[0].id == weight_record.id


def test_saved_records_are_available_in_a_new_session(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'persistent.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    profile = make_profile()
    plan_request = MealPlanRequest.model_validate(
        {
            "profile": profile.model_dump(mode="json"),
            "daily_calorie_target": 2000,
        }
    )
    with factory() as first_session:
        saved_profile, saved_plan = save_profile_and_meal_plan(
            first_session,
            profile,
            generate_meal_plan(plan_request),
        )
        profile_id = saved_profile.id
        meal_plan_id = saved_plan.id

    with factory() as reopened_session:
        assert reopened_session.get(ProfileRecord, profile_id) is not None
        assert [
            plan.id for plan in list_meal_plans(reopened_session, profile_id)
        ] == [meal_plan_id]
    engine.dispose()
