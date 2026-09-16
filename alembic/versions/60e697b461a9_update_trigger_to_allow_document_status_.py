"""update trigger to allow document status update

Revision ID: 60e697b461a9
Revises: 0003
Create Date: 2026-09-15 17:57:00.063101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60e697b461a9'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from backend.db.triggers import PG_TRIGGER_FUNCTION_SQL

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(PG_TRIGGER_FUNCTION_SQL)

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Restore the old function
        op.execute("""
        CREATE OR REPLACE FUNCTION prevent_record_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Operation % is strictly prohibited on immutable table %. Source records and audit logs are append-only.', TG_OP, TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
        """)
