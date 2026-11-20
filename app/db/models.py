"""SQLAlchemy models for profile and recommendation persistence."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProfileRecord(Base):
    """A saved, validated profile without direct identity fields."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(32))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    activity_level: Mapped[str] = mapped_column(String(32))
    health_goal: Mapped[str] = mapped_column(String(32))
    food_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_foods: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
    )

    meal_plans: Mapped[list["MealPlanRecord"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    weight_records: Mapped[list["WeightRecord"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class MealPlanRecord(Base):
    """A complete deterministic or AI-explained meal-plan snapshot."""

    __tablename__ = "meal_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
    )
    daily_calorie_target_kcal: Mapped[float] = mapped_column(Float)
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    profile: Mapped[ProfileRecord] = relationship(back_populates="meal_plans")


class WeightRecord(Base):
    """An optional dated weight measurement for a saved profile."""

    __tablename__ = "weight_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
    )
    weight_kg: Mapped[float] = mapped_column(Float)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
    )

    profile: Mapped[ProfileRecord] = relationship(back_populates="weight_records")
