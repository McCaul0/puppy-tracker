from __future__ import annotations

import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


FIXED_NOW = datetime(2026, 4, 14, 10, 0, tzinfo=timezone.utc)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    repo_root = Path(__file__).resolve().parents[2]
    tmp_dir = repo_root / "tests" / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_dir / f"tap_to_log_{uuid4().hex}.db"
    monkeypatch.setenv("PUPPY_TRACKER_DB", str(db_path))
    monkeypatch.setenv("PUPPY_TRACKER_PORT", "8765")
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    sys.modules.pop("app", None)
    app_module = importlib.import_module("app")
    monkeypatch.setattr(app_module, "utc_now", lambda: FIXED_NOW)
    with TestClient(app_module.app) as test_client:
        yield test_client
    if db_path.exists():
        db_path.unlink()
    sys.modules.pop("app", None)


def test_dashboard_uses_awake_tile_as_sleep_wake_toggle(client: TestClient) -> None:
    response = client.get("/api/state")
    assert response.status_code == 200
    snapshot = response.json()

    tiles = snapshot["live_state"]["tiles"]
    assert tiles["pee"]["is_tappable"] is True
    assert tiles["pee"]["tap_activity"] == "pee"
    assert tiles["pee"]["tap_hint"] == "Tap to log"
    assert tiles["awake"]["is_tappable"] is True
    assert tiles["awake"]["tap_activity"] == "sleep"
    assert tiles["awake"]["tap_hint"] == "Tap to log"
    assert tiles["awake"]["label"] == "Awake"
    assert tiles["awake"]["show_urgency"] is False
    assert snapshot["live_state"]["secondary_quick_actions"] == []


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


def test_awake_tile_switches_to_wake_when_sleep_is_active(client: TestClient) -> None:
    response = client.post(
        "/api/events",
        json={
            "activity": "sleep",
            "actor": "McCaul",
            "event_time_utc": "2026-04-14T09:00:00Z",
        },
    )
    assert response.status_code == 200
    snapshot = response.json()

    awake_tile = snapshot["live_state"]["tiles"]["awake"]
    assert awake_tile["label"] == "Asleep"
    assert awake_tile["display_value"] == "1h ago"
    assert awake_tile["detail_text"] == "Since 5:00 AM"
    assert awake_tile["urgency_label"] == "On track"
    assert awake_tile["tap_activity"] == "wake"
    assert awake_tile["tap_hint"] == "Tap to log"
    assert awake_tile["show_urgency"] is False
