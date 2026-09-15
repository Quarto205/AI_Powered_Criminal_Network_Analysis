import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.session import get_session_factory
from backend.db.models.analytics import AuditLog
from backend.db.models.identity import User
from uuid import uuid4
from datetime import datetime, timezone

def test_audit():
    factory = get_session_factory()
    db = factory()
    
    # 1. create dummy user
    u_id = uuid4()
    u = User(user_id=u_id, username="test_audit", email="test@audit.com", password_hash="hash", account_status="ACTIVE")
    db.add(u)
    db.commit()
    
    # 2. insert audit log
    log_id = uuid4()
    log = AuditLog(
        audit_id=log_id,
        actor_uuid=u_id,
        action_code="TEST",
        timestamp=datetime.now(timezone.utc),
        outcome="SUCCESS"
    )
    db.add(log)
    db.commit()
    
    print("Inserted successfully")
    
    # 3. try to update
    try:
        log.outcome = "DENIED"
        db.commit()
        print("UPDATE SUCCEEDED (THIS IS BAD)")
    except Exception as e:
        print("UPDATE FAILED (THIS IS GOOD):", e)
        db.rollback()
        
    # 4. try to delete
    try:
        db.delete(log)
        db.commit()
        print("DELETE SUCCEEDED (THIS IS BAD)")
    except Exception as e:
        print("DELETE FAILED (THIS IS GOOD):", e)
        db.rollback()
        
    db.close()

if __name__ == "__main__":
    test_audit()
