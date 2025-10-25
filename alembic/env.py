# alembic/env.py
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv  # make sure python-dotenv is installed


# --- Alembic Config ---
# This provides access to the Alembic configuration (from alembic.ini)
config = context.config

# Configure logging from alembic.ini
# This sets up loggers so Alembic can output messages
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- Load .env and prepare project imports ---
# Define the base directory (project root, where alembic.ini is located)
BASE_DIR = Path(__file__).resolve().parents[1]
# Add the project base directory to sys.path to allow imports like "from app.db.models import Base"
sys.path.append(str(BASE_DIR))

# Load environment variables from .env file if present
load_dotenv()

# Read DATABASE_URL from environment variables
# If it's not defined, fallback to a local SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tips.db")

# Override the sqlalchemy.url value from alembic.ini
# This ensures migrations use the correct database connection
config.set_main_option("sqlalchemy.url", DATABASE_URL)


# --- Import Base.metadata (after sys.path and dotenv setup) ---
# Import the SQLAlchemy Base from your app models to expose metadata
from app.db.models import Base  # noqa: E402
# Alembic needs target_metadata to compare models with the database schema
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode Alembic generates the SQL migration scripts
    without actually connecting to the database.
    """

    # Get database URL from config
    url = config.get_main_option("sqlalchemy.url")
    # Detect if the DB is SQLite to apply specific settings
    is_sqlite = url.startswith("sqlite")

    # Configure the Alembic context for offline mode
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,              # Embed literal values directly into SQL
        dialect_opts={"paramstyle": "named"},
        compare_type=True,               # Detect changes in column types
        compare_server_default=True,     # Detect changes in server defaults
        render_as_batch=is_sqlite,       # Needed for ALTER TABLE on SQLite
    )

    # Run the migration in a transaction context
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this mode Alembic connects to the DB and applies migrations.
    """

    # Create SQLAlchemy engine using config from alembic.ini
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Disable connection pooling during migrations
        future=True,              # Use SQLAlchemy 2.0 engine behavior
    )

    # Establish connection and run migrations
    with connectable.connect() as connection:
        url = str(connection.engine.url)
        is_sqlite = url.startswith("sqlite")

        # Configure Alembic with active DB connection
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=is_sqlite,  # Enable batch mode for SQLite
        )

        # Run migrations in a transaction block
        with context.begin_transaction():
            context.run_migrations()


# Decide whether to run migrations in offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
