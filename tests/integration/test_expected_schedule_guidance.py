from __future__ import annotations

from datetime import timedelta


def test_sleep_logging_stays_start_only_and_projects_guidance(client, app_module):
    now = app_module.utc_now()
    settings_response = client.post(
        "/api/settings",
        json={
            "puppy_name": "Puppy",
            "household_name": "Home",
            "timezone_offset_minutes": -240,
            "activities": ["pee", "poop", "food", "water", "sleep", "wake", "play"],
            "household_members": ["McCaul"],
            "puppy_birth_date": (now.date() - timedelta(weeks=14)).isoformat(),
        },
    )
    assert settings_response.status_code == 200

    response = client.post(
        "/api/events",
        json={
            "activity": "sleep",
            "actor": "McCaul",
            "event_time_utc": now.isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["events"][0]["activity"] == "sleep"
    assert payload["events"][0]["duration_minutes"] is None
    assert payload["live_state"]["primary_advisory"]["title"] == "Sleeping now"
    assert payload["live_state"]["sleep_projection"]["recommended_check_reason"]
    assert payload["live_state"]["schedule"]["routine_summary"]


def test_post_food_guidance_is_explained_in_state_payload(client, app_module):
    now = app_module.utc_now()
    client.post(
        "/api/settings",
        json={
            "puppy_name": "Puppy",
            "household_name": "Home",
            "timezone_offset_minutes": -240,
            "activities": ["pee", "poop", "food", "water", "sleep", "wake", "play"],
            "household_members": ["McCaul"],
            "puppy_birth_date": (now.date() - timedelta(weeks=14)).isoformat(),
        },
    )
    client.post(
        "/api/events",
        json={
            "activity": "food",
            "actor": "McCaul",
            "event_time_utc": (now - timedelta(minutes=15)).isoformat(),
        },
    )

    response = client.get("/api/state")

    assert response.status_code == 200
    payload = response.json()
    advisory = payload["live_state"]["primary_advisory"]

    assert advisory["advisory_key"] == "post-food-potty"
    assert advisory["rule_type"] == "behavior-trigger"
    assert advisory["triggered_by"]


def test_recent_potty_clears_stale_post_food_banner(client, app_module):
    now = app_module.utc_now()
    client.post(
        "/api/settings",
        json={
            "puppy_name": "Puppy",
            "household_name": "Home",
            "timezone_offset_minutes": -240,
            "activities": ["pee", "poop", "food", "water", "sleep", "wake", "play"],
            "household_members": ["McCaul"],
            "puppy_birth_date": (now.date() - timedelta(weeks=20)).isoformat(),
        },
    )
    client.post(
        "/api/events",
        json={
            "activity": "food",
            "actor": "McCaul",
            "event_time_utc": (now - timedelta(hours=6)).isoformat(),
        },
    )
    client.post(
        "/api/events",
        json={
            "activity": "pee",
            "actor": "McCaul",
            "event_time_utc": (now - timedelta(minutes=2)).isoformat(),
        },
    )

    response = client.get("/api/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["live_state"]["primary_advisory"]["advisory_key"] != "post-food-potty"

    post_food_row = next(row for row in payload["live_state"]["logic_breakdown"] if row["key"] == "post-food-potty")
    assert post_food_row["status"] == "cleared"
    assert "Cleared by pee" in post_food_row["detail"]
