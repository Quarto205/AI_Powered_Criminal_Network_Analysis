"""Add relationship evidence state check constraint and entity identifier unique constraint

Revision ID: 0002_evidence_state_constraints
Revises: 0001_initial_schema
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_evidence_state_constraints'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Check constraint on relationships.status
    with op.batch_alter_table('relationships') as batch_op:
        batch_op.create_check_constraint(
            'ck_relationships_status',
            "status IN ('OBSERVED', 'CORROBORATED', 'CONFIRMED', 'REJECTED', 'INFERRED')"
        )

    # 2. Unique constraint on entity_identifiers (entity_id, type, normalized_value_hash)
    with op.batch_alter_table('entity_identifiers') as batch_op:
        batch_op.create_unique_constraint(
            'uq_entity_identifiers_entity_type_hash',
            ['entity_id', 'type', 'normalized_value_hash']
        )
        batch_op.create_index(
            'idx_entity_identifiers_type_hash',
            ['type', 'normalized_value_hash']
        )


def downgrade() -> None:
    with op.batch_alter_table('entity_identifiers') as batch_op:
        batch_op.drop_index('idx_entity_identifiers_type_hash')
        batch_op.drop_constraint('uq_entity_identifiers_entity_type_hash', type_='unique')

    with op.batch_alter_table('relationships') as batch_op:
        batch_op.drop_constraint('ck_relationships_status', type_='check')
