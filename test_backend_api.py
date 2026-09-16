import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def run_tests():
    print("=== STARTING BACKEND INTEGRATION TEST ===")
    
    # 1. Login
    res = requests.post(f"{BASE_URL}/auth/login", json={"username": "System_Agent3", "password": "password"})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        sys.exit(1)
    token = res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Logged in successfully.")

    # 2. Get Cases via DB directly to avoid pagination issues
    from backend.db.session import get_engine, get_session_factory
    from backend.db.models.identity import Case
    engine = get_engine()
    SessionLocal = get_session_factory(engine)
    db = SessionLocal()
    case_a = db.query(Case).filter(Case.case_code == "CASE-A").first()
    case_b = db.query(Case).filter(Case.case_code == "CASE-B").first()
    
    if not case_a or not case_b:
        print("Cases not found!")
        sys.exit(1)
        
    case_id = str(case_a.case_id)
    print(f"[OK] Found CASE-A: {case_id}")

    # 3. Trigger Agent 1 (Document Upload)
    files = {'file': ('sample_doc.pdf', open('sample_doc.pdf', 'rb'), 'application/pdf')}
    res = requests.post(f"{BASE_URL}/cases/{case_id}/documents", headers=headers, files=files)
    if res.status_code in [200, 201, 202]:
        print(f"[OK] Document uploaded successfully. Response: {res.json()}")
    else:
        print(f"[FAIL] Document upload failed: {res.status_code} {res.text}")

    # 4. Trigger SNA
    res = requests.post(f"{BASE_URL}/cases/{case_id}/analysis", headers=headers, json={"analysis_type": "SNA", "parameters": {}})
    if res.status_code in [200, 201, 202]:
        run_id = res.json()["data"]["run_id"]
        print(f"[OK] SNA triggered. Run ID: {run_id}")
        
        # Poll
        for _ in range(10):
            status_res = requests.get(f"{BASE_URL}/cases/{case_id}/analysis/{run_id}", headers=headers)
            status = status_res.json()["data"]["status"]
            print(f"  SNA status: {status}")
            if status in ("COMPLETED", "SUCCESS"):
                break
            time.sleep(2)
    else:
        print(f"[FAIL] SNA trigger failed: {res.text}")
        
    # 5. Trigger PATTERNS
    res = requests.post(f"{BASE_URL}/cases/{case_id}/analysis", headers=headers, json={"analysis_type": "PATTERNS", "parameters": {}})
    if res.status_code in [200, 201, 202]:
        run_id = res.json()["data"]["run_id"]
        print(f"[OK] PATTERNS triggered. Run ID: {run_id}")
    else:
        print(f"[FAIL] PATTERNS trigger failed: {res.text}")

    # 6. Trigger GAT_INFERENCE
    res = requests.post(f"{BASE_URL}/cases/{case_id}/analysis", headers=headers, json={"analysis_type": "GAT_INFERENCE", "parameters": {}})
    if res.status_code in [200, 201, 202]:
        run_id = res.json()["data"]["run_id"]
        print(f"[OK] GAT_INFERENCE triggered. Run ID: {run_id}")
    else:
        print(f"[FAIL] GAT_INFERENCE trigger failed: {res.text}")
        
    time.sleep(5) # wait a bit for async tasks to run
    
    # 7. Check Alerts
    res = requests.get(f"{BASE_URL}/cases/{case_id}/alerts", headers=headers)
    if res.status_code == 200:
        alerts = res.json()["data"]["alerts"]
        print(f"[OK] Fetched {len(alerts)} alerts.")
    else:
        print(f"[FAIL] Failed to fetch alerts: {res.text}")

    # 8. Trigger Priority Ranking (uses intelligence router)
    res = requests.post(f"{BASE_URL}/cases/{case_id}/intelligence/priority-rankings", headers=headers)
    if res.status_code in [200, 201]:
        print(f"[OK] Priority rankings triggered: {res.json()}")
    else:
        print(f"[FAIL] Priority ranking failed: {res.text}")

    # 9. Get Leads
    res = requests.get(f"{BASE_URL}/cases/{case_id}/intelligence/leads", headers=headers)
    if res.status_code == 200:
        leads = res.json().get("investigative_leads", [])
        print(f"[OK] Fetched {len(leads)} leads.")
        
        if leads:
            lead_entity_id = leads[0]["entity_id"]
            # 10. Get Explanation for top lead
            res = requests.get(f"{BASE_URL}/cases/{case_id}/intelligence/leads/{lead_entity_id}/explanation", headers=headers)
            print(f"[OK] Explanation status: {res.status_code}")
            if res.status_code == 200:
                 print(f"Explanation data: {res.json().get('content')}")
    else:
        print(f"[FAIL] Failed to fetch leads: {res.text}")
        
    # Check graph
    res = requests.get(f"{BASE_URL}/cases/{case_id}/graph", headers=headers)
    if res.status_code == 200:
        graph = res.json()["data"]
        print(f"[OK] Graph fetched: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges.")
    else:
        print(f"[FAIL] Graph fetch failed: {res.text}")

if __name__ == '__main__':
    run_tests()
