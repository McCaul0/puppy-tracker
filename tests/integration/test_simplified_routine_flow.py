from __future__ import annotations

import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


FIXED_NOW = datetime(2026, 4, 11, 15, 0, tzinfo=timezone.utc)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    repo_root = Path(__file__).resolve().parents[2]
    tmp_dir = repo_root / "tests" / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_dir / f"routine_profile_integration_{uuid4().hex}.db"
    monkeypatch.setenv("PUPPY_TRACKER_DB", str(db_path))
    monkeypatch.setenv("PUPPY_TRACKER_PORT", "8766")
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


def save_birth_date(client: TestClient, birth_date: str) -> dict:
    response = client.post(
        "/api/settings",
        json={
            "puppy_name": "Puppy",
            "household_name": "Home",
            "timezone_offset_minutes": -240,
            "activities": ["pee", "poop", "food", "water", "sleep", "wake", "play"],
            "household_members": ["McCaul", "Jess"],
            "puppy_birth_date": birth_date,
        },
    )
    assert response.status_code == 200
    return response.json()


def log_event(client: TestClient, activity: str, *, actor: str = "McCaul", when: str | None = None) -> dict:
    response = client.post(
        "/api/events",
        json={
            "activity": activity,
            "actor": actor,
            "event_time_utc": when,
        },
    )
    assert response.status_code == 200
    return response.json()


def save_custom_profile(client: TestClient) -> dict:
    response = client.put(
        "/api/routine-profile",
        json={
            "base_age_band_id": "10_to_12_weeks",
            "save_mode": "advanced",
            "custom_values": {
                "pee_due": 75,
                "pee_overdue": 105,
                "poop_due": 255,
                "poop_overdue": 330,
                "food_due": 345,
                "food_overdue": 405,
                "water_due": 135,
                "water_overdue": 195,
                "awake_due": 58,
                "awake_overdue": 72,
                "sleep_default": 115,
                "post_food_potty_due": 13,
                "post_food_potty_overdue": 26,
            },
        },
    )
    assert response.status_code == 200
    return response.json()


def test_default_routine_overview_tracks_age_band_and_recent_events(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    snapshot = log_event(client, "pee", when="2026-04-11T14:30:00Z")

    overview = snapshot["live_state"]["routine_overview"]
    assert overview["source_state"]["routine_mode"] == "default_auto"
    assert overview["next_block"]["kind"] in {"potty", "food", "sleep", "water"}
    assert overview["agenda"]


def test_custom_routine_stays_in_place_until_user_accepts_new_age_proposal(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    save_custom_profile(client)
    aged_snapshot = save_birth_date(client, "2025-12-01")

    assert aged_snapshot["live_state"]["schedule"]["routine_mode"] == "custom_manual"
    assert aged_snapshot["live_state"]["schedule"]["effective_age_band_id"] == "10_to_12_weeks"
    proposal_id = aged_snapshot["live_state"]["routine_proposal"]["proposal_id"]

    rejected = client.post(
        f"/api/routine-proposal/{proposal_id}/decision",
        json={"action": "reject"},
    )
    assert rejected.status_code == 200
    rejected_snapshot = rejected.json()
    assert rejected_snapshot["live_state"]["schedule"]["routine_mode"] == "custom_manual"
    assert rejected_snapshot["live_state"]["schedule"]["effective_age_band_id"] == "10_to_12_weeks"

    refreshed = client.get("/api/state")
    assert refreshed.status_code == 200
    refreshed_snapshot = refreshed.json()
    assert refreshed_snapshot["live_state"]["routine_proposal"] is None


def test_accepting_proposal_returns_to_auto_following_current_age_band(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    save_custom_profile(client)
    aged_snapshot = save_birth_date(client, "2025-12-01")
    proposal_id = aged_snapshot["live_state"]["routine_proposal"]["proposal_id"]

    accepted = client.post(
        f"/api/routine-proposal/{proposal_id}/decision",
        json={"action": "accept"},
    )
    assert accepted.status_code == 200
    accepted_snapshot = accepted.json()

    overview = accepted_snapshot["live_state"]["routine_overview"]
    assert accepted_snapshot["live_state"]["schedule"]["routine_mode"] == "default_auto"
    assert accepted_snapshot["live_state"]["schedule"]["effective_age_band_id"] == "4_to_6_months"
    assert overview["source_state"]["proposal_status"] == "accepted"
