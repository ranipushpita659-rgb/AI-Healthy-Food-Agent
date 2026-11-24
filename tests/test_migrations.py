"""Coverage for safe baseline migrations and migration management."""

from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect

from app.db.migrations import downgrade_database, upgrade_database


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_fresh_database_is_migrated(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "fresh.db")
    upgrade_database(database_url)

    engine = sa.create_engine(database_url)
    with engine.connect() as connection:
        table_names = set(inspect(connection).get_table_names())
        assert {"profiles", "meal_plans", "weight_records", "alembic_version"} <= table_names
        current = connection.execute(
            sa.text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        assert current == "0001_baseline"
    engine.dispose()


def test_existing_database_rows_survive_baseline(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "existing.db")
    engine = sa.create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "CREATE TABLE profiles "
                "(id VARCHAR(36) PRIMARY KEY, age INTEGER NOT NULL, "
                "gender VARCHAR(32) NOT NULL, height_cm FLOAT NOT NULL, "
                "weight_kg FLOAT NOT NULL, activity_level VARCHAR(32) NOT NULL, "
                "health_goal VARCHAR(32) NOT NULL, food_preferences JSON NOT NULL, "
                "excluded_foods JSON NOT NULL, created_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            sa.text(
                "CREATE TABLE meal_plans "
                "(id VARCHAR(36) PRIMARY KEY, profile_id VARCHAR(36) NOT NULL, "
                "created_at DATETIME NOT NULL, daily_calorie_target_kcal FLOAT NOT NULL, "
                "plan_json JSON NOT NULL)"
            )
        )
        connection.execute(
            sa.text(
                "CREATE TABLE weight_records "
                "(id VARCHAR(36) PRIMARY KEY, profile_id VARCHAR(36) NOT NULL, "
                "weight_kg FLOAT NOT NULL, measured_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO profiles "
                "(id, age, gender, height_cm, weight_kg, activity_level, health_goal, "
                "food_preferences, excluded_foods, created_at) "
                "VALUES ('profile-existing', 30, 'female', 165, 60, 'moderate', "
                "'maintain_weight', '[]', '[]', '2026-11-21 10:00:00')"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO meal_plans "
                "(id, profile_id, created_at, daily_calorie_target_kcal, plan_json) "
                "VALUES ('plan-existing', 'profile-existing', "
                "'2026-11-21 10:01:00', 2000, '{}')"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO weight_records "
                "(id, profile_id, weight_kg, measured_at) "
                "VALUES ('weight-existing', 'profile-existing', 59.5, "
                "'2026-11-21 10:02:00')"
            )
        )
    engine.dispose()

    upgrade_database(database_url)

    migrated_engine = sa.create_engine(database_url)
    with migrated_engine.connect() as connection:
        assert connection.execute(
            sa.text("SELECT COUNT(*) FROM profiles")
        ).scalar_one() == 1
        assert connection.execute(
            sa.text("SELECT COUNT(*) FROM meal_plans")
        ).scalar_one() == 1
        assert connection.execute(
            sa.text("SELECT COUNT(*) FROM weight_records")
        ).scalar_one() == 1
        assert connection.execute(
            sa.text("SELECT weight_kg FROM weight_records")
        ).scalar_one() == 59.5
    migrated_engine.dispose()


def test_alembic_operations_can_add_and_remove_a_new_column(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "column-change.db")
    upgrade_database(database_url)

    engine = sa.create_engine(database_url)
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        operations = Operations(context)
        with operations.batch_alter_table("profiles") as batch:
            batch.add_column(sa.Column("migration_test_marker", sa.String(length=64)))

        assert "migration_test_marker" in {
            column["name"] for column in inspect(connection).get_columns("profiles")
        }

        with operations.batch_alter_table("profiles") as batch:
            batch.drop_column("migration_test_marker")

        assert "migration_test_marker" not in {
            column["name"] for column in inspect(connection).get_columns("profiles")
        }
    engine.dispose()


def test_baseline_downgrade_is_non_destructive(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "safe-downgrade.db")
    upgrade_database(database_url)

    engine = sa.create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO profiles "
                "(id, age, gender, height_cm, weight_kg, activity_level, health_goal, "
                "food_preferences, excluded_foods, created_at) "
                "VALUES ('profile-safe', 25, 'male', 175, 70, 'light', "
                "'maintain_weight', '[]', '[]', '2026-11-21 10:00:00')"
            )
        )
    engine.dispose()

    downgrade_database(database_url, "base")

    preserved_engine = sa.create_engine(database_url)
    with preserved_engine.connect() as connection:
        assert connection.execute(
            sa.text("SELECT COUNT(*) FROM profiles")
        ).scalar_one() == 1
    preserved_engine.dispose()
