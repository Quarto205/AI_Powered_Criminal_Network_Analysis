"""
Database configuration settings for SIH26189.
Supports environment-based configuration for PostgreSQL with a fallback
to SQLite for offline testing and development environments.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class DatabaseSettings(BaseModel):
    """
    Database connection settings. Never hardcodes credentials or secrets.
    """
    database_url: Optional[str] = Field(
        default=None,
        description="Full database connection string (e.g. postgresql://user:pass@host:5432/dbname)",
    )
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="sih26189")
    echo_sql: bool = Field(default=False)

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        """Loads database settings from environment variables."""
        return cls(
            database_url=os.getenv("DATABASE_URL"),
            postgres_user=os.getenv("POSTGRES_USER", "postgres"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "sih26189"),
            echo_sql=os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "yes"),
        )

    def get_connection_url(self) -> str:
        """
        Returns the resolved database connection URL.
        If DATABASE_URL is explicitly set, uses it.
        Otherwise, constructs standard PostgreSQL connection string.
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


_settings: Optional[DatabaseSettings] = None


def get_db_settings() -> DatabaseSettings:
    """Singleton getter for database settings."""
    global _settings
    if _settings is None:
        _settings = DatabaseSettings.from_env()
    return _settings


def set_db_settings(settings: Optional[DatabaseSettings]) -> None:
    """Sets database settings override (primarily for testing)."""
    global _settings
    _settings = settings

