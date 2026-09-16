"""
Domain D: AI, Analytics, and Audit Models for SIH26189.
Tables:
24. model_runs
25. predictions
26. risk_scores
27. alerts
28. graph_snapshots
29. audit_logs (strictly append-only)
30. saved_queries
31. exports
32. agent3_datasets
33. network_metrics
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Integer,
    func,
)
from sqlalchemy.orm import relationship

from backend.db.base import Base
from backend.db.types import GUIDType, JSONBType


class Agent3Dataset(Base):
    """
    agent3_datasets table: Registry of imported datasets for Agent 3 analytics.
    """
    __tablename__ = "agent3_datasets"

    dataset_id = Column(GUIDType, primary_key=True, default=uuid4)
    dataset_name = Column(String(100), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    source_file = Column(String(255), nullable=False)
    checksum = Column(String(64), nullable=False)
    node_count = Column(Integer, nullable=False)
    edge_count = Column(Integer, nullable=False)
    schema_version = Column(String(50), nullable=False)
    imported_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class ModelRun(Base):
    """
    model_runs table: Execution logs and provenance for AI / SNA / ML pipeline runs.
    """
    __tablename__ = "model_runs"

    run_id = Column(GUIDType, primary_key=True, default=uuid4)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    task_type = Column(String(100), nullable=False)
    input_snapshot_checksum = Column(String(64), nullable=False)
    status = Column(String(50), nullable=False, default="COMPLETED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    predictions = relationship("Prediction", back_populates="model_run", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="model_run", cascade="all, delete-orphan")


class Prediction(Base):
    """
    predictions table: Inferred links and analytical association scores (e.g. from GATv2).
    Never confused with source evidence or guilt.
    """
    __tablename__ = "predictions"

    prediction_id = Column(GUIDType, primary_key=True, default=uuid4)
    run_id = Column(GUIDType, ForeignKey("model_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    source_ref = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False)
    target_ref = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False)
    score = Column(Float, nullable=False)
    calibration = Column(String(50), nullable=False)

    model_run = relationship("ModelRun", back_populates="predictions")
    case = relationship("Case")
    source_entity = relationship("Entity", foreign_keys=[source_ref])
    target_entity = relationship("Entity", foreign_keys=[target_ref])


class RiskScore(Base):
    """
    risk_scores table: Prioritization ranking values and contributing features summary.
    """
    __tablename__ = "risk_scores"

    score_id = Column(GUIDType, primary_key=True, default=uuid4)
    target_entity_uuid = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="RESTRICT"), nullable=False, index=True)
    run_id = Column(GUIDType, ForeignKey("model_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    score_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    features_summary = Column(JSONBType, nullable=True)

    entity = relationship("Entity")
    model_run = relationship("ModelRun", back_populates="risk_scores")


class NetworkMetric(Base):
    """
    network_metrics table: Structural graph analytics (e.g., Degree, Betweenness, K-Core, Communities).
    Derived from deterministic graph projection properties, not predictive models.
    """
    __tablename__ = "network_metrics"

    metric_id = Column(GUIDType, primary_key=True, default=uuid4)
    run_id = Column(GUIDType, ForeignKey("model_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    target_entity_uuid = Column(GUIDType, ForeignKey("entities.entity_id", ondelete="CASCADE"), nullable=True, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=True)
    value_str = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSONBType, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    model_run = relationship("ModelRun")
    case = relationship("Case")
    entity = relationship("Entity")


class Alert(Base):
    """
    alerts table: Deterministic motif alerts and pattern detection findings.
    """
    __tablename__ = "alerts"

    alert_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    rule_id = Column(String(100), nullable=False)
    contributing_entities = Column(JSONBType, nullable=False)
    status = Column(String(50), nullable=False, default="NEW")
    metadata_ = Column("metadata", JSONBType, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    case = relationship("Case")


class GraphSnapshot(Base):
    """
    graph_snapshots table: Tracks sync and projection provenance with Neo4j.
    """
    __tablename__ = "graph_snapshots"

    snapshot_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    source_migration_version = Column(String(100), nullable=False)
    checksum = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    case = relationship("Case")


class AuditLog(Base):
    """
    audit_logs table: Security operations ledger.
    Strictly append-only: both UPDATE and DELETE operations are blocked at DB and ORM layers.
    """
    __tablename__ = "audit_logs"

    audit_id = Column(GUIDType, primary_key=True, default=uuid4)
    actor_uuid = Column(GUIDType, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    action_code = Column(String(100), nullable=False)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="RESTRICT"), nullable=True)
    target_item = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    outcome = Column(String(50), nullable=False)

    __table_args__ = (
        Index("idx_audit_logs_case_actor", "case_id", "actor_uuid"),
    )

    actor = relationship("User")
    case = relationship("Case")


class SavedQuery(Base):
    """
    saved_queries table: Case-scoped structured search templates for investigators.
    """
    __tablename__ = "saved_queries"

    query_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    user_uuid = Column(GUIDType, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    filters_json = Column(JSONBType, nullable=False)

    case = relationship("Case")
    user = relationship("User")


class Export(Base):
    """
    exports table: Immutable index of generated case report artifacts.
    """
    __tablename__ = "exports"

    export_id = Column(GUIDType, primary_key=True, default=uuid4)
    case_id = Column(GUIDType, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    user_uuid = Column(GUIDType, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    artifact_ref = Column(String(512), nullable=False)
    version_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    case = relationship("Case")
    user = relationship("User")
