"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return a simple status response when the API is available."""
    return {"status": "ok"}
