"""
Append-only and immutability enforcement for SIH26189.
Provides PostgreSQL trigger definitions and SQLAlchemy ORM event listeners
enforcing database-level and application-level immutability for source records
and audit logs.

Immutable Tables:
- documents
- document_versions
- document_chunks
- events
- communications
- transactions
- audit_logs (strictly append-only: UPDATE and DELETE blocked)
"""

from typing import Type
from sqlalchemy import event
from sqlalchemy.orm import Mapper

IMMUTABLE_TABLE_NAMES = [
    "documents",
    "document_versions",
    "document_chunks",
    "events",
    "communications",
    "transactions",
    "audit_logs",
]


class ImmutableRecordError(Exception):
    """Raised when an attempt is made to mutate or delete an immutable/append-only record."""
    pass


# PostgreSQL DDL for trigger function and table triggers
PG_TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION prevent_record_modification()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'documents' AND TG_OP = 'UPDATE' THEN
        IF OLD.document_id = NEW.document_id AND OLD.case_id = NEW.case_id AND OLD.file_type = NEW.file_type AND OLD.file_hash = NEW.file_hash AND OLD.storage_key = NEW.storage_key AND OLD.created_at = NEW.created_at THEN
            RETURN NEW;
        END IF;
    END IF;
    RAISE EXCEPTION 'Operation % is strictly prohibited on immutable table %. Source records and audit logs are append-only.', TG_OP, TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;
"""

PG_DROP_TRIGGER_FUNCTION_SQL = """
DROP FUNCTION IF EXISTS prevent_record_modification() CASCADE;
"""


def generate_pg_trigger_ddl(table_name: str) -> str:
    """Generates PostgreSQL trigger DDL to block UPDATE and DELETE on a table."""
    return f"""
CREATE OR REPLACE TRIGGER trg_immutable_{table_name}
BEFORE UPDATE OR DELETE ON {table_name}
FOR EACH ROW
EXECUTE FUNCTION prevent_record_modification();
"""


def generate_pg_drop_trigger_ddl(table_name: str) -> str:
    """Generates PostgreSQL DDL to drop immutability trigger on a table."""
    return f"DROP TRIGGER IF EXISTS trg_immutable_{table_name} ON {table_name};"


def register_orm_immutability_listener(model_class: Type) -> None:
    """
    Registers SQLAlchemy event listeners on the given model class to reject
    UPDATE and DELETE operations across all database backends (including SQLite in tests).
    """
    @event.listens_for(model_class, "before_update")
    def _block_update(mapper: Mapper, connection, target):
        if model_class.__tablename__ == "documents":
            from sqlalchemy import inspect
            state = inspect(target)
            for attr in state.attrs:
                if attr.history.has_changes() and attr.key != "status":
                    raise ImmutableRecordError(
                        f"UPDATE operation is strictly forbidden on immutable entity 'documents'. "
                        f"Source records and audit trails are append-only."
                    )
            return
        
        raise ImmutableRecordError(
            f"UPDATE operation is strictly forbidden on immutable entity '{model_class.__tablename__}'. "
            f"Source records and audit trails are append-only."
        )

    @event.listens_for(model_class, "before_delete")
    def _block_delete(mapper: Mapper, connection, target):
        raise ImmutableRecordError(
            f"DELETE operation is strictly forbidden on immutable entity '{model_class.__tablename__}'. "
            f"Source records and audit trails are append-only."
        )
