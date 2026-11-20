"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.foods import router as foods_router
from app.api.routes.agent import router as agent_router
from app.api.routes.health import router as health_router
from app.api.routes.meals import router as meals_router
from app.api.routes.nutrition import router as nutrition_router
from app.api.routes.profile import router as profile_router
from app.core.config import settings
from app.db.session import initialize_database

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize persisted data tables before serving requests."""
    initialize_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(meals_router, prefix="/api")
app.include_router(nutrition_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(foods_router, prefix="/api")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def get_homepage() -> FileResponse:
    """Serve the browser-based dashboard."""
    return FileResponse(FRONTEND_DIR / "index.html")
