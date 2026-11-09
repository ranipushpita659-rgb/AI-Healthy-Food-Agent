"""Endpoints for the structured food dataset."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.data.food_repository import FoodDataError, list_foods
from app.schemas.food import FoodItem

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/foods", response_model=list[FoodItem])
def get_foods(
    category: str | None = Query(default=None, min_length=1),
    tag: str | None = Query(default=None, min_length=1),
) -> list[FoodItem]:
    """List foods, optionally filtering by exact category or tag."""
    try:
        return list_foods(category=category, tag=tag)
    except FoodDataError as error:
        logger.exception("Could not load the structured food dataset.")
        raise HTTPException(
            status_code=500,
            detail="Food data could not be loaded. Check the server logs.",
        ) from error
