"""
Neo4j Graph Database Driver Connection Lifecycle Manager for SIH26189.
Provides connection pooling, health checks, transaction wrappers, and safe graceful shutdown.
"""

import sys
if sys.version_info >= (3, 14) and "numpy" not in sys.modules:
    # Python 3.14 on Windows has an experimental mingw numpy build that segfaults on import.
    # Disabling optional numpy hydration in neo4j prevents access violation.
    sys.modules["numpy"] = None

import logging
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import (
    AuthError,
    ConfigurationError,
    ServiceUnavailable,
    Neo4jError,
)

from backend.config.neo4j import Neo4jSettings, get_neo4j_settings

logger = logging.getLogger("backend.graph.connection")


class GraphConnectionStatus:
    HEALTHY = "healthy"
    UNAVAILABLE = "unavailable"
    AUTHENTICATION_FAILURE = "authentication_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    ERROR = "error"


class Neo4jConnectionManager:
    """
    Manages the lifecycle of the Neo4j driver connection pool.
    Never exposes raw passwords or sensitive credentials in logs or errors.
    """
    def __init__(self, settings: Optional[Neo4jSettings] = None):
        self._settings = settings or get_neo4j_settings()
        self._driver: Optional[Driver] = None

    def get_driver(self) -> Driver:
        """Initializes or returns the existing pooled Neo4j driver."""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self._settings.neo4j_uri,
                    auth=(self._settings.neo4j_user, self._settings.neo4j_password),
                    max_connection_lifetime=self._settings.max_connection_lifetime,
                    max_connection_pool_size=self._settings.max_connection_pool_size,
                    connection_acquisition_timeout=self._settings.connection_acquisition_timeout,
                )
                logger.info(f"Neo4j driver initialized for {self._settings.neo4j_uri}")
            except ConfigurationError as e:
                logger.error("Neo4j configuration error", exc_info=True)
                raise
            except Exception as e:
                logger.error("Failed to initialize Neo4j driver", exc_info=True)
                raise

        return self._driver

    def check_health(self) -> Dict[str, Any]:
        """
        Executes a lightweight connectivity verification.
        Distinguishes healthy, unavailable, auth failure, and configuration error.
        """
        try:
            driver = self.get_driver()
            with driver.session(database=self._settings.neo4j_database) as session:
                result = session.run("RETURN 1 AS ping")
                record = result.single()
                if record and record["ping"] == 1:
                    return {"status": GraphConnectionStatus.HEALTHY, "database": self._settings.neo4j_database}
            return {"status": GraphConnectionStatus.ERROR, "message": "Unexpected health check response"}
        except AuthError:
            logger.warning("Neo4j health check failed: authentication error")
            return {"status": GraphConnectionStatus.AUTHENTICATION_FAILURE}
        except ConfigurationError:
            logger.warning("Neo4j health check failed: configuration error")
            return {"status": GraphConnectionStatus.CONFIGURATION_FAILURE}
        except (ServiceUnavailable, OSError) as e:
            logger.warning(f"Neo4j health check failed: service unavailable ({type(e).__name__})")
            return {"status": GraphConnectionStatus.UNAVAILABLE}
        except Exception as e:
            logger.warning(f"Neo4j health check failed: {type(e).__name__}")
            return {"status": GraphConnectionStatus.ERROR}

    def is_healthy(self) -> bool:
        """Simple boolean check for graph availability."""
        health = self.check_health()
        return health.get("status") == GraphConnectionStatus.HEALTHY

    def get_session(self, access_mode: Optional[str] = None) -> Session:
        """Returns a managed session from the driver pool."""
        driver = self.get_driver()
        return driver.session(
            database=self._settings.neo4j_database,
            default_access_mode=access_mode,
        )

    def close(self) -> None:
        """Gracefully closes driver connection pool."""
        if self._driver is not None:
            try:
                self._driver.close()
                logger.info("Neo4j driver successfully closed.")
            except Exception as e:
                logger.error("Error closing Neo4j driver", exc_info=True)
            finally:
                self._driver = None


_graph_manager: Optional[Neo4jConnectionManager] = None


def get_graph_manager() -> Neo4jConnectionManager:
    """Singleton getter for the Neo4j connection manager."""
    global _graph_manager
    if _graph_manager is None:
        _graph_manager = Neo4jConnectionManager()
    return _graph_manager


def set_graph_manager(manager: Optional[Neo4jConnectionManager]) -> None:
    """Explicitly override graph manager (primarily for mock testing)."""
    global _graph_manager
    _graph_manager = manager
