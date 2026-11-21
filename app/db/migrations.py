"""Alembic migration commands for application setup and maintenance."""

from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence

from alembic import command
from alembic.config import Config

from app.core.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def get_alembic_config(database_url: str | None = None) -> Config:
    config = Config(str(ALEMBIC_INI))
    url = database_url or settings.database_url
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def upgrade_database(database_url: str | None = None, revision: str = "head") -> None:
    command.upgrade(get_alembic_config(database_url), revision)


def downgrade_database(database_url: str | None = None, revision: str = "-1") -> None:
    command.downgrade(get_alembic_config(database_url), revision)


def show_current(database_url: str | None = None) -> None:
    command.current(get_alembic_config(database_url), verbose=True)


def show_history(database_url: str | None = None) -> None:
    command.history(get_alembic_config(database_url), verbose=True)


def main(argv: Sequence[str] | None = None) -> None:
    parser = ArgumentParser(description="Manage AI Healthy Food Agent database migrations.")
    subcommands = parser.add_subparsers(dest="action", required=True)
    subcommands.add_parser("upgrade", help="Apply pending migrations.")
    subcommands.add_parser("current", help="Show the current database revision.")
    subcommands.add_parser("history", help="Show migration history.")

    downgrade = subcommands.add_parser("downgrade", help="Roll back migrations.")
    downgrade.add_argument("revision", nargs="?", default="-1")

    args = parser.parse_args(argv)
    if args.action == "upgrade":
        upgrade_database()
    elif args.action == "current":
        show_current()
    elif args.action == "history":
        show_history()
    else:
        downgrade_database(revision=args.revision)


if __name__ == "__main__":
    main()
