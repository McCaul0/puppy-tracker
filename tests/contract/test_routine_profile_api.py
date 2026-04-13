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
    db_path = tmp_dir / f"routine_profile_contract_{uuid4().hex}.db"
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


def save_custom_profile(client: TestClient) -> dict:
    response = client.put(
        "/api/routine-profile",
        json={
            "base_age_band_id": "10_to_12_weeks",
            "save_mode": "simple",
            "custom_values": {
                "pee_due": 70,
                "pee_overdue": 100,
                "poop_due": 250,
                "poop_overdue": 320,
                "food_due": 330,
                "food_overdue": 390,
                "water_due": 130,
                "water_overdue": 190,
                "awake_due": 55,
                "awake_overdue": 70,
                "sleep_default": 110,
                "post_food_potty_due": 12,
                "post_food_potty_overdue": 24,
            },
        },
    )
    assert response.status_code == 200
    return response.json()


def test_state_includes_routine_overview_and_editor(client: TestClient) -> None:
    snapshot = save_birth_date(client, "2026-01-31")

    schedule = snapshot["live_state"]["schedule"]
    assert schedule["routine_mode"] == "default_auto"
    assert schedule["profile_source"] == "default_current_age"
    assert schedule["recommended_age_band_id"] == "10_to_12_weeks"

    overview = snapshot["live_state"]["routine_overview"]
    assert overview["headline"] == "Today's rhythm"
    assert overview["current_block"]["phase"] == "now"
    assert overview["next_block"]["phase"] == "next"

    editor = snapshot["live_state"]["routine_editor"]
    assert editor["routine_mode"] == "default_auto"
    assert any(field["id"] == "potty_rhythm" for field in editor["simple_fields"])
    assert any(field["id"] == "pee_due" for field in editor["advanced_fields"])


def test_custom_routine_save_returns_custom_manual_state(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    snapshot = save_custom_profile(client)

    schedule = snapshot["live_state"]["schedule"]
    assert schedule["routine_mode"] == "custom_manual"
    assert schedule["profile_source"] == "custom_saved"
    assert schedule["effective_age_band_id"] == "10_to_12_weeks"
    assert schedule["pee_due"] == 70
    assert snapshot["live_state"]["routine_proposal"] is None


def test_age_transition_creates_pending_proposal_for_custom_routine(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    save_custom_profile(client)
    snapshot = save_birth_date(client, "2025-12-01")

    schedule = snapshot["live_state"]["schedule"]
    assert schedule["routine_mode"] == "custom_manual"
    assert schedule["effective_age_band_id"] == "10_to_12_weeks"
    assert schedule["recommended_age_band_id"] == "4_to_6_months"

    proposal = snapshot["live_state"]["routine_proposal"]
    assert proposal["status"] == "pending"
    assert proposal["current_custom_age_band_id"] == "10_to_12_weeks"
    assert proposal["recommended_age_band_id"] == "4_to_6_months"
    assert proposal["diff_items"]


def test_rejecting_pending_proposal_preserves_custom_routine(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    save_custom_profile(client)
    snapshot = save_birth_date(client, "2025-12-01")
    proposal_id = snapshot["live_state"]["routine_proposal"]["proposal_id"]

    decision = client.post(
        f"/api/routine-proposal/{proposal_id}/decision",
        json={"action": "reject"},
    )
    assert decision.status_code == 200
    decided_snapshot = decision.json()

    schedule = decided_snapshot["live_state"]["schedule"]
    assert schedule["routine_mode"] == "custom_manual"
    assert schedule["effective_age_band_id"] == "10_to_12_weeks"
    assert schedule["pee_due"] == 70
    assert decided_snapshot["live_state"]["routine_proposal"] is None
    assert decided_snapshot["live_state"]["routine_overview"]["source_state"]["proposal_status"] == "rejected"


def test_accepting_pending_proposal_updates_to_current_recommendation(client: TestClient) -> None:
    save_birth_date(client, "2026-01-31")
    save_custom_profile(client)
    snapshot = save_birth_date(client, "2025-12-01")
    proposal_id = snapshot["live_state"]["routine_proposal"]["proposal_id"]

    decision = client.post(
        f"/api/routine-proposal/{proposal_id}/decision",
        json={"action": "accept"},
    )
    assert decision.status_code == 200
    decided_snapshot = decision.json()

    schedule = decided_snapshot["live_state"]["schedule"]
    assert schedule["routine_mode"] == "default_auto"
    assert schedule["profile_source"] == "default_current_age"
    assert schedule["effective_age_band_id"] == "4_to_6_months"
    assert schedule["pee_due"] == schedule["defaults"]["pee_due"]
    assert decided_snapshot["live_state"]["routine_proposal"] is None
