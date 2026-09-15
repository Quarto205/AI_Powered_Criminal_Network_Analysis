from backend.db.session import get_db, get_engine, get_session_factory
"""
Unit Tests for Neo4j Graph Database Integration and Projection Sync.
Validates:
- 100% Parameterized Cypher query generation
- Closed allow-list validation for entity labels and relationship types
- Malicious injection attempts (SQL/Cypher injection characters remain parameters)
- Idempotent entity node projection (1 projection = 1 node; N projections = 1 node)
- Idempotent relationship edge projection
- Full case rebuild determinism & clean purge
- Deterministic SHA-256 checksum stability
- Cytoscape.js output formatting with factual/predicted edge styling
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.base import Base
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.entities import Entity, Relationship, RelationshipEvidence
from backend.db.models.analytics import GraphSnapshot, Prediction
from backend.graph.cypher_builder import (
    CypherBuilder,
    CypherValidationError,
    get_safe_label,
    get_safe_rel_type,
)
from backend.graph.mock_driver import MockNeo4jConnectionManager
from backend.services.graph_projection import GraphProjectionService
from backend.services.graph_query import GraphQueryService


@pytest.fixture
def sqlite_db_session():
    """In-memory SQLite session with full schema initialized."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_graph_manager():
    """Mock connection manager for testing projection and queries."""
    return MockNeo4jConnectionManager()


# ==============================================================================
# 1. CYPHER PARAMETERIZATION & SECURITY INVARIANTS
# ==============================================================================

