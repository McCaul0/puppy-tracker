from __future__ import annotations

import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


FIXED_NOW = datetime(2026, 4, 14, 16, 15, tzinfo=timezone.utc)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    repo_root = Path(__file__).resolve().parents[2]
    tmp_dir = repo_root / "tests" / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_dir / f"main_page_behavior_{uuid4().hex}.db"
    monkeypatch.setenv("PUPPY_TRACKER_DB", str(db_path))
    monkeypatch.setenv("PUPPY_TRACKER_PORT", "8767")
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


def save_settings(client: TestClient, birth_date: str = "") -> dict:
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


def save_custom_routine_profile(client: TestClient, *, sleep_default: int) -> dict:
    response = client.put(
        "/api/routine-profile",
        json={
            "base_age_band_id": "12_to_16_weeks",
            "save_mode": "advanced",
            "custom_values": {
                "pee_due": 120,
                "pee_overdue": 180,
                "poop_due": 300,
                "poop_overdue": 420,
                "food_due": 360,
                "food_overdue": 480,
                "water_due": 180,
                "water_overdue": 240,
                "awake_due": 90,
                "awake_overdue": 120,
                "sleep_default": sleep_default,
                "post_food_potty_due": 15,
                "post_food_potty_overdue": 30,
            },
        },
    )
    assert response.status_code == 200
    return response.json()


def log_event(
    client: TestClient,
    activity: str,
    *,
    when: str,
    actor: str = "McCaul",
    is_accident: bool = False,
    note: str = "",
) -> dict:
    response = client.post(
        "/api/events",
        json={
            "activity": activity,
            "actor": actor,
            "event_time_utc": when,
            "is_accident": is_accident,
            "note": note,
        },
    )
    assert response.status_code == 200
    return response.json()


def update_event(
    client: TestClient,
    event_id: int,
    *,
    activity: str,
    when: str,
    actor: str = "McCaul",
    is_accident: bool = False,
    note: str = "",
) -> dict:
    response = client.put(
        f"/api/events/{event_id}",
        json={
            "activity": activity,
            "actor": actor,
            "event_time_utc": when,
            "duration_minutes": 20 if activity == "play" else None,
            "is_accident": is_accident,
            "note": note,
        },
    )
    assert response.status_code == 200
    return response.json()


def delete_event(client: TestClient, event_id: int) -> dict:
    response = client.delete(f"/api/events/{event_id}")
    assert response.status_code == 200
    return response.json()


def primary_title(snapshot: dict) -> str:
    return snapshot["live_state"]["primary_advisory"]["title"]


def test_dashboard_defaults_to_all_good_and_no_data_when_no_events_exist(client: TestClient) -> None:
    save_settings(client)

    snapshot = client.get("/api/state").json()
    tiles = snapshot["live_state"]["tiles"]

    assert primary_title(snapshot) == "All good for now"
    assert snapshot["live_state"]["primary_advisory"]["reason"] == "Nothing looks urgent right now."
    assert tiles["pee"]["display_value"] == "No entries yet"
    assert tiles["pee"]["urgency"] == "unknown"
    assert tiles["pee"]["urgency_label"] == "No data"
    assert tiles["awake"]["label"] == "Awake"
    assert tiles["awake"]["display_value"] == "No entries yet"
    assert tiles["awake"]["urgency"] == "unknown"
    assert tiles["awake"]["urgency_label"] == "No data"
    assert tiles["awake"]["detail_text"] is None


def test_pee_due_soon_drives_banner_when_awake_is_still_on_track(client: TestClient) -> None:
    save_settings(client)
    log_event(client, "pee", when="2026-04-14T14:15:00Z")
    snapshot = log_event(client, "wake", when="2026-04-14T15:45:00Z")

    pee_tile = snapshot["live_state"]["tiles"]["pee"]

    assert primary_title(snapshot) == "Potty soon"
    assert pee_tile["display_value"] == "2h ago"
    assert pee_tile["urgency"] == "soon"
    assert pee_tile["urgency_label"] == "Due soon"


def test_pee_overdue_beats_sleep_overdue_in_banner_priority(client: TestClient) -> None:
    save_settings(client)
    log_event(client, "wake", when="2026-04-14T12:00:00Z")
    snapshot = log_event(client, "pee", when="2026-04-14T13:00:00Z")

    assert snapshot["live_state"]["since_awake_minutes"] == 195
    assert snapshot["live_state"]["since_pee_minutes"] == 195
    assert primary_title(snapshot) == "Pee break overdue"
    assert snapshot["live_state"]["primary_advisory"]["reason"] == "Last pee was 3h 15m ago."


def test_sleep_block_ends_at_later_non_sleep_activity_before_planned_end(client: TestClient) -> None:
    save_settings(client)
    save_custom_routine_profile(client, sleep_default=180)
    log_event(client, "sleep", when="2026-04-14T13:15:00Z")
    snapshot = log_event(client, "pee", when="2026-04-14T15:30:00Z")

    sleep_block = snapshot["live_state"]["sleep_block"]
    awake_tile = snapshot["live_state"]["tiles"]["awake"]
    pee_tile = snapshot["live_state"]["tiles"]["pee"]

    assert sleep_block["end_source"] == "activity"
    assert sleep_block["end_time_utc"] == "2026-04-14T15:30:00+00:00"
    assert awake_tile["label"] == "Awake"
    assert awake_tile["display_value"] == "45m ago"
    assert awake_tile["detail_text"] == "Since 11:30 AM"
    assert pee_tile["display_value"] == "45m ago"
    assert primary_title(snapshot) == "All good for now"


