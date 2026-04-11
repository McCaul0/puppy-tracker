from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_APP_PATH = REPO_ROOT / "test_app" / "app.py"


@pytest.fixture
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "puppy_tracker_test.db"
    monkeypatch.setenv("PUPPY_TRACKER_DB", str(db_path))
    module_name = f"test_app_under_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, TEST_APP_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load test_app/app.py for tests")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    module.init_db()
    try:
        yield module
    finally:
        sys.modules.pop(module_name, None)


@pytest.fixture
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client
