"""Safe baseline for existing and fresh SQLite databases.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-21 10:00:00
"""

from sqlalchemy import inspect
import sqlalchemy as sa
from alembic import op


revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())

    if "profiles" not in existing_tables:
        op.create_table(
            "profiles",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("age", sa.Integer(), nullable=False),
            sa.Column("gender", sa.String(length=32), nullable=False),
            sa.Column("height_cm", sa.Float(), nullable=False),
            sa.Column("weight_kg", sa.Float(), nullable=False),
            sa.Column("activity_level", sa.String(length=32), nullable=False),
            sa.Column("health_goal", sa.String(length=32), nullable=False),
            sa.Column("food_preferences", sa.JSON(), nullable=False),
            sa.Column("excluded_foods", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if "meal_plans" not in existing_tables:
        op.create_table(
            "meal_plans",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("profile_id", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("daily_calorie_target_kcal", sa.Float(), nullable=False),
            sa.Column("plan_json", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if "weight_records" not in existing_tables:
        op.create_table(
            "weight_records",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("profile_id", sa.String(length=36), nullable=False),
            sa.Column("weight_kg", sa.Float(), nullable=False),
            sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {
        table: {index["name"] for index in inspect(connection).get_indexes(table)}
        for table in ("meal_plans", "weight_records")
        if table in set(inspect(connection).get_table_names())
    }
    if "ix_meal_plans_profile_id" not in existing_indexes.get("meal_plans", set()):
        op.create_index(
            "ix_meal_plans_profile_id",
            "meal_plans",
            ["profile_id"],
            unique=False,
        )
    if "ix_weight_records_profile_id" not in existing_indexes.get("weight_records", set()):
        op.create_index(
            "ix_weight_records_profile_id",
            "weight_records",
            ["profile_id"],
            unique=False,
        )


def downgrade() -> None:
    # The baseline represents the application's pre-migration schema.
    # It deliberately does not drop tables or records.
    pass
