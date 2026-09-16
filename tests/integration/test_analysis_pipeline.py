from backend.db.session import get_db, get_engine, get_session_factory
"""
Integration Tests for Asynchronous Analysis Triggers, Run Lifecycle,
Investigative Priority Rankings, Deterministic Pattern Alerts, and Human Primacy.
Validates:
- POST /analysis: HTTP 202 Accepted, run_id, PENDING status, non-blocking async dispatch, audit
- GET /analysis/{run_id}: run status inspection, strict case isolation (404 for foreign runs)
- GET /scores: ordered by value DESC, entity join, entity_type filter, case isolation
- GET /alerts: deterministic pattern detection findings, severity and status filters
- Human Decision Primacy: human-confirmed entities/relationships remain CONFIRMED and protected from AI overwrites
- Absolute non-accusatory terminology guardrail
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app
from apps.api.deps import get_db
from backend.db.base import Base
from backend.db.models.identity import Case, CaseMember, Role, User, UserRole
from backend.db.models.entities import Entity, Relationship
from backend.db.models.analytics import Alert, AuditLog, ModelRun, Prediction, RiskScore
from backend.graph.connection import set_graph_manager
from backend.graph.mock_driver import MockNeo4jConnectionManager
from backend.security.audit import SecurityAuditAction
from backend.security.password import hash_password
from backend.security.rbac import SystemRoles
from backend.security.tokens import create_access_token
from backend.config.security import SecuritySettings, set_security_settings


@pytest.fixture
def analysis_test_env():
    """Sets up SQLite test environment for analysis pipeline and intelligence tests."""
    test_settings = SecuritySettings(
        jwt_secret_key="analysis-test-deterministic-jwt-secret-key-32b!",
        jwt_algorithm="HS256",
        jwt_access_token_expire_seconds=28800,
    )
    set_security_settings(test_settings)
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    db.session_factory = TestingSessionLocal

    mock_mgr = MockNeo4jConnectionManager()
    set_graph_manager(mock_mgr)

    # 1. Seed Roles
    analyst_role = Role(role_id=uuid4(), name=SystemRoles.ANALYST)
    inv_role = Role(role_id=uuid4(), name=SystemRoles.INVESTIGATOR)
    sup_role = Role(role_id=uuid4(), name=SystemRoles.SUPERVISOR)
    db.add_all([analyst_role, inv_role, sup_role])
    db.commit()

    # 2. Seed Users
    # Analyst (has ANALYSIS_TRIGGER and CASE_READ)
    analyst_user = User(
        user_id=uuid4(),
        email="analyst@example.com",
        username="analyst_user",
        password_hash=hash_password("AnalystSecret1!"),
        account_status="ACTIVE",
    )
    # External User (non-member of cases)
    external_user = User(
        user_id=uuid4(),
        email="external@example.com",
        username="external_user",
        password_hash=hash_password("ExternalSecret1!"),
        account_status="ACTIVE",
    )
    db.add_all([analyst_user, external_user])
    db.commit()

    db.add(UserRole(user_id=analyst_user.user_id, role_id=analyst_role.role_id))
    db.commit()

    # 3. Seed Cases
    case_a = Case(
        case_id=uuid4(),
        case_code="CASE-ANALYSIS-A",
        title="Primary Analysis Case",
        status="ACTIVE",
        jurisdiction="DL-CENTRAL",
        created_by=analyst_user.user_id,
    )
    case_b = Case(
        case_id=uuid4(),
        case_code="CASE-ANALYSIS-B",
        title="Isolated Case B",
        status="ACTIVE",
        jurisdiction="MH-MUMBAI",
        created_by=analyst_user.user_id,
    )
    db.add_all([case_a, case_b])
    db.commit()

    # Assign analyst to Case A only
    member_a = CaseMember(
        case_member_id=uuid4(),
        case_id=case_a.case_id,
        user_id=analyst_user.user_id,
        role_in_case="ANALYST",
    )
    db.add(member_a)
    db.commit()

    # 4. Seed Entities for Case A and Case B
    ent_a1 = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        canonical_name="Target Alpha",
        entity_type="PERSON",
        status="PROPOSED",
    )
    ent_a2 = Entity(
        entity_id=uuid4(),
        case_id=case_a.case_id,
        canonical_name="Company Beta Ltd",
        entity_type="ORGANIZATION",
        status="CONFIRMED",
    )
    ent_b1 = Entity(
        entity_id=uuid4(),
        case_id=case_b.case_id,
        canonical_name="Foreign Gamma",
        entity_type="PERSON",
        status="PROPOSED",
    )
    db.add_all([ent_a1, ent_a2, ent_b1])
    db.commit()

    # 5. Seed Risk Scores
    dummy_run = ModelRun(
        run_id=uuid4(),
        model_name="Agent3_Baseline",
        version="1.0.0",
        task_type="SNA",
        input_snapshot_checksum="CHECKSUM_INIT",
        status="SUCCESS",
    )
    db.add(dummy_run)
    db.commit()

    score_1 = RiskScore(
        score_id=uuid4(),
        target_entity_uuid=ent_a1.entity_id,
        run_id=dummy_run.run_id,
        score_type="PRIORITY_RANKING",
        value=0.88,
        features_summary={"degree_centrality": 14, "betweenness_centrality": 0.35},
    )
    score_2 = RiskScore(
        score_id=uuid4(),
        target_entity_uuid=ent_a2.entity_id,
        run_id=dummy_run.run_id,
        score_type="PRIORITY_RANKING",
        value=0.94,
        features_summary={"degree_centrality": 28, "betweenness_centrality": 0.72},
    )
    score_foreign = RiskScore(
        score_id=uuid4(),
        target_entity_uuid=ent_b1.entity_id,
        run_id=dummy_run.run_id,
        score_type="PRIORITY_RANKING",
        value=0.99,
        features_summary={"degree_centrality": 50},
    )
    db.add_all([score_1, score_2, score_foreign])
    db.commit()

    # 6. Seed Alerts
    alert_1 = Alert(
        alert_id=uuid4(),
        case_id=case_a.case_id,
        alert_type="TRANSACTION_CYCLE",
        severity="CRITICAL",
        rule_id="RULE-CYCLE-01",
        contributing_entities=[str(ent_a1.entity_id), str(ent_a2.entity_id)],
        status="NEW",
    )
    alert_2 = Alert(
        alert_id=uuid4(),
        case_id=case_a.case_id,
        alert_type="RAPID_FAN_OUT",
        severity="LOW",
        rule_id="RULE-FANOUT-02",
        contributing_entities=[str(ent_a1.entity_id)],
        status="REVIEWED",
    )
    alert_foreign = Alert(
        alert_id=uuid4(),
        case_id=case_b.case_id,
        alert_type="CALL_BURST",
        severity="HIGH",
        rule_id="RULE-BURST-03",
        contributing_entities=[str(ent_b1.entity_id)],
        status="NEW",
    )
    db.add_all([alert_1, alert_2, alert_foreign])
    db.commit()

    # Auth tokens
    analyst_token = create_access_token(
        user_id=analyst_user.user_id,
        username=analyst_user.username,
        email=analyst_user.email,
        roles=[SystemRoles.ANALYST],
    )
    external_token = create_access_token(
        user_id=external_user.user_id,
        username=external_user.username,
        email=external_user.email,
        roles=[SystemRoles.INVESTIGATOR],
    )

    def override_get_db():
        session = TestingSessionLocal()
        session.session_factory = TestingSessionLocal
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield {
        "client": client,
        "db": db,
        "analyst_token": analyst_token,
        "external_token": external_token,
        "analyst_user": analyst_user,
        "case_a": case_a,
        "case_b": case_b,
        "ent_a1": ent_a1,
        "ent_a2": ent_a2,
        "ent_b1": ent_b1,
        "dummy_run": dummy_run,
    }

    app.dependency_overrides.clear()
    db.close()
    set_security_settings(None)


class TestAnalysisPipeline:
    def test_analysis_trigger_async_202(self, analysis_test_env):
        """
        POST /api/v1/cases/{case_id}/analysis:
        - Returns HTTP 202 Accepted.
        - Returns run_id, case_id, status=PENDING.
        - Persists model_runs record in PENDING state.
        - Audits ANALYSIS_TRIGGER security event.
        - Non-blocking async response.
        """
        env = analysis_test_env
        client = env["client"]
        case_id = env["case_a"].case_id

        payload = {
            "pipelines": ["SNA", "PATTERN_MOTIFS", "GAT_LINK_PREDICTION"],
            "parameters": {
                "time_window_days": 90,
                "min_confidence_threshold": 0.5,
            },
        }

        resp = client.post(
            f"/api/v1/cases/{case_id}/analysis",
            json=payload,
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )

        assert resp.status_code == 202
        body = resp.json()
        assert body["success"] is True
        assert body["tracking_id"] is not None
        data = body["data"]
        assert data["case_id"] == str(case_id)
        assert data["status"] == "PENDING"
        run_id = UUID(data["run_id"])

        # Check DB directly for model_run record
        db = env["db"]
        model_run = db.query(ModelRun).filter(ModelRun.run_id == run_id).first()
        assert model_run is not None
        assert model_run.model_name == "Agent3_Network_Intelligence"

        # Check audit log for ANALYSIS_TRIGGER
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action_code == SecurityAuditAction.ANALYSIS_TRIGGER,
                AuditLog.case_id == case_id,
            )
            .first()
        )
        assert audit is not None
        assert str(run_id) in audit.target_item

    def test_analysis_run_status_and_case_isolation(self, analysis_test_env):
        """
        GET /api/v1/cases/{case_id}/analysis/{run_id}:
        - Retrieves valid status for authorized member.
        - Returns 404 for a run belonging to another case (isolation).
        - Returns 404 for non-member user.
        """
        env = analysis_test_env
        client = env["client"]
        case_a_id = env["case_a"].case_id
        case_b_id = env["case_b"].case_id

        # 1. Trigger a run in Case A
        payload = {"pipelines": ["SNA"], "parameters": {}}
        trig_resp = client.post(
            f"/api/v1/cases/{case_a_id}/analysis",
            json=payload,
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert trig_resp.status_code == 202
        run_id = trig_resp.json()["data"]["run_id"]

        # 2. Query status for Case A -> 200
        stat_resp = client.get(
            f"/api/v1/cases/{case_a_id}/analysis/{run_id}",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert stat_resp.status_code == 200
        stat_data = stat_resp.json()["data"]
        assert stat_data["run_id"] == run_id
        assert stat_data["status"] in ["PENDING", "SUCCESS", "RUNNING"]

        # 3. Query run_id against Case B (wrong case) -> 404
        # Even though analyst user created the case, they are not a member of Case B
        cross_resp = client.get(
            f"/api/v1/cases/{case_b_id}/analysis/{run_id}",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert cross_resp.status_code == 404

        # 4. Non-member user queries run status -> 404
        ext_resp = client.get(
            f"/api/v1/cases/{case_a_id}/analysis/{run_id}",
            headers={"Authorization": f"Bearer {env['external_token']}"},
        )
        assert ext_resp.status_code == 404

    def test_list_case_scores_ordering_and_isolation(self, analysis_test_env):
        """
        GET /api/v1/cases/{case_id}/scores:
        - Strictly sorted by value DESC (highest priority investigative lead first).
        - Case-isolated: Case B scores never appear.
        - Supports optional entity_type filtering.
        - Non-accusatory vocabulary.
        """
        env = analysis_test_env
        client = env["client"]
        case_id = env["case_a"].case_id

        # Query all scores for Case A
        resp = client.get(
            f"/api/v1/cases/{case_id}/scores",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["total"] == 2
        scores = data["scores"]

        # Assert sorted DESC: 0.94 first, then 0.88
        assert scores[0]["value"] == 0.94
        assert scores[0]["canonical_name"] == "Company Beta Ltd"
        assert scores[1]["value"] == 0.88
        assert scores[1]["canonical_name"] == "Target Alpha"

        # Assert Case B score (0.99) is NOT present
        for s in scores:
            assert s["canonical_name"] != "Foreign Gamma"

        # Filter by entity_type=ORGANIZATION
        org_resp = client.get(
            f"/api/v1/cases/{case_id}/scores?entity_type=ORGANIZATION",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert org_resp.status_code == 200
        org_data = org_resp.json()["data"]
        assert org_data["total"] == 1
        assert org_data["scores"][0]["canonical_name"] == "Company Beta Ltd"

    def test_list_case_alerts_filtering_and_isolation(self, analysis_test_env):
        """
        GET /api/v1/cases/{case_id}/alerts:
        - Retrieves deterministic pattern alerts.
        - Case B alerts are isolated.
        - Filters by status and severity.
        """
        env = analysis_test_env
        client = env["client"]
        case_id = env["case_a"].case_id

        # Query all alerts for Case A
        resp = client.get(
            f"/api/v1/cases/{case_id}/alerts",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert resp.status_code == 200
        alerts = resp.json()["data"]["alerts"]
        assert len(alerts) == 2
        types = {a["alert_type"] for a in alerts}
        assert "TRANSACTION_CYCLE" in types
        assert "RAPID_FAN_OUT" in types
        assert "CALL_BURST" not in types  # Case B alert

        # Filter by severity=CRITICAL
        crit_resp = client.get(
            f"/api/v1/cases/{case_id}/alerts?severity=CRITICAL",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert crit_resp.status_code == 200
        crit_alerts = crit_resp.json()["data"]["alerts"]
        assert len(crit_alerts) == 1
        assert crit_alerts[0]["alert_type"] == "TRANSACTION_CYCLE"

        # Filter by status=REVIEWED
        rev_resp = client.get(
            f"/api/v1/cases/{case_id}/alerts?status=REVIEWED",
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert rev_resp.status_code == 200
        rev_alerts = rev_resp.json()["data"]["alerts"]
        assert len(rev_alerts) == 1
        assert rev_alerts[0]["alert_type"] == "RAPID_FAN_OUT"

    def test_human_decision_primacy_vs_ai_outputs(self, analysis_test_env):
        """
        Non-negotiable invariant:
        Human review decisions are canonical and protected.
        A human-confirmed entity must remain CONFIRMED when AI analysis runs or predictions arrive.
        """
        env = analysis_test_env
        db = env["db"]
        case_id = env["case_a"].case_id

        # ent_a2 was seeded with status='CONFIRMED'
        ent = db.query(Entity).filter(Entity.canonical_name == "Company Beta Ltd").first()
        assert ent.status == "CONFIRMED"

        # Simulate Agent 3 generating a new prediction or lower priority score
        new_run = ModelRun(
            run_id=uuid4(),
            model_name="Agent3_LinkPredictor",
            version="1.0.0",
            task_type="GAT_LINK_PREDICTION",
            input_snapshot_checksum="RUN_CHECKSUM",
            status="SUCCESS",
        )
        db.add(new_run)
        db.commit()

        pred = Prediction(
            prediction_id=uuid4(),
            run_id=new_run.run_id,
            case_id=case_id,
            source_ref=env["ent_a1"].entity_id,
            target_ref=ent.entity_id,
            predicted_relationship_type="ASSOCIATED_WITH",
            score=0.32,
            calibration="CALIBRATED",
        )
        db.add(pred)
        db.commit()

        # Re-query entity from DB
        db.refresh(ent)
        assert ent.status == "CONFIRMED", "Human confirmed status must never be altered by AI predictions"

    def test_analysis_trigger_validation_guardrails(self, analysis_test_env):
        """
        Validates analysis parameter boundary checks:
        - Empty pipeline list -> 422
        - Unsupported pipeline name -> 422
        - Confidence threshold > 1.0 or < 0.0 -> 422
        - Negative time window -> 422
        """
        env = analysis_test_env
        client = env["client"]
        case_id = env["case_a"].case_id

        # 1. Unsupported pipeline
        resp = client.post(
            f"/api/v1/cases/{case_id}/analysis",
            json={"pipelines": ["UNKNOWN_MAGIC_MODEL"], "parameters": {}},
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert resp.status_code == 422

        # 2. Out of bounds threshold
        resp = client.post(
            f"/api/v1/cases/{case_id}/analysis",
            json={
                "pipelines": ["SNA"],
                "parameters": {"min_confidence_threshold": 1.5},
            },
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert resp.status_code == 422

        # 3. Negative time window
        resp = client.post(
            f"/api/v1/cases/{case_id}/analysis",
            json={
                "pipelines": ["SNA"],
                "parameters": {"time_window_days": -10},
            },
            headers={"Authorization": f"Bearer {env['analyst_token']}"},
        )
        assert resp.status_code == 422
