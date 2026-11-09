"""Schema for validated foods loaded from the structured JSON dataset."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class FoodItem(BaseModel):
    """A food record whose nutrient values are stated for its serving."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    fdc_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    serving_g: float = Field(gt=0, description="Serving mass in grams")
    calories_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    fibre_g: float = Field(ge=0)
    tags: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    source_dataset: str = Field(min_length=1)
    source_url: HttpUrl

    @field_validator("id", "name", "category", "source_dataset")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        """Reject empty strings and remove accidental surrounding whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This value must not be empty.")
        return cleaned

    @field_validator("tags", "allergens")
    @classmethod
    def clean_labels(cls, labels: list[str]) -> list[str]:
        """Normalize labels for reliable case-insensitive filtering."""
        cleaned = [label.strip().casefold() for label in labels]
        if any(not label for label in cleaned):
            raise ValueError("Food labels must not be empty.")
        return cleaned
