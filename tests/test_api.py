"""API tests for calculation and food-data endpoints."""

import asyncio

import httpx

from app.main import app


def request(method: str, url: str, payload: dict[str, object] | None = None) -> httpx.Response:
    """Make an in-process request without the deprecated Starlette test client."""
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, url, json=payload)

    return asyncio.run(send_request())


def test_bmi_endpoint_returns_value_and_caution() -> None:
    response = request(
        "POST",
        "/api/nutrition/bmi",
        {"height_cm": 175, "weight_kg": 70},
    )

    assert response.status_code == 200
    assert response.json()["bmi"] == 22.9
    assert "not a diagnosis" in response.json()["note"]


def test_calorie_endpoint_returns_formula_and_estimate() -> None:
    response = request(
        "POST",
        "/api/nutrition/calories",
        {
            "profile": {
                "age": 30,
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 70,
                "activity_level": "sedentary",
                "health_goal": "maintain_weight",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["maintenance_calories_min_kcal"] == 1979
    assert "Mifflin-St Jeor" in response.json()["formula"]


def test_calorie_endpoint_rejects_minor_profile() -> None:
    response = request(
        "POST",
        "/api/nutrition/calories",
        {
            "profile": {
                "age": 17,
                "gender": "female",
                "height_cm": 165,
                "weight_kg": 55,
                "activity_level": "moderate",
                "health_goal": "maintain_weight",
            }
        },
    )

    assert response.status_code == 422
    assert "adults age 18 and older" in response.text


def test_food_endpoint_lists_and_filters_foods() -> None:
    response = request("GET", "/api/foods?category=fruit&tag=vegan")

    assert response.status_code == 200
    assert {food["id"] for food in response.json()} == {
        "banana_raw",
        "apple_raw_skin",
    }


def test_health_endpoint_remains_available() -> None:
    response = request("GET", "/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_nutrition_analysis_endpoint_sums_selected_foods() -> None:
    response = request(
        "POST",
        "/api/nutrition/analyze",
        {
            "items": [
                {"food_id": "banana_raw", "servings": 1},
                {"food_id": "apple_raw_skin", "servings": 2},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "calories_kcal": 193,
        "protein_g": 1.61,
        "carbohydrates_g": 50.46,
        "fat_g": 0.67,
        "fibre_g": 7.4,
    }


def test_nutrition_analysis_endpoint_returns_not_found_for_unknown_food() -> None:
    response = request(
        "POST",
        "/api/nutrition/analyze",
        {"items": [{"food_id": "unknown", "servings": 1}]},
    )

    assert response.status_code == 404


def test_meal_plan_endpoint_respects_excluded_foods() -> None:
    response = request(
        "POST",
        "/api/meals/generate",
        {
            "daily_calorie_target": 2000,
            "profile": {
                "age": 30,
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 70,
                "activity_level": "sedentary",
                "health_goal": "maintain_weight",
                "excluded_foods": ["egg"],
            },
        },
    )

    assert response.status_code == 200
    assert len(response.json()["meals"]) == 4
    recommended_ids = {
        item["food_id"]
        for meal in response.json()["meals"]
        for item in meal["items"]
    }
    assert "egg_whole_boiled" not in recommended_ids


def test_meal_plan_endpoint_reports_missing_matching_foods() -> None:
    response = request(
        "POST",
        "/api/meals/generate",
        {
            "daily_calorie_target": 2000,
            "profile": {
                "age": 30,
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 70,
                "activity_level": "sedentary",
                "health_goal": "maintain_weight",
                "food_preferences": ["halal"],
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["missing_meals"] == [
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    ]


def test_meal_plan_endpoint_rejects_unusable_calorie_estimate() -> None:
    response = request(
        "POST",
        "/api/meals/generate",
        {
            "profile": {
                "age": 120,
                "gender": "female",
                "height_cm": 1,
                "weight_kg": 1,
                "activity_level": "sedentary",
                "health_goal": "lose_weight",
            }
        },
    )

    assert response.status_code == 422
    assert "invalid calorie estimate" in response.text
