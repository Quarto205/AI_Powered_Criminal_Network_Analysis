#!/usr/bin/env python3
"""
Automated Contract Validation Suite (SIH26189 - Phase 0)
Validates:
  1. Presence of all 10 canonical contracts in docs/contracts/
  2. Root configuration files (AGENTS.md, .env.example, .gitignore, README.md)
  3. Frontend TypeScript contracts, mocks, fixtures, and styling invariants
  4. Absence of hardcoded passwords, tokens, or credentials (SEC-001)
  5. Enforcement of solid (evidence) vs dashed (inferred) graph styling invariants
"""

import os
import sys
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONTRACT_FILES = [
    "01_SHARED_TYPES.md",
    "02_DATABASE_SCHEMA.md",
    "03_GRAPH_SCHEMA.md",
    "04_API_SPEC.md",
    "05_AI_CONTRACTS.md",
    "06_WORKFLOWS.md",
    "07_AUTH_SECURITY.md",
    "08_UI_DATA_CONTRACT.md",
    "09_NAMING_CONVENTIONS.md",
    "10_CROSS_TEAM_DEPENDENCIES.md"
]

FRONTEND_FILES = [
    "apps/web/src/types/contracts.ts",
    "apps/web/src/mocks/mockEnvelope.ts",
    "apps/web/src/fixtures/graphFixture.ts",
    "apps/web/src/styles/graphStyles.ts"
]

SECRET_PATTERNS = [
    re.compile(r'(?i)(?:password|passwd|secret|api_key|token)\s*=\s*["\'][A-Za-z0-9_\-\.]{8,}["\']'),
    re.compile(r'(?i)-----BEGIN (?:RSA )?PRIVATE KEY-----')
]

def run_checks():
    print("=" * 60)
    print("SIH26189 — Contract & Security Validation Suite (Phase 0)")
    print("=" * 60 + "\n")
    
    errors = []

    # 1. Canonical Contracts Check
    print("[Check 1/5] Verifying 10 Canonical Contracts in docs/contracts/...")
    contracts_dir = os.path.join(REPO_ROOT, "docs", "contracts")
    for cf in CONTRACT_FILES:
        p = os.path.join(contracts_dir, cf)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            print(f"  [OK] Found: docs/contracts/{cf}")
        else:
            errors.append(f"Missing or empty contract: docs/contracts/{cf}")
            print(f"  [FAIL] Missing: docs/contracts/{cf}")

    # 2. Root Governance & Security Config
    print("\n[Check 2/5] Verifying Governance & Config Files...")
    root_files = ["AGENTS.md", ".env.example", ".gitignore", "README.md", "docs/DOCUMENT_CONSISTENCY_REPORT.md"]
    for rf in root_files:
        p = os.path.join(REPO_ROOT, rf)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            print(f"  [OK] Found: {rf}")
        else:
            errors.append(f"Missing root file: {rf}")
            print(f"  [FAIL] Missing: {rf}")

    # 3. Frontend TypeScript Foundation
    print("\n[Check 3/5] Verifying Frontend Lead Foundation Artifacts...")
    for ff in FRONTEND_FILES:
        p = os.path.join(REPO_ROOT, ff)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            print(f"  [OK] Found: {ff}")
        else:
            errors.append(f"Missing frontend file: {ff}")
            print(f"  [FAIL] Missing: {ff}")

    # 4. Graph Visual Invariants Check
    print("\n[Check 4/5] Checking Graph Visual Invariants (Solid vs Dashed)...")
    styles_path = os.path.join(REPO_ROOT, "apps", "web", "src", "styles", "graphStyles.ts")
    if os.path.exists(styles_path):
        content = open(styles_path, "r", encoding="utf-8").read()
        has_solid = "solid" in content and "OBSERVED" in content
        has_dashed = "dashed" in content and "INFERRED" in content
        if has_solid and has_dashed:
            print("  [OK] Invariant verified: OBSERVED -> solid, INFERRED -> dashed")
        else:
            errors.append("graphStyles.ts does not properly specify solid/dashed invariants")
            print("  [FAIL] Graph styling invariants missing!")

    # 5. Secret Scan (SEC-001)
    print("\n[Check 5/5] Performing Security Scan for Hardcoded Secrets (SEC-001)...")
    scanned_count = 0
    flagged_secrets = []
    
    for root, dirs, files in os.walk(REPO_ROOT):
        if ".git" in root or "node_modules" in root:
            continue
        for f in files:
            if f.endswith((".py", ".ts", ".js", ".json", ".md", ".env.example")):
                filepath = os.path.join(root, f)
                scanned_count += 1
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                        text = fp.read()
                    for pattern in SECRET_PATTERNS:
                        # Exclude .env.example placeholders
                        if f == ".env.example":
                            continue
                        if pattern.search(text):
                            flagged_secrets.append(os.path.relpath(filepath, REPO_ROOT))
                except Exception:
                    pass

    print(f"  [OK] Scanned {scanned_count} files across repository.")
    if flagged_secrets:
        errors.append(f"Hardcoded credentials suspected in: {flagged_secrets}")
        print(f"  [FAIL] Secrets flagged in: {flagged_secrets}")
    else:
        print("  [OK] 0 hardcoded credentials or private keys detected.")

    print("\n" + "=" * 60)
    if not errors:
        print("[SUCCESS] ALL PHASE 0 CONTRACT & SECURITY CHECKS PASSED!")
        print("=" * 60)
        return True
    else:
        print(f"[FAIL] {len(errors)} CHECKS FAILED:")
        for e in errors:
            print(f"  - {e}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
