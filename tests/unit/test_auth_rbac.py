"""
Unit Test Suite for Authentication, Password Hashing, JWT Tokens, RBAC, and Security Audit.
Verifies security invariants in 07_AUTH_SECURITY.md and 04_API_SPEC.md.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config.security import SecuritySettings, get_security_settings, set_security_settings
from backend.db.base import Base
from backend.db.models.identity import Role, User, UserRole
from backend.db.models.analytics import AuditLog
from backend.db.triggers import ImmutableRecordError
from backend.security.audit import SecurityAuditAction, record_security_event
from backend.security.password import dummy_verify, hash_password, verify_password
from backend.security.rbac import (
    ANALYST_PERMISSIONS,
    INVESTIGATOR_PERMISSIONS,
    SUPERVISOR_PERMISSIONS,
    Permissions,
    SystemRoles,
    get_permissions_for_roles,
    has_permission,
)
from backend.security.tokens import (
    TokenClaimsError,
    TokenExpiredError,
    TokenTamperedError,
    create_access_token,
    decode_access_token,
)


@pytest.fixture(autouse=True)
def configure_test_security_settings():
    """Sets a deterministic secret key for unit testing."""
    test_settings = SecuritySettings(
        jwt_secret_key="unit-test-deterministic-jwt-secret-key-32bytes!",
        jwt_algorithm="HS256",
        jwt_access_token_expire_seconds=28800,
    )
    set_security_settings(test_settings)
    yield
    set_security_settings(None)


@pytest.fixture
def in_memory_db():
    """Creates a temporary in-memory SQLite database session with Base metadata."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ==============================================================================
# 1. PASSWORD HASHING & VERIFICATION TESTS (Argon2id)
# ==============================================================================

class TestPasswordSecurity:

    def test_argon2id_hashing_not_plaintext(self):
        plain = "InvestigatorSecretPassword123!"
        hashed = hash_password(plain)
        assert plain not in hashed
        assert hashed.startswith("$argon2id$")

    def test_salt_uniqueness(self):
        plain = "SamePasswordTwice"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2  # Unique cryptographic salt per hash

    def test_valid_password_verification(self):
        plain = "ValidInvestigatorPass99#"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_verification_fails(self):
        plain = "CorrectPassword"
        hashed = hash_password(plain)
        assert verify_password("WrongPassword", hashed) is False

    def test_empty_or_malformed_password_fails_safely(self):
        assert verify_password("", "some_hash") is False
        assert verify_password("pass", "") is False
        assert verify_password("pass", "not_an_argon2_hash") is False

    def test_empty_password_hash_raises_value_error(self):
        with pytest.raises(ValueError):
            hash_password("")

    def test_dummy_verify_runs_without_exception(self):
        # Timing attack mitigation must execute safely
        dummy_verify()


# ==============================================================================
# 2. JWT TOKEN GENERATION & CLAIMS TESTS
# ==============================================================================

class TestJWTTokenSecurity:

    def test_token_creation_and_required_claims(self):
        user_id = uuid4()
        username = "investigator_sharma"
        email = "sharma@investigation.gov.in"
        roles = ["INVESTIGATOR"]

        token = create_access_token(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles,
        )
        assert isinstance(token, str)

        claims = decode_access_token(token)
        assert claims["sub"] == str(user_id)
        assert claims["username"] == username
        assert claims["email"] == email
        assert claims["roles"] == roles
        assert "iat" in claims
        assert "exp" in claims
        assert "jti" in claims

        # Enforce 8-hour token validity (28,800 seconds)
        assert claims["exp"] - claims["iat"] == 28800

    def test_expired_token_rejection(self):
        user_id = uuid4()
        # Create token that expired 10 seconds ago
        token = create_access_token(
            user_id=user_id,
            username="investigator_test",
            email="test@sih.gov.in",
            roles=["INVESTIGATOR"],
            custom_expire_seconds=-10,
        )

        with pytest.raises(TokenExpiredError) as exc_info:
            decode_access_token(token)
        assert "expired" in str(exc_info.value).lower()

    def test_tampered_token_signature_rejection(self):
        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            username="analyst_test",
            email="analyst@sih.gov.in",
            roles=["ANALYST"],
        )
        # Tamper payload part of token
        parts = token.split(".")
        tampered_token = f"{parts[0]}.{parts[1][:-4]}abcd.{parts[2]}"

        with pytest.raises(TokenTamperedError):
            decode_access_token(tampered_token)

    def test_token_with_wrong_secret_rejected(self):
        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            username="supervisor_test",
            email="supervisor@sih.gov.in",
            roles=["SUPERVISOR"],
        )
        # Change secret key in configuration
        other_settings = SecuritySettings(
            jwt_secret_key="completely-different-signing-key-32b!",
            jwt_algorithm="HS256",
            jwt_access_token_expire_seconds=28800,
        )
        set_security_settings(other_settings)

        with pytest.raises(TokenTamperedError):
            decode_access_token(token)

    def test_algorithm_confusion_defense(self):
        import jwt
        user_id = uuid4()
        # Attempt to forge an unsigned token ('none' algorithm)
        unsigned_token = jwt.encode(
            {"sub": str(user_id), "username": "attacker", "roles": ["ADMIN"], "iat": 100, "exp": 9999999999, "jti": "abc"},
            key="",
            algorithm="none",
        )
        with pytest.raises(TokenTamperedError):
            decode_access_token(unsigned_token)


# ==============================================================================
# 3. RBAC ROLES & PERMISSIONS TESTS
# ==============================================================================

