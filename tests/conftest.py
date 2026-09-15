"""
Root test configuration for SIH26189.
Ensures environment and interpreter compatibility before tests run.
"""

import sys

# On Windows with Python 3.14, the installed experimental MinGW build of numpy
# has an access violation in float128 initialization.
# Since SIH26189 Backend does not depend on numpy (and neo4j uses it only optionally for hydration),
# disabling numpy hydration in neo4j prevents interpreter crashes.
if sys.version_info >= (3, 14) and "numpy" not in sys.modules:
    sys.modules["numpy"] = None

# On Windows, pytest tmpdir cleanup of dead symlinks (pytest-current) can raise WinError 5
try:
    import _pytest.pathlib
    _orig_cleanup = _pytest.pathlib.cleanup_dead_symlinks
    def _safe_cleanup_dead_symlinks(root):
        try:
            return _orig_cleanup(root)
        except Exception:
            pass
    _pytest.pathlib.cleanup_dead_symlinks = _safe_cleanup_dead_symlinks
except (ImportError, AttributeError):
    pass
