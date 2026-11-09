"""Schemas for grounded, backend-mediated AI recommendations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.profile import ProfileRequest


class AgentCandidateFood(BaseModel):
    """Structured food record that may be supplied to a future LLM request."""

    model_config = ConfigDict(extra="forbid")

    food_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    calories_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbohydrates_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    fibre_g: float = Field(ge=0)


class AgentRecommendationRequest(BaseModel):
    """Validated context for a future recommendation explanation."""

    model_config = ConfigDict(extra="forbid")

    profile: ProfileRequest
    calorie_target_kcal: float | None = Field(default=None, gt=0)
    candidate_foods: list[AgentCandidateFood] = Field(default_factory=list)


class AgentRecommendationResponse(BaseModel):
    """Natural-language explanation linked to supplied candidate food IDs."""

    explanation: str
    food_ids: list[str]
    source: Literal["llm", "deterministic"]