class TestRBACHierarchy:

    def test_investigator_permissions(self):
        roles = [SystemRoles.INVESTIGATOR]
        assert has_permission(roles, Permissions.CASE_READ) is True
        assert has_permission(roles, Permissions.DOCUMENT_UPLOAD) is True
        assert has_permission(roles, Permissions.GRAPH_READ) is True
        assert has_permission(roles, Permissions.ENTITY_WRITE) is True

        # Investigator must NOT have elevated permissions
        assert has_permission(roles, Permissions.REVIEW_OVERRIDE) is False
        assert has_permission(roles, Permissions.AUDIT_READ) is False
        assert has_permission(roles, Permissions.EXPORT_REPORT) is False
        assert has_permission(roles, Permissions.CASE_CREATE) is False
        assert has_permission(roles, Permissions.ANALYSIS_TRIGGER) is False

    def test_analyst_permissions(self):
        roles = [SystemRoles.ANALYST]
        # Inherits Investigator permissions
        assert has_permission(roles, Permissions.CASE_READ) is True
        assert has_permission(roles, Permissions.DOCUMENT_UPLOAD) is True
        assert has_permission(roles, Permissions.GRAPH_READ) is True

        # Possesses Analyst permissions
        assert has_permission(roles, Permissions.ANALYSIS_TRIGGER) is True
        assert has_permission(roles, Permissions.REVIEW_STAGE) is True
        assert has_permission(roles, Permissions.QUERY_SAVE) is True
        assert has_permission(roles, Permissions.PATTERN_DETECT) is True

        # Analyst must NOT have Supervisor permissions
        assert has_permission(roles, Permissions.REVIEW_OVERRIDE) is False
        assert has_permission(roles, Permissions.AUDIT_READ) is False
        assert has_permission(roles, Permissions.EXPORT_REPORT) is False
        assert has_permission(roles, Permissions.CASE_CREATE) is False
        assert has_permission(roles, Permissions.CASE_ASSIGN_MEMBER) is False

    def test_supervisor_permissions(self):
        roles = [SystemRoles.SUPERVISOR]
        # Possesses all permissions across the hierarchy
        assert has_permission(roles, Permissions.CASE_READ) is True
        assert has_permission(roles, Permissions.ANALYSIS_TRIGGER) is True
        assert has_permission(roles, Permissions.CASE_CREATE) is True
        assert has_permission(roles, Permissions.CASE_ARCHIVE) is True
        assert has_permission(roles, Permissions.CASE_ASSIGN_MEMBER) is True
        assert has_permission(roles, Permissions.REVIEW_OVERRIDE) is True
        assert has_permission(roles, Permissions.AUDIT_READ) is True
        assert has_permission(roles, Permissions.EXPORT_REPORT) is True
        assert has_permission(roles, Permissions.ENTITY_MERGE_APPROVE) is True

    def test_role_aggregation(self):
        # A user with multiple roles inherits the union of their permissions
        roles = [SystemRoles.INVESTIGATOR, "CUSTOM_ANALYTICS"]
        perms = get_permissions_for_roles(roles)
        assert Permissions.DOCUMENT_UPLOAD in perms


# ==============================================================================
# 4. SECURITY AUDIT LOGGING TESTS
# ==============================================================================

class TestSecurityAuditService:

    def test_record_known_actor_security_event(self, in_memory_db):
        user = User(
            user_id=uuid4(),
            username="investigator_audit_test",
            email="audit_test@sih.gov.in",
            password_hash=hash_password("AuditPass123!"),
            account_status="ACTIVE",
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        case_id = uuid4()
        log_entry = record_security_event(
            db=in_memory_db,
            action_code=SecurityAuditAction.AUTH_LOGIN_SUCCESS,
            actor_uuid=user.user_id,
            case_id=case_id,
            target_item="investigator_audit_test",
            outcome="SUCCESS",
        )
        assert log_entry is not None
        assert log_entry.action_code == SecurityAuditAction.AUTH_LOGIN_SUCCESS
        assert log_entry.actor_uuid == user.user_id
        assert log_entry.outcome == "SUCCESS"

        # Verify query from database
        stored = in_memory_db.query(AuditLog).filter_by(audit_id=log_entry.audit_id).first()
        assert stored is not None
        assert stored.actor_uuid == user.user_id

    def test_record_unknown_actor_login_failure(self, in_memory_db):
        # When username does not exist, actor_uuid is None
        # Does not violate DB FK constraint and logs safely
        result = record_security_event(
            db=in_memory_db,
            action_code=SecurityAuditAction.AUTH_LOGIN_FAILURE,
            actor_uuid=None,
            target_item="unknown_user_attempt",
            outcome="FAILURE",
        )
        assert result is None
        # DB audit_logs remains unchanged (no invalid foreign key inserted)
        assert in_memory_db.query(AuditLog).count() == 0

    def test_audit_logs_immutability_enforcement(self, in_memory_db):
        user = User(
            user_id=uuid4(),
            username="immutable_audit_user",
            email="imm_audit@sih.gov.in",
            password_hash=hash_password("Pass123!"),
            account_status="ACTIVE",
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        log_entry = record_security_event(
            db=in_memory_db,
            action_code=SecurityAuditAction.CASE_ACCESS_DENIED,
            actor_uuid=user.user_id,
            outcome="DENIED",
        )

        # Attempt UPDATE on audit_logs must be rejected
        log_entry.outcome = "TAMPERED"
        with pytest.raises(ImmutableRecordError):
            in_memory_db.commit()
        in_memory_db.rollback()

        # Attempt DELETE on audit_logs must be rejected
        in_memory_db.delete(log_entry)
        with pytest.raises(ImmutableRecordError):
            in_memory_db.commit()
