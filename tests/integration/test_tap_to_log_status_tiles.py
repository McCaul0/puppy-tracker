from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PUPPY_TRACKER_DB", str(tmp_path / "tap_to_log_test.db"))
    monkeypatch.setenv("PUPPY_TRACKER_PORT", "8765")
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    sys.modules.pop("app", None)
    app_module = importlib.import_module("app")
    with TestClient(app_module.app) as test_client:
        yield test_client
    sys.modules.pop("app", None)


def test_dashboard_marks_supported_tiles_as_tappable(client: TestClient) -> None:
    response = client.get("/api/state")
    assert response.status_code == 200
    snapshot = response.json()

    tiles = snapshot["live_state"]["tiles"]
    assert tiles["pee"]["is_tappable"] is True
    assert tiles["pee"]["tap_activity"] == "pee"
    assert tiles["pee"]["tap_hint"] == "Tap to log"
    assert tiles["awake"]["is_tappable"] is False
    assert tiles["awake"]["tap_activity"] is None
    assert tiles["awake"]["readonly_reason"] == "Derived state"
    assert snapshot["live_state"]["secondary_quick_actions"] == [
        {"activity": "play", "label": "Play"},
        {"activity": "sleep", "label": "Sleep"},
        {"activity": "wake", "label": "Wake"},
    ]


def test_supported_tile_activity_uses_existing_event_pipeline(client: TestClient) -> None:
    response = client.post(
        "/api/events",
        json={
            "activity": "pee",
            "actor": "McCaul",
        },
    )
    assert response.status_code == 200
    snapshot = response.json()

    assert snapshot["events"][0]["activity"] == "pee"
    assert snapshot["events"][0]["actor"] == "McCaul"
    assert snapshot["live_state"]["since_pee_minutes"] == 0
    assert snapshot["live_state"]["tiles"]["pee"]["display_value"] == "just now"
    assert snapshot["live_state"]["tiles"]["pee"]["is_tappable"] is True
