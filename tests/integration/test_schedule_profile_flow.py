from __future__ import annotations

from datetime import timedelta


def test_schedule_edit_recalculates_guidance(client, app_module):
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

    update_response = client.put(
        "/api/schedule-profile",
        json={
            "source": "custom",
            "routine_blocks": [
                {
                    "id": "custom-play",
                    "kind": "play",
                    "label": "Backyard play",
                    "start_local_time": "15:30",
                    "duration_minutes": 25,
                    "days_of_week": app_module.WEEKDAY_IDS,
                    "enabled": True,
                    "source": "custom",
                }
            ],
            "trigger_rules": [
                {
                    "rule_key": "post_food_potty",
                    "enabled": True,
                    "due_minutes": 5,
                    "overdue_minutes": 10,
                    "notes": "Custom food trigger",
                    "source": "custom",
                }
            ],
            "care_limits": [
                {
                    "need": "potty",
                    "context": "overnight",
                    "limit_minutes": 240,
                    "source": "custom",
                    "emphasis": "high",
                }
            ],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["snapshot"]["live_state"]["schedule"]["post_food_potty_due"] == 5

    client.post(
        "/api/events",
        json={
            "activity": "food",
            "actor": "McCaul",
            "event_time_utc": (now - timedelta(minutes=6)).isoformat(),
        },
    )

    state_response = client.get("/api/state")
    profile_response = client.get("/api/schedule-profile")

    assert state_response.status_code == 200
    assert profile_response.status_code == 200
    state_payload = state_response.json()
    profile_payload = profile_response.json()

    assert state_payload["live_state"]["primary_advisory"]["advisory_key"] == "post-food-potty"
    assert state_payload["live_state"]["schedule_profile_summary"]["source"] == "custom"
    assert profile_payload["routine_blocks"][0]["id"] == "custom-play"
