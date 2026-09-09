"""
Database session and engine lifecycle management for SIH26189.
Provides connection pooling, transaction boundaries, session factory,
and FastAPI get_db dependency.
"""

from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.database import DatabaseSettings, get_db_settings
from backend.db.base import Base

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine(settings: Optional[DatabaseSettings] = None, custom_url: Optional[str] = None) -> Engine:
    """
    Returns or creates the database engine singleton.
    Configures SQLite foreign key pragmas if using SQLite.
    """
    global _engine
    if _engine is None or custom_url is not None:
        cfg = settings or get_db_settings()
        url = custom_url or cfg.get_connection_url()

        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        engine = create_engine(
            url,
            echo=cfg.echo_sql,
            connect_args=connect_args,
            pool_pre_ping=True,
        )

        # Enforce foreign keys in SQLite
        if engine.dialect.name == "sqlite":
            @event.listens_for(engine, "connect")
            def _enable_sqlite_foreign_keys(dbapi_conn, conn_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        if custom_url is None:
            _engine = engine
        return engine

    return _engine


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """Returns or creates the sessionmaker factory."""
    global _session_factory
    if _session_factory is None or engine is not None:
        eng = engine or get_engine()
        factory = sessionmaker(
            bind=eng,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        if engine is None:
            _session_factory = factory
        return factory
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding an isolated transactional database session.
    Automatically rolls back on exception and closes session after request.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables(engine: Engine) -> None:
    """Creates all 31 registered tables on the target engine."""
    import backend.db.models  # ensure all models are registered
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine: Engine) -> None:
    """Drops all registered tables on the target engine."""
    import backend.db.models
    Base.metadata.drop_all(bind=engine)
