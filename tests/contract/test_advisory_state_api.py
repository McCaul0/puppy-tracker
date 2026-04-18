from __future__ import annotations

from datetime import timedelta


def assert_no_cache_headers(response) -> None:
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"


def test_state_payload_exposes_advisory_fields(client):
    response = client.get("/api/state")

    assert response.status_code == 200
    assert_no_cache_headers(response)
    payload = response.json()
    live_state = payload["live_state"]

    assert {"primary_advisory", "active_advisories", "logic_breakdown", "schedule", "sleep_projection", "schedule_profile_summary"} <= set(live_state)
    assert {"advisory_key", "title", "reason", "rule_type", "status", "priority", "triggered_by"} <= set(
        live_state["primary_advisory"]
    )
    assert isinstance(live_state["active_advisories"], list)
    assert isinstance(live_state["logic_breakdown"], list)
    assert isinstance(live_state["schedule"]["routine_summary"], list)
    assert {"recommended_check_at_utc", "recommended_check_reason", "care_limit_warning"} <= set(
        live_state["sleep_projection"]
    )


def test_state_payload_humanizes_long_duration_summaries(client, app_module):
    now = app_module.utc_now()
    settings_response = client.post(
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
    assert settings_response.status_code == 200

    response = client.get("/api/state")

    assert response.status_code == 200
    routine_summary = {card["title"]: card for card in response.json()["live_state"]["schedule"]["routine_summary"]}

    assert routine_summary["Overnight limit"]["primary"] == "Potty check by 5h overnight"
    assert routine_summary["Overnight limit"]["secondary"] == "Default overnight block 5h"
    assert routine_summary["Food and water"]["primary"] == "Food 8h / Water 4h"
    assert routine_summary["Food and water"]["secondary"] == "Water overdue at 5h"


def test_settings_normalization_removes_nap_from_supported_activities(client):
    response = client.post(
        "/api/settings",
        json={
            "puppy_name": "Puppy",
            "household_name": "Home",
            "timezone_offset_minutes": -240,
            "activities": ["pee", "poop", "food", "water", "sleep", "wake", "play", "nap"],
            "household_members": ["McCaul"],
            "puppy_birth_date": "",
        },
    )

    assert response.status_code == 200
    assert_no_cache_headers(response)
    activities = response.json()["settings"]["activities"]

    assert "nap" not in activities
    assert activities == ["pee", "poop", "food", "water", "sleep", "wake", "play"]


def test_index_includes_mobile_safe_datetime_input_styles(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert "input, select, textarea{width:100%;max-width:100%;min-width:0;box-sizing:border-box;" in html
    assert ".datetime-pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,8.25rem);gap:8px;align-items:end;overflow:hidden}" in html
    assert ".datetime-pair > *{min-width:0;max-width:100%;justify-self:stretch}" in html
    assert ".datetime-pair input{min-width:0;max-width:100%;overflow:hidden}" in html
    assert (
        'input[type="date"],input[type="time"],input[type="datetime-local"]'
        "{display:block;width:100%;inline-size:100%;max-width:100%;min-width:0;box-sizing:border-box;background-clip:padding-box;"
        "-webkit-appearance:none;appearance:none;line-height:1.2}"
    ) in html
    assert (
        'input[type="date"]::-webkit-date-and-time-value,input[type="time"]::-webkit-date-and-time-value,input[type="datetime-local"]::-webkit-date-and-time-value{min-width:0;text-align:left}'
    ) in html


def test_index_includes_routine_proposal_modal_and_refresh_hooks(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert 'id="routine-proposal-modal"' in html
    assert "Accept schedule changes" in html
    assert "Keep current schedule" in html
    assert "window.addEventListener('pageshow'" in html
    assert "document.addEventListener('visibilitychange'" in html
    assert "cache: 'no-store'" in html


def test_index_includes_humanized_minutes_hints_for_schedule_editor(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert "function editorMinutesHint(minutes)" in html
    assert "bindMinutesHint(inputId, hintId)" in html
    assert 'id="block-duration-hint-${index}"' in html
    assert 'id="rule-due-hint-${index}"' in html
    assert 'id="rule-overdue-hint-${index}"' in html
    assert 'id="limit-minutes-hint-${index}"' in html