def test_sleep_block_ends_at_explicit_wake_event(client: TestClient) -> None:
    save_settings(client)
    log_event(client, "sleep", when="2026-04-14T13:15:00Z")
    snapshot = log_event(client, "wake", when="2026-04-14T15:30:00Z")

    sleep_block = snapshot["live_state"]["sleep_block"]
    awake_tile = snapshot["live_state"]["tiles"]["awake"]

    assert sleep_block["end_source"] == "wake"
    assert sleep_block["end_time_utc"] == "2026-04-14T15:30:00+00:00"
    assert awake_tile["label"] == "Awake"
    assert awake_tile["display_value"] == "45m ago"
    assert awake_tile["detail_text"] == "Since 11:30 AM"


def test_sleep_block_stays_open_past_target_until_a_recorded_end_exists(client: TestClient) -> None:
    save_settings(client)
    snapshot = log_event(client, "sleep", when="2026-04-14T13:15:00Z")

    sleep_block = snapshot["live_state"]["sleep_block"]
    awake_tile = snapshot["live_state"]["tiles"]["awake"]
    current_block = snapshot["live_state"]["routine_overview"]["current_block"]

    assert sleep_block["end_source"] == "open"
    assert sleep_block["end_time_utc"] is None
    assert sleep_block["is_sleeping_now"] is True
    assert awake_tile["label"] == "Asleep"
    assert awake_tile["display_value"] == "3h ago"
    assert awake_tile["detail_text"] == "Since 9:15 AM"
    assert current_block["time_label"] == "Nap target around 11:15 AM"
    assert current_block["explanation"] == "This target only guides recommendations. Sleep stays active until wake or another activity is logged."


def test_later_non_sleep_activity_after_target_still_ends_sleep_at_recorded_time(client: TestClient) -> None:
    save_settings(client)
    log_event(client, "sleep", when="2026-04-14T13:15:00Z")
    snapshot = log_event(client, "pee", when="2026-04-14T15:30:00Z")

    sleep_block = snapshot["live_state"]["sleep_block"]
    awake_tile = snapshot["live_state"]["tiles"]["awake"]

    assert sleep_block["end_source"] == "activity"
    assert sleep_block["end_time_utc"] == "2026-04-14T15:30:00+00:00"
    assert awake_tile["label"] == "Awake"
    assert awake_tile["display_value"] == "45m ago"
    assert awake_tile["detail_text"] == "Since 11:30 AM"


def test_editing_later_activity_changes_awake_anchor(client: TestClient) -> None:
    save_settings(client)
    save_custom_routine_profile(client, sleep_default=180)
    log_event(client, "sleep", when="2026-04-14T13:15:00Z")
    created = log_event(client, "pee", when="2026-04-14T15:30:00Z")
    pee_event_id = created["events"][0]["id"]

    snapshot = update_event(client, pee_event_id, activity="pee", when="2026-04-14T14:45:00Z")
    sleep_block = snapshot["live_state"]["sleep_block"]
    awake_tile = snapshot["live_state"]["tiles"]["awake"]
    pee_tile = snapshot["live_state"]["tiles"]["pee"]

    assert sleep_block["end_source"] == "activity"
    assert sleep_block["end_time_utc"] == "2026-04-14T14:45:00+00:00"
    assert awake_tile["display_value"] == "1h 30m ago"
    assert awake_tile["detail_text"] == "Since 10:45 AM"
    assert pee_tile["display_value"] == "1h 30m ago"


def test_deleting_latest_pee_falls_back_to_previous_anchor(client: TestClient) -> None:
    save_settings(client)
    log_event(client, "pee", when="2026-04-14T13:00:00Z")
    created = log_event(client, "pee", when="2026-04-14T15:30:00Z")
    latest_pee_id = created["events"][0]["id"]

    snapshot = delete_event(client, latest_pee_id)
    pee_tile = snapshot["live_state"]["tiles"]["pee"]

    assert pee_tile["display_value"] == "3h 15m ago"
    assert pee_tile["urgency"] == "overdue"
    assert primary_title(snapshot) == "Pee break overdue"


def test_deleting_post_food_clearing_potty_restores_post_food_banner(client: TestClient) -> None:
    save_settings(client)
    log_event(client, "food", when="2026-04-14T15:45:00Z")
    created = log_event(client, "pee", when="2026-04-14T16:00:00Z")
    pee_event_id = created["events"][0]["id"]

    snapshot = delete_event(client, pee_event_id)

    assert primary_title(snapshot) == "Potty likely overdue"
    assert snapshot["live_state"]["primary_advisory"]["reason"] == "Ate 30m ago."


def test_editing_activity_from_pee_to_water_clears_accident_and_moves_anchor(client: TestClient) -> None:
    save_settings(client)
    created = log_event(client, "pee", when="2026-04-14T15:30:00Z", is_accident=True)
    pee_event_id = created["events"][0]["id"]

    snapshot = update_event(client, pee_event_id, activity="water", when="2026-04-14T15:30:00Z")
    event = snapshot["events"][0]
    tiles = snapshot["live_state"]["tiles"]

    assert event["activity"] == "water"
    assert event["is_accident"] == 0
    assert tiles["water"]["display_value"] == "45m ago"
    assert tiles["pee"]["display_value"] == "No entries yet"
    assert tiles["pee"]["urgency_label"] == "No data"
