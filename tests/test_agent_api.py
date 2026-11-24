"""API tests for persisted AI recommendations and profile records."""

import asyncio
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import Base
from app.db.session import get_session
from app.main import app


@pytest.fixture
def isolated_database(tmp_path: Path) -> Iterator[None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'api-test.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield
    app.dependency_overrides.pop(get_session, None)
    engine.dispose()


def request(method: str, url: str, payload: dict[str, object] | None = None) -> httpx.Response:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, url, json=payload)

    return asyncio.run(send_request())


@pytest.mark.usefixtures("isolated_database")
def test_recommendation_falls_back_and_persists_history(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.setattr(settings, "llm_model", None)
    payload = {
        "profile": {
            "age": 30,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70,
            "activity_level": "sedentary",
            "health_goal": "maintain_weight",
        },
        "available_foods": ["rice", "egg", "banana", "apple"],
        "daily_calorie_target": 2000,
    }

    response = request("POST", "/api/agent/recommend", payload)

    assert response.status_code == 200
    result = response.json()
    assert result["source"] == "deterministic"
    assert result["meal_plan"]["meal_plan_id"]
    recommended_ids = {
        item["food_id"]
        for meal in result["meal_plan"]["meals"]
        for item in meal["items"]
    }
    assert recommended_ids <= {
        "brown_rice_cooked",
        "white_rice_cooked",
        "egg_whole_boiled",
        "banana_raw",
        "apple_raw_skin",
    }
    profile_id = result["meal_plan"]["profile_id"]

    history = request("GET", f"/api/profiles/{profile_id}/meal-plans")
    assert history.status_code == 200
    assert history.json()[0]["meal_plan_id"] == result["meal_plan"]["meal_plan_id"]

    weight = request(
        "POST",
        f"/api/profiles/{profile_id}/weight-records",
        {"weight_kg": 69.5},
    )
    assert weight.status_code == 201
    assert weight.json()["weight_kg"] == 69.5


@pytest.mark.usefixtures("isolated_database")
def test_profile_can_be_saved_without_generating_a_plan() -> None:
    response = request(
        "POST",
        "/api/profiles",
        {
            "age": 28,
            "gender": "female",
            "height_cm": 160,
            "weight_kg": 55,
            "activity_level": "light",
            "health_goal": "maintain_weight",
        },
    )

    assert response.status_code == 201
    assert response.json()["profile_id"]