class TestCypherSecurityAndParameterization:
    """Validates 100% Cypher parameterization and closed allow-lists."""

    def test_entity_upsert_uses_named_parameters(self):
        eid = uuid4()
        cid = uuid4()
        query, params = CypherBuilder.build_entity_upsert(
            entity_id=eid,
            case_id=cid,
            entity_type="PERSON",
            canonical_name="Ramesh Kumar",
            status="ACTIVE",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        assert "$entity_id" in query
        assert "$case_id" in query
        assert "$canonical_name" in query
        assert "$entity_type" in query
        assert str(eid) not in query  # Value must NOT be in query string
        assert str(cid) not in query
        assert "Ramesh Kumar" not in query
        assert params["entity_id"] == str(eid)
        assert params["case_id"] == str(cid)
        assert params["canonical_name"] == "Ramesh Kumar"

    def test_relationship_upsert_uses_named_parameters(self):
        rid = uuid4()
        cid = uuid4()
        src = uuid4()
        tgt = uuid4()
        query, params = CypherBuilder.build_relationship_upsert(
            relationship_id=rid,
            case_id=cid,
            source_id=src,
            target_id=tgt,
            rel_type="CONTACTED",
            status="OBSERVED",
            confidence_score=0.95,
            is_predicted=False,
            provenance_count=2,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        assert "$relationship_id" in query
        assert "$case_id" in query
        assert "$source_id" in query
        assert "$target_id" in query
        assert str(rid) not in query
        assert str(src) not in query
        assert str(tgt) not in query
        assert params["relationship_id"] == str(rid)
        assert params["source_id"] == str(src)
        assert params["target_id"] == str(tgt)

    def test_injection_strings_remain_pure_parameters(self):
        """Malicious Cypher injection strings must remain harmless dict values."""
        eid = uuid4()
        cid = uuid4()
        evil_name = "Alice'; DETACH DELETE n //"
        query, params = CypherBuilder.build_entity_upsert(
            entity_id=eid,
            case_id=cid,
            entity_type="PERSON",
            canonical_name=evil_name,
            status="ACTIVE",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        assert "DETACH DELETE" not in query
        assert params["canonical_name"] == evil_name

    def test_unallowlisted_entity_type_rejected(self):
        with pytest.raises(CypherValidationError):
            get_safe_label("MALICIOUS_LABEL) MATCH (x) //")

    def test_unallowlisted_relationship_type_rejected(self):
        with pytest.raises(CypherValidationError):
            get_safe_rel_type("EVIL_REL]->(m) //")

    def test_case_purge_is_strictly_scoped(self):
        cid = uuid4()
        query, params = CypherBuilder.build_case_purge(cid)
        assert query == "MATCH (n {case_id: $case_id}) DETACH DELETE n"
        assert params["case_id"] == str(cid)
        # Ensure it never performs global purge
        assert query != "MATCH (n) DETACH DELETE n"


# ==============================================================================
# 2. PROJECTION IDEMPOTENCY & GRAPH REBUILD
# ==============================================================================

class TestGraphProjectionIdempotency:
    """Validates that repeated projections produce stable topology."""

    def test_entity_projection_idempotency(self, sqlite_db_session, mock_graph_manager):
        cid = uuid4()
        entity = Entity(
            entity_id=uuid4(),
            case_id=cid,
            entity_type="PERSON",
            canonical_name="Suresh Sharma",
            status="ACTIVE",
            created_at=datetime.now(timezone.utc),
        )
        sqlite_db_session.add(entity)
        sqlite_db_session.commit()

        service = GraphProjectionService(db=sqlite_db_session, graph_manager=mock_graph_manager)

        # Project once
        service.upsert_entity(entity)
        store = mock_graph_manager.mock_driver._store
        assert len(store["nodes"]) == 1

        # Project 5 more times
        for _ in range(5):
            service.upsert_entity(entity)

        # Node count must strictly remain 1
        assert len(store["nodes"]) == 1
        node = store["nodes"][(str(entity.entity_id), str(cid))]
        assert node["canonical_name"] == "Suresh Sharma"

    def test_relationship_projection_idempotency(self, sqlite_db_session, mock_graph_manager):
        cid = uuid4()
        e1 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PERSON", canonical_name="E1", status="ACTIVE")
        e2 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PHONE", canonical_name="E2", status="ACTIVE")
        rel = Relationship(
            relationship_id=uuid4(),
            case_id=cid,
            source_entity_uuid=e1.entity_id,
            target_entity_uuid=e2.entity_id,
            type="OWNS",
            status="OBSERVED",
        )
        sqlite_db_session.add_all([e1, e2, rel])
        sqlite_db_session.commit()

        service = GraphProjectionService(db=sqlite_db_session, graph_manager=mock_graph_manager)
        service.upsert_entity(e1)
        service.upsert_entity(e2)

        # Upsert relationship repeatedly
        for _ in range(4):
            service.upsert_relationship(rel)

        store = mock_graph_manager.mock_driver._store
        assert len(store["edges"]) == 1
        edge = store["edges"][(str(rel.relationship_id), str(cid))]
        assert edge["type"] == "OWNS"

    def test_full_rebuild_from_scratch(self, sqlite_db_session, mock_graph_manager):
        """Simulates full case graph rebuild from canonical PostgreSQL records."""
        cid = uuid4()
        # Seed 5 entities
        entities = [
            Entity(entity_id=uuid4(), case_id=cid, entity_type="PERSON", canonical_name=f"Person {i}", status="ACTIVE")
            for i in range(5)
        ]
        # Seed 4 relationships
        relationships = [
            Relationship(
                relationship_id=uuid4(),
                case_id=cid,
                source_entity_uuid=entities[i].entity_id,
                target_entity_uuid=entities[i + 1].entity_id,
                type="CONTACTED",
                status="OBSERVED",
            )
            for i in range(4)
        ]
        sqlite_db_session.add_all(entities + relationships)
        sqlite_db_session.commit()

        service = GraphProjectionService(db=sqlite_db_session, graph_manager=mock_graph_manager)

        # Rebuild 1
        res1 = service.rebuild_case_graph(cid)
        assert res1["nodes_projected"] == 5
        assert res1["edges_projected"] == 4
        assert res1["checksum"] is not None

        # Verify snapshot ledger in PostgreSQL
        snapshots = sqlite_db_session.query(GraphSnapshot).filter(GraphSnapshot.case_id == cid).all()
        assert len(snapshots) == 1
        assert snapshots[0].checksum == res1["checksum"]

        # Rebuild 2 (should produce identical topology and same checksum)
        res2 = service.rebuild_case_graph(cid)
        assert res2["checksum"] == res1["checksum"]
        assert len(sqlite_db_session.query(GraphSnapshot).filter(GraphSnapshot.case_id == cid).all()) == 2

    def test_checksum_changes_when_canonical_data_changes(self, sqlite_db_session, mock_graph_manager):
        cid = uuid4()
        e1 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PERSON", canonical_name="Alpha", status="ACTIVE")
        sqlite_db_session.add(e1)
        sqlite_db_session.commit()

        service = GraphProjectionService(db=sqlite_db_session, graph_manager=mock_graph_manager)
        res1 = service.rebuild_case_graph(cid)

        # Add new entity to case
        e2 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PERSON", canonical_name="Beta", status="ACTIVE")
        sqlite_db_session.add(e2)
        sqlite_db_session.commit()

        res2 = service.rebuild_case_graph(cid)
        assert res1["checksum"] != res2["checksum"]


# ==============================================================================
# 3. GRAPH QUERY SERVICE & CYTOSCAPE FORMATTING
# ==============================================================================

class TestGraphQueryAndCytoscapeFormatting:
    """Validates graph querying, factual/predicted edge styling, and Cytoscape format."""

    def test_cytoscape_format_and_edge_styling(self, sqlite_db_session, mock_graph_manager):
        cid = uuid4()
        e1 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PERSON", canonical_name="P1", status="ACTIVE")
        e2 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PHONE", canonical_name="Ph1", status="ACTIVE")
        e3 = Entity(entity_id=uuid4(), case_id=cid, entity_type="PERSON", canonical_name="P2", status="ACTIVE")
        rel = Relationship(
            relationship_id=uuid4(),
            case_id=cid,
            source_entity_uuid=e1.entity_id,
            target_entity_uuid=e2.entity_id,
            type="OWNS",
            status="OBSERVED",
        )
        # Prediction
        pred = Prediction(
            prediction_id=uuid4(),
            run_id=uuid4(),
            case_id=cid,
            source_ref=e1.entity_id,
            target_ref=e3.entity_id,
            score=0.75,
            calibration="CALIBRATED",
        )
        sqlite_db_session.add_all([e1, e2, e3, rel, pred])
        sqlite_db_session.commit()

        # Rebuild graph to project both factual and predicted edges
        proj_service = GraphProjectionService(db=sqlite_db_session, graph_manager=mock_graph_manager)
        proj_service.rebuild_case_graph(cid)

        query_service = GraphQueryService(db=sqlite_db_session, graph_manager=mock_graph_manager)

        # Query with predicted edges included
        resp = query_service.get_case_graph(case_id=cid, include_predicted=True)
        assert resp.stats.node_count == 3
        assert resp.stats.edge_count == 2
        assert resp.stats.predicted_edge_count == 1

        # Check solid vs dashed styling
        edge_styles = {e.data.id: e.data.style_line for e in resp.edges}
        assert edge_styles[str(rel.relationship_id)] == "solid"
        assert edge_styles[str(pred.prediction_id)] == "dashed"

        # Query with include_predicted=False
        resp_no_pred = query_service.get_case_graph(case_id=cid, include_predicted=False)
        assert resp_no_pred.stats.edge_count == 1
        assert resp_no_pred.stats.predicted_edge_count == 0
        assert resp_no_pred.edges[0].data.style_line == "solid"
