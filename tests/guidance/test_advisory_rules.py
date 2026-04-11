from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_age_band_selection_tracks_birth_date(app_module):
    now = app_module.utc_now()
    settings = {
        "puppy_birth_date": (now.date() - timedelta(weeks=20)).isoformat(),
        "timezone_offset_minutes": -240,
        "schedule_profile": {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []},
    }

    age_band = app_module.resolve_age_band(settings, now)

    assert age_band["id"] == "4_to_6_months"
    assert age_band["label"] == "4-6 months"


def test_four_to_six_month_band_waits_for_four_calendar_months(app_module):
    settings = {
        "puppy_birth_date": "2025-12-17",
        "timezone_offset_minutes": -240,
        "schedule_profile": {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []},
    }

    before_boundary = app_module.resolve_age_band(settings, datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc))
    at_boundary = app_module.resolve_age_band(settings, datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc))

    assert before_boundary["id"] == "12_to_16_weeks"
    assert before_boundary["overnight_potty_limit_minutes"] == 240
    assert at_boundary["id"] == "4_to_6_months"
    assert at_boundary["overnight_potty_limit_minutes"] == 300


def test_post_food_trigger_beats_generic_sleep_soon(app_module):
    now = app_module.utc_now()
    settings = {
        "puppy_birth_date": (now.date() - timedelta(weeks=14)).isoformat(),
        "timezone_offset_minutes": -240,
        "schedule_profile": {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []},
        "advisory_overrides": [],
    }
    schedule = app_module.get_schedule(settings, now)
    events_desc = [
        {
            "activity": "food",
            "event_time_utc": (now - timedelta(minutes=schedule["post_food_potty_due"] + 2)).isoformat(),
        },
        {
            "activity": "wake",
            "event_time_utc": (now - timedelta(minutes=schedule["awake_due"] - 5)).isoformat(),
        },
    ]
    live = {
        "since_awake_minutes": schedule["awake_due"] - 5,
        "since_pee_minutes": 20,
        "since_poop_minutes": 60,
        "since_food_minutes": schedule["post_food_potty_due"] + 2,
        "since_water_minutes": 10,
        "since_wake_minutes": None,
        "since_play_minutes": None,
        "sleep_block": None,
    }

    advisories = app_module.build_advisory_candidates(events_desc, settings, schedule, live, now)
    advisories.sort(key=lambda item: item["priority"])

    assert advisories[0]["advisory_key"] == "post-food-potty"
    assert advisories[0]["rule_type"] == "behavior-trigger"
    assert "Ate" in advisories[0]["reason"]


def test_post_food_trigger_clears_after_potty_is_logged(app_module):
    now = app_module.utc_now()
    settings = {
        "puppy_birth_date": (now.date() - timedelta(weeks=20)).isoformat(),
        "timezone_offset_minutes": -240,
        "schedule_profile": {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []},
        "advisory_overrides": [],
    }
    schedule = app_module.get_schedule(settings, now)
    food_minutes = schedule["post_food_potty_overdue"] + 45
    events_desc = [
        {
            "activity": "pee",
            "event_time_utc": (now - timedelta(minutes=2)).isoformat(),
        },
        {
            "activity": "food",
            "event_time_utc": (now - timedelta(minutes=food_minutes)).isoformat(),
        },
    ]
    live = {
        "since_awake_minutes": 2,
        "since_pee_minutes": 2,
        "since_poop_minutes": 90,
        "since_food_minutes": food_minutes,
        "since_water_minutes": 60,
        "since_wake_minutes": None,
        "since_play_minutes": None,
        "sleep_block": None,
    }

    advisories = app_module.build_advisory_candidates(events_desc, settings, schedule, live, now)

    assert all(item["advisory_key"] != "post-food-potty" for item in advisories)

    primary = advisories[0]
    logic_rows = app_module.build_logic_breakdown(events_desc, schedule, live, now, primary)
    post_food_row = next(row for row in logic_rows if row["key"] == "post-food-potty")

    assert post_food_row["status"] == "cleared"
    assert "Cleared by pee" in post_food_row["detail"]


def test_human_minutes_short_rolls_past_sixty_minutes(app_module):
    assert app_module.human_minutes_short(125) == "2h 5m"
    assert app_module.human_minutes_short(60) == "1h"


def test_routine_summary_humanizes_long_durations(app_module):
    now = app_module.utc_now()
    settings = {
        "puppy_birth_date": (now.date() - timedelta(weeks=20)).isoformat(),
        "timezone_offset_minutes": -240,
        "schedule_profile": {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []},
    }

    schedule = app_module.get_schedule(settings, now)
    cards = {card["title"]: card for card in app_module.routine_summary_cards(schedule)}

    assert cards["Overnight limit"]["primary"] == "Potty check by 5h overnight"
    assert cards["Overnight limit"]["secondary"] == "Default overnight block 5h"
    assert cards["Food and water"]["primary"] == "Food 8h / Water 4h"
    assert cards["Food and water"]["secondary"] == "Water overdue at 5h"
