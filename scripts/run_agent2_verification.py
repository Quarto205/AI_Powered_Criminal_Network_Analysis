#!/usr/bin/env python3
"""
SIH26189 — AGENT 2 FINAL VERIFICATION SUITE
Programmatic test runner that executes the Agent 2 verification suite.
"""

import sys
import pytest
from datetime import datetime

def main():
    print("=" * 60)
    print("SIH26189 — AGENT 2 FINAL VERIFICATION SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # The suite to run
    test_args = [
        "tests/unit/",
        "tests/integration/test_agent2_e2e_pipeline.py",
        "tests/integration/test_regression_pipeline.py",
        "tests/integration/test_degraded_mode_matrix.py",
        "tests/unit/test_phase6_security.py",
        "-v",
        "--tb=short"
    ]

    print(f"Executing: pytest {' '.join(test_args)}\n")
    
    # Run pytest programmatically
    exit_code = pytest.main(test_args)

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("[SUCCESS] All Agent 2 Invariants PASSED! System is GRAPH_READY.")
    else:
        print("[FAILURE] Integration tests failed. Review traceback above.")
    print("=" * 60)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
