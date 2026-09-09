import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure current working directory is in sys.path
sys.path.insert(0, os.path.abspath("."))

# Import database settings and canonical metadata
from backend.config.database import get_db_settings
from backend.db.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata to canonical application metadata containing all 31 tables
target_metadata = Base.metadata


def get_url():
    """Retrieves URL from alembic config option if overridden, else backend settings / environment."""
    cfg_url = config.get_main_option("sqlalchemy.url")
    # If the user or test passed a custom URL (e.g. SQLite test DB), use it
    if cfg_url and not cfg_url.startswith("postgresql+psycopg2://postgres:postgres@localhost:5432/sih_criminal_network"):
        return cfg_url
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return get_db_settings().get_connection_url()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
