"""
Neo4j configuration settings for SIH26189.
Supports environment-based configuration for Neo4j analytical graph database.
Never hardcodes credentials or logs sensitive secrets.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class Neo4jSettings(BaseModel):
    """
    Neo4j connection settings.
    Default URI matches local Neo4j Bolt port (7687).
    """
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")
    neo4j_database: str = Field(default="neo4j")
    max_connection_lifetime: int = Field(default=3600)
    max_connection_pool_size: int = Field(default=50)
    connection_acquisition_timeout: float = Field(default=30.0)

    @classmethod
    def from_env(cls) -> "Neo4jSettings":
        """Loads Neo4j settings from environment variables."""
        return cls(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j")),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
            connection_acquisition_timeout=float(os.getenv("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", "30.0")),
        )


_neo4j_settings: Optional[Neo4jSettings] = None


def get_neo4j_settings() -> Neo4jSettings:
    """Singleton getter for Neo4j settings."""
    global _neo4j_settings
    if _neo4j_settings is None:
        _neo4j_settings = Neo4jSettings.from_env()
    return _neo4j_settings


def set_neo4j_settings(settings: Optional[Neo4jSettings]) -> None:
    """Explicitly override settings (primarily for testing)."""
    global _neo4j_settings
    _neo4j_settings = settings
