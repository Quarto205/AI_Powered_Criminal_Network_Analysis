"""Initial migration creating 31 canonical tables and append-only triggers

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from backend.db.triggers import (
    PG_TRIGGER_FUNCTION_SQL,
    PG_DROP_TRIGGER_FUNCTION_SQL,
    generate_pg_trigger_ddl,
    generate_pg_drop_trigger_ddl,
    IMMUTABLE_TABLE_NAMES,
)

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------------------------------
    # 1. DOMAIN A: Identity, RBAC, and Multi-Tenant (Tables 1-6)
    # --------------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('account_status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('user_id', name=op.f('pk_users')),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'roles',
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('role_id', name=op.f('pk_roles')),
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    op.create_table(
        'permissions',
        sa.Column('permission_id', sa.Uuid(), nullable=False),
        sa.Column('permission_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('permission_id', name=op.f('pk_permissions')),
    )
    op.create_index(op.f('ix_permissions_permission_code'), 'permissions', ['permission_code'], unique=True)

    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], name=op.f('fk_user_roles_role_id_roles'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('fk_user_roles_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id', name=op.f('pk_user_roles')),
    )

    op.create_table(
        'cases',
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('case_code', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('fk_cases_created_by_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('case_id', name=op.f('pk_cases')),
    )
    op.create_index('idx_cases_case_code', 'cases', ['case_code'], unique=True)

    op.create_table(
        'case_members',
        sa.Column('case_member_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role_in_case', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_case_members_case_id_cases'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('fk_case_members_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('case_member_id', name=op.f('pk_case_members')),
        sa.UniqueConstraint('case_id', 'user_id', name='uq_case_members_case_user'),
    )
    op.create_index('idx_case_members_case_user', 'case_members', ['case_id', 'user_id'], unique=False)

    # --------------------------------------------------------------------------
    # 2. DOMAIN B: Ingestion / Source Artifacts (Tables 7-9)
    # --------------------------------------------------------------------------
    op.create_table(
        'documents',
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='RECEIVED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_documents_case_id_cases'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('document_id', name=op.f('pk_documents')),
        sa.UniqueConstraint('case_id', 'file_hash', name='uq_documents_case_hash'),
    )
    op.create_index('idx_documents_case_hash', 'documents', ['case_id', 'file_hash'], unique=True)
    op.create_index(op.f('ix_documents_case_id'), 'documents', ['case_id'], unique=False)

    op.create_table(
        'document_versions',
        sa.Column('version_id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], name=op.f('fk_document_versions_document_id_documents'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('version_id', name=op.f('pk_document_versions')),
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)

    op.create_table(
        'document_chunks',
        sa.Column('chunk_id', sa.Uuid(), nullable=False),
        sa.Column('version_id', sa.Uuid(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('character_span', sa.String(length=100), nullable=True),
        sa.Column('text_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_ref', sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['document_versions.version_id'], name=op.f('fk_document_chunks_version_id_document_versions'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('chunk_id', name=op.f('pk_document_chunks')),
    )
    op.create_index(op.f('ix_document_chunks_version_id'), 'document_chunks', ['version_id'], unique=False)

    # --------------------------------------------------------------------------
    # 3. DOMAIN C: Entities, Relationships, and Evidence (Tables 10-23)
    # --------------------------------------------------------------------------
    op.create_table(
        'entities',
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_entities_case_id_cases'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('entity_id', name=op.f('pk_entities')),
    )
    op.create_index('idx_entities_case_type', 'entities', ['case_id', 'entity_type'], unique=False)

    op.create_table(
        'entity_aliases',
        sa.Column('alias_id', sa.Uuid(), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('alias_text', sa.String(length=255), nullable=False),
        sa.Column('source_ref', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.entity_id'], name=op.f('fk_entity_aliases_entity_id_entities'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alias_id', name=op.f('pk_entity_aliases')),
    )
    op.create_index(op.f('ix_entity_aliases_entity_id'), 'entity_aliases', ['entity_id'], unique=False)

    op.create_table(
        'entity_identifiers',
        sa.Column('identifier_id', sa.Uuid(), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('normalized_value_hash', sa.String(length=64), nullable=False),
        sa.Column('value_policy', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.entity_id'], name=op.f('fk_entity_identifiers_entity_id_entities'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('identifier_id', name=op.f('pk_entity_identifiers')),
    )
    op.create_index(op.f('ix_entity_identifiers_entity_id'), 'entity_identifiers', ['entity_id'], unique=False)

    op.create_table(
        'relationships',
        sa.Column('relationship_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('source_entity_uuid', sa.Uuid(), nullable=False),
        sa.Column('target_entity_uuid', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OBSERVED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_relationships_case_id_cases'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_entity_uuid'], ['entities.entity_id'], name=op.f('fk_relationships_source_entity_uuid_entities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['target_entity_uuid'], ['entities.entity_id'], name=op.f('fk_relationships_target_entity_uuid_entities'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('relationship_id', name=op.f('pk_relationships')),
    )
    op.create_index('idx_relationships_case_source_target', 'relationships', ['case_id', 'source_entity_uuid', 'target_entity_uuid'], unique=False)

    op.create_table(
        'relationship_evidence',
        sa.Column('evidence_id', sa.Uuid(), nullable=False),
        sa.Column('relationship_id', sa.Uuid(), nullable=False),
        sa.Column('source_ref', sa.String(length=255), nullable=False),
        sa.Column('support_type', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['relationship_id'], ['relationships.relationship_id'], name=op.f('fk_relationship_evidence_relationship_id_relationships'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evidence_id', name=op.f('pk_relationship_evidence')),
    )
    op.create_index(op.f('ix_relationship_evidence_relationship_id'), 'relationship_evidence', ['relationship_id'], unique=False)

    op.create_table(
        'events',
        sa.Column('event_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('entity_refs', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_events_case_id_cases'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('event_id', name=op.f('pk_events')),
    )
    op.create_index(op.f('ix_events_case_id'), 'events', ['case_id'], unique=False)

    op.create_table(
        'communications',
        sa.Column('communication_id', sa.Uuid(), nullable=False),
        sa.Column('caller_ref', sa.Uuid(), nullable=False),
        sa.Column('receiver_ref', sa.Uuid(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('timestamps', sa.DateTime(timezone=True), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['caller_ref'], ['entities.entity_id'], name=op.f('fk_communications_caller_ref_entities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['receiver_ref'], ['entities.entity_id'], name=op.f('fk_communications_receiver_ref_entities'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('communication_id', name=op.f('pk_communications')),
    )
    op.create_index(op.f('ix_communications_caller_ref'), 'communications', ['caller_ref'], unique=False)
    op.create_index(op.f('ix_communications_receiver_ref'), 'communications', ['receiver_ref'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('transaction_id', sa.Uuid(), nullable=False),
        sa.Column('sender_ref', sa.Uuid(), nullable=False),
        sa.Column('receiver_ref', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['receiver_ref'], ['entities.entity_id'], name=op.f('fk_transactions_receiver_ref_entities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sender_ref'], ['entities.entity_id'], name=op.f('fk_transactions_sender_ref_entities'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('transaction_id', name=op.f('pk_transactions')),
    )
    op.create_index(op.f('ix_transactions_receiver_ref'), 'transactions', ['receiver_ref'], unique=False)
    op.create_index(op.f('ix_transactions_sender_ref'), 'transactions', ['sender_ref'], unique=False)

    op.create_table(
        'locations',
        sa.Column('location_id', sa.Uuid(), nullable=False),
        sa.Column('normalized_label', sa.String(length=255), nullable=False),
        sa.Column('geography', sa.String(length=255), nullable=True),
        sa.Column('lat_lon_policy', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('location_id', name=op.f('pk_locations')),
    )

    op.create_table(
        'vehicles',
        sa.Column('vehicle_id', sa.Uuid(), nullable=False),
        sa.Column('masked_plate', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('source_refs', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.PrimaryKeyConstraint('vehicle_id', name=op.f('pk_vehicles')),
    )

    op.create_table(
        'organizations',
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('registry_type', sa.String(length=100), nullable=True),
        sa.Column('identifiers', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.PrimaryKeyConstraint('organization_id', name=op.f('pk_organizations')),
    )

    op.create_table(
        'phones',
        sa.Column('phone_id', sa.Uuid(), nullable=False),
        sa.Column('normalized_number', sa.String(length=50), nullable=False),
        sa.Column('active_status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.PrimaryKeyConstraint('phone_id', name=op.f('pk_phones')),
    )

    op.create_table(
        'accounts',
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('masked_identifier', sa.String(length=100), nullable=False),
        sa.Column('bank_type', sa.String(length=50), nullable=True),
        sa.Column('provider', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('account_id', name=op.f('pk_accounts')),
    )

    op.create_table(
        'investigation_notes',
        sa.Column('note_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('author_uuid', sa.Uuid(), nullable=False),
        sa.Column('notes_text', sa.Text(), nullable=False),
        sa.Column('entity_refs', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.ForeignKeyConstraint(['author_uuid'], ['users.user_id'], name=op.f('fk_investigation_notes_author_uuid_users'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_investigation_notes_case_id_cases'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('note_id', name=op.f('pk_investigation_notes')),
    )
    op.create_index(op.f('ix_investigation_notes_case_id'), 'investigation_notes', ['case_id'], unique=False)

    # --------------------------------------------------------------------------
    # 4. DOMAIN D: AI, Analytics, and Audit (Tables 24-31)
    # --------------------------------------------------------------------------
    op.create_table(
        'model_runs',
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('input_snapshot_checksum', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='COMPLETED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('run_id', name=op.f('pk_model_runs')),
    )

    op.create_table(
        'predictions',
        sa.Column('prediction_id', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('source_ref', sa.Uuid(), nullable=False),
        sa.Column('target_ref', sa.Uuid(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('calibration', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_predictions_case_id_cases'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['model_runs.run_id'], name=op.f('fk_predictions_run_id_model_runs'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_ref'], ['entities.entity_id'], name=op.f('fk_predictions_source_ref_entities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['target_ref'], ['entities.entity_id'], name=op.f('fk_predictions_target_ref_entities'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('prediction_id', name=op.f('pk_predictions')),
    )
    op.create_index(op.f('ix_predictions_case_id'), 'predictions', ['case_id'], unique=False)
    op.create_index(op.f('ix_predictions_run_id'), 'predictions', ['run_id'], unique=False)

    op.create_table(
        'risk_scores',
        sa.Column('score_id', sa.Uuid(), nullable=False),
        sa.Column('target_entity_uuid', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('score_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('features_summary', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['model_runs.run_id'], name=op.f('fk_risk_scores_run_id_model_runs'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entity_uuid'], ['entities.entity_id'], name=op.f('fk_risk_scores_target_entity_uuid_entities'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('score_id', name=op.f('pk_risk_scores')),
    )
    op.create_index(op.f('ix_risk_scores_run_id'), 'risk_scores', ['run_id'], unique=False)
    op.create_index(op.f('ix_risk_scores_target_entity_uuid'), 'risk_scores', ['target_entity_uuid'], unique=False)

    op.create_table(
        'alerts',
        sa.Column('alert_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('rule_id', sa.String(length=100), nullable=False),
        sa.Column('contributing_entities', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='NEW', nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_alerts_case_id_cases'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alert_id', name=op.f('pk_alerts')),
    )
    op.create_index(op.f('ix_alerts_case_id'), 'alerts', ['case_id'], unique=False)

    op.create_table(
        'graph_snapshots',
        sa.Column('snapshot_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('source_migration_version', sa.String(length=100), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_graph_snapshots_case_id_cases'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('snapshot_id', name=op.f('pk_graph_snapshots')),
    )
    op.create_index(op.f('ix_graph_snapshots_case_id'), 'graph_snapshots', ['case_id'], unique=False)

    op.create_table(
        'audit_logs',
        sa.Column('audit_id', sa.Uuid(), nullable=False),
        sa.Column('actor_uuid', sa.Uuid(), nullable=False),
        sa.Column('action_code', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=True),
        sa.Column('target_item', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['actor_uuid'], ['users.user_id'], name=op.f('fk_audit_logs_actor_uuid_users'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_audit_logs_case_id_cases'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('audit_id', name=op.f('pk_audit_logs')),
    )
    op.create_index('idx_audit_logs_case_actor', 'audit_logs', ['case_id', 'actor_uuid'], unique=False)

    op.create_table(
        'saved_queries',
        sa.Column('query_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('user_uuid', sa.Uuid(), nullable=False),
        sa.Column('filters_json', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_saved_queries_case_id_cases'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_uuid'], ['users.user_id'], name=op.f('fk_saved_queries_user_uuid_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('query_id', name=op.f('pk_saved_queries')),
    )
    op.create_index(op.f('ix_saved_queries_case_id'), 'saved_queries', ['case_id'], unique=False)
    op.create_index(op.f('ix_saved_queries_user_uuid'), 'saved_queries', ['user_uuid'], unique=False)

    op.create_table(
        'exports',
        sa.Column('export_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('user_uuid', sa.Uuid(), nullable=False),
        sa.Column('artifact_ref', sa.String(length=512), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_exports_case_id_cases'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_uuid'], ['users.user_id'], name=op.f('fk_exports_user_uuid_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('export_id', name=op.f('pk_exports')),
    )
    op.create_index(op.f('ix_exports_case_id'), 'exports', ['case_id'], unique=False)

    # --------------------------------------------------------------------------
    # 5. POSTGRESQL APPEND-ONLY TRIGGER ATTACHMENTS
    # --------------------------------------------------------------------------
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(PG_TRIGGER_FUNCTION_SQL)
        for tbl in IMMUTABLE_TABLE_NAMES:
            op.execute(generate_pg_trigger_ddl(tbl))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for tbl in IMMUTABLE_TABLE_NAMES:
            op.execute(generate_pg_drop_trigger_ddl(tbl))
        op.execute(PG_DROP_TRIGGER_FUNCTION_SQL)

    op.drop_table('exports')
    op.drop_table('saved_queries')
    op.drop_table('audit_logs')
    op.drop_table('graph_snapshots')
    op.drop_table('alerts')
    op.drop_table('risk_scores')
    op.drop_table('predictions')
    op.drop_table('model_runs')
    op.drop_table('investigation_notes')
    op.drop_table('accounts')
    op.drop_table('phones')
    op.drop_table('organizations')
    op.drop_table('vehicles')
    op.drop_table('locations')
    op.drop_table('transactions')
    op.drop_table('communications')
    op.drop_table('events')
    op.drop_table('relationship_evidence')
    op.drop_table('relationships')
    op.drop_table('entity_identifiers')
    op.drop_table('entity_aliases')
    op.drop_table('entities')
    op.drop_table('document_chunks')
    op.drop_table('document_versions')
    op.drop_table('documents')
    op.drop_table('case_members')
    op.drop_table('cases')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
