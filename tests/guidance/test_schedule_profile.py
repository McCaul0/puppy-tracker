from __future__ import annotations

from datetime import timedelta


def test_sort_routine_blocks_orders_by_start_time(app_module):
    blocks = [
        {"id": "late", "kind": "sleep", "label": "Late", "start_local_time": "15:00"},
        {"id": "early", "kind": "feeding", "label": "Early", "start_local_time": "08:00"},
        {"id": "mid", "kind": "play", "label": "Mid", "start_local_time": "12:00"},
    ]

    ordered = app_module.sort_routine_blocks(blocks)

    assert [block["id"] for block in ordered] == ["early", "mid", "late"]


def test_merge_schedule_profile_applies_custom_thresholds(app_module):
    now = app_module.utc_now()
    settings = {
        "puppy_birth_date": (now.date() - timedelta(weeks=14)).isoformat(),
        "timezone_offset_minutes": -240,
        "schedule_profile": {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []},
    }
    base_schedule = app_module.get_schedule(settings, now)
    profile = {
        "source": "custom",
        "routine_blocks": [],
        "trigger_rules": [
            {
                "rule_key": "post_food_potty",
                "enabled": True,
                "due_minutes": 5,
                "overdue_minutes": 10,
                "notes": "Faster food trigger",
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

    merged = app_module.merge_schedule_profile(base_schedule, profile)

    assert merged["post_food_potty_due"] == 5
    assert merged["post_food_potty_overdue"] == 10
    assert merged["overnight_potty_limit_minutes"] == 240
    assert merged["profile_source"] == "custom"
