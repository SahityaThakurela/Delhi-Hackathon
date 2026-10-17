# Root wrapper for backend/tests/p1_db_smoke.py
import sys
import os

# Add backend directory to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tests.p1_db_smoke import test_p1_db_smoke_all_tables

__all__ = ["test_p1_db_smoke_all_tables"]
