"""Shared pytest configuration and fixtures for the test suite."""

import sys
from pathlib import Path

import pytest

# Ensure project `src/` is on sys.path for local test runs
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _reset_safe_id_map():
    """Reset the global safe_id map before each test to prevent state leakage."""
    from uml_planterator import utils

    utils.reset_id_map()
    yield
    utils.reset_id_map()
