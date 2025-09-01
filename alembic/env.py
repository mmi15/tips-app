from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv  # make sure python-dotenv is installed

# --- Alembic Config ---
config = context.config

# Configure logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Load .env and prepare project imports ---
# repo root (where alembic.ini lives)
BASE_DIR = Path(__file__).resolve().parents[1]
# enables: from app.db.models import Base
sys.path.append(str(BASE_DIR))

load_dotenv()  # load .env if present

# Read DATABASE_URL (fallback to local SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tips.db")

# Override sqlalchemy.url from alembic.ini with the env value
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# --- Import Base.metadata (after sys.path and dotenv setup) ---
from app.db.models import Base  # noqa: E402
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode Alembic generates the SQL scripts
    without creating an actual DB connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = url.startswith("sqlite")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=is_sqlite,  # needed for ALTER TABLE on SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this mode Alembic connects to the DB and applies migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        url = str(connection.engine.url)
        is_sqlite = url.startswith("sqlite")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
