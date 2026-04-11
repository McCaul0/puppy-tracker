from __future__ import annotations

from datetime import timedelta


def test_get_schedule_profile_exposes_defaults(client, app_module):
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

    response = client.get("/api/schedule-profile")

    assert response.status_code == 200
    payload = response.json()
    assert {"profile_version", "source", "active_age_band", "routine_blocks", "care_limits", "trigger_rules"} <= set(payload)
    assert payload["routine_blocks"]
    assert payload["trigger_rules"][0]["source"] == "default-age-band"
    assert payload["care_limits"][0]["source"] == "default-age-band"


def test_put_schedule_profile_returns_profile_and_snapshot(client, app_module):
    now = app_module.utc_now()
    payload = {
        "source": "custom",
        "routine_blocks": [
            {
                "id": "custom-nap",
                "kind": "sleep",
                "label": "Custom nap",
                "start_local_time": "10:30",
                "duration_minutes": 90,
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
    }

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
    response = client.put("/api/schedule-profile", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert {"schedule_profile", "snapshot"} <= set(body)
    assert body["schedule_profile"]["routine_blocks"][0]["id"] == "custom-nap"
    assert body["snapshot"]["live_state"]["schedule"]["post_food_potty_due"] == 5
