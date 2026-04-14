from __future__ import annotations

import json
import os
import sqlite3
from calendar import monthrange
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

APP_TITLE = "Puppy Coordinator"
APP_VERSION = os.environ.get("PUPPY_TRACKER_VERSION", "v14.4")
DB_PATH = Path(os.environ.get("PUPPY_TRACKER_DB", "puppy_tracker.db"))
APP_PORT = int(os.environ.get("PUPPY_TRACKER_PORT", "8000"))
DEFAULT_TZ_OFFSET_MINUTES = int(os.environ.get("PUPPY_TZ_OFFSET_MINUTES", "-240"))

DEFAULT_ACTIVITIES = ["pee", "poop", "food", "water", "sleep", "wake", "play"]
DEFAULT_HOUSEHOLD_MEMBERS = ["McCaul", "Jess"]
REST_ACTIVITIES = {"sleep"}
STATUS_TILE_ORDER = ["pee", "poop", "food", "water", "awake"]
TAPPABLE_TILE_ACTIVITIES = {"pee", "poop", "food", "water"}
SECONDARY_QUICK_ACTION_ORDER = ["play", "sleep", "wake"]
ACTIVITY_LABELS = {
    "pee": "Pee",
    "poop": "Poop",
    "food": "Food",
    "water": "Water",
    "awake": "Awake",
    "play": "Play",
    "sleep": "Sleep",
    "wake": "Wake",
}
SCHEDULE_PROFILE_KEY = "schedule_profile"
ADVISORY_OVERRIDES_KEY = "advisory_overrides"
DEFAULT_DEFER_MINUTES = 20
WEEKDAY_IDS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
ROUTINE_FIELDS = [
    "pee_due",
    "pee_overdue",
    "poop_due",
    "poop_overdue",
    "food_due",
    "food_overdue",
    "water_due",
    "water_overdue",
    "awake_due",
    "awake_overdue",
    "sleep_default",
    "post_food_potty_due",
    "post_food_potty_overdue",
]
ROUTINE_FIELD_LABELS = {
    "pee_due": "Pee due",
    "pee_overdue": "Pee overdue",
    "poop_due": "Poop due",
    "poop_overdue": "Poop overdue",
    "food_due": "Food due",
    "food_overdue": "Food overdue",
    "water_due": "Water due",
    "water_overdue": "Water overdue",
    "awake_due": "Sleep due",
    "awake_overdue": "Sleep overdue",
    "sleep_default": "Nap length",
    "post_food_potty_due": "Post-food potty due",
    "post_food_potty_overdue": "Post-food potty overdue",
}
ROUTINE_VALUE_PAIRS = [
    ("pee_due", "pee_overdue"),
    ("poop_due", "poop_overdue"),
    ("food_due", "food_overdue"),
    ("water_due", "water_overdue"),
    ("awake_due", "awake_overdue"),
    ("post_food_potty_due", "post_food_potty_overdue"),
]
SIMPLE_ROUTINE_GROUPS = [
    {"id": "potty_rhythm", "label": "Potty rhythm", "description": "How quickly potty trips become due.", "fields": ["pee_due", "pee_overdue"]},
    {"id": "meal_rhythm", "label": "Meal rhythm", "description": "How quickly meals become due.", "fields": ["food_due", "food_overdue"]},
    {"id": "awake_window", "label": "Awake window", "description": "How long awake stretches usually last.", "fields": ["awake_due", "awake_overdue"]},
    {"id": "nap_length", "label": "Nap length", "description": "The usual nap target for quick sleep logs.", "fields": ["sleep_default"]},
]

AGE_BAND_DEFAULTS = [
    {
        "id": "8_to_10_weeks",
        "label": "8-10 weeks",
        "min_weeks": 0.0,
        "max_weeks": 10.0,
        "pee_due": 45,
        "pee_overdue": 60,
        "poop_due": 180,
        "poop_overdue": 240,
        "food_due": 240,
        "food_overdue": 300,
        "water_due": 90,
        "water_overdue": 120,
        "awake_due": 45,
        "awake_overdue": 60,
        "day_sleep_minutes": 120,
        "night_sleep_minutes": 180,
        "overnight_potty_limit_minutes": 180,
        "post_food_potty_due": 10,
        "post_food_potty_overdue": 20,
        "post_drink_potty_due": 10,
        "post_drink_potty_overdue": 20,
        "post_play_potty_due": 5,
        "post_play_potty_overdue": 15,
    },
    {
        "id": "10_to_12_weeks",
        "label": "10-12 weeks",
        "min_weeks": 10.0,
        "max_weeks": 12.0,
        "pee_due": 60,
        "pee_overdue": 90,
        "poop_due": 240,
        "poop_overdue": 300,
        "food_due": 300,
        "food_overdue": 360,
        "water_due": 120,
        "water_overdue": 180,
        "awake_due": 60,
        "awake_overdue": 75,
        "day_sleep_minutes": 120,
        "night_sleep_minutes": 210,
        "overnight_potty_limit_minutes": 210,
        "post_food_potty_due": 10,
        "post_food_potty_overdue": 25,
        "post_drink_potty_due": 10,
        "post_drink_potty_overdue": 20,
        "post_play_potty_due": 5,
        "post_play_potty_overdue": 15,
    },
    {
        "id": "12_to_16_weeks",
        "label": "12-16 weeks",
        "min_weeks": 12.0,
        "max_weeks": 16.0,
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
        "day_sleep_minutes": 120,
        "night_sleep_minutes": 240,
        "overnight_potty_limit_minutes": 240,
        "post_food_potty_due": 15,
        "post_food_potty_overdue": 30,
        "post_drink_potty_due": 10,
        "post_drink_potty_overdue": 20,
        "post_play_potty_due": 5,
        "post_play_potty_overdue": 15,
    },
    {
        "id": "4_to_6_months",
        "label": "4-6 months",
        "min_weeks": 16.0,
        "max_weeks": 24.0,
        "pee_due": 180,
        "pee_overdue": 240,
        "poop_due": 420,
        "poop_overdue": 540,
        "food_due": 480,
        "food_overdue": 720,
        "water_due": 240,
        "water_overdue": 300,
        "awake_due": 180,
        "awake_overdue": 240,
        "day_sleep_minutes": 120,
        "night_sleep_minutes": 300,
        "overnight_potty_limit_minutes": 300,
        "post_food_potty_due": 15,
        "post_food_potty_overdue": 30,
        "post_drink_potty_due": 10,
        "post_drink_potty_overdue": 20,
        "post_play_potty_due": 5,
        "post_play_potty_overdue": 15,
    },
    {
        "id": "6_plus_months",
        "label": "6+ months",
        "min_weeks": 24.0,
        "max_weeks": None,
        "pee_due": 240,
        "pee_overdue": 360,
        "poop_due": 540,
        "poop_overdue": 720,
        "food_due": 600,
        "food_overdue": 720,
        "water_due": 300,
        "water_overdue": 360,
        "awake_due": 240,
        "awake_overdue": 300,
        "day_sleep_minutes": 120,
        "night_sleep_minutes": 360,
        "overnight_potty_limit_minutes": 360,
        "post_food_potty_due": 15,
        "post_food_potty_overdue": 35,
        "post_drink_potty_due": 10,
        "post_drink_potty_overdue": 20,
        "post_play_potty_due": 5,
        "post_play_potty_overdue": 15,
    },
]
DEFAULT_ROUTINE_PROFILE_STATE = {
    "version": 1,
    "routine_mode": "default_auto",
    "last_reviewed_recommendation_band_id": None,
    "last_proposal_action": None,
    "custom_profile": None,
}

app = FastAPI(title=APP_TITLE)

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def normalize_activities(values: List[str]) -> List[str]:
    cleaned: List[str] = []
    for value in values:
        item = str(value).strip().lower()
        if not item or item in {"accident", "nap"} or item in cleaned:
            continue
        cleaned.append(item)
    for activity in DEFAULT_ACTIVITIES:
        if activity not in cleaned:
            cleaned.append(activity)
    return cleaned


def normalize_household_members(values: List[str]) -> List[str]:
    cleaned: List[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in cleaned:
            continue
        cleaned.append(item)
    return cleaned or DEFAULT_HOUSEHOLD_MEMBERS.copy()


def normalize_is_accident(activity: str, is_accident: bool) -> bool:
    return activity in {"pee", "poop"} and bool(is_accident)


def json_clone(value: Any) -> Any:
    return json.loads(json.dumps(value))


def load_json(raw_value: Optional[str], default: Any) -> Any:
    if not raw_value:
        return json_clone(default)
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return json_clone(default)


def add_calendar_months(value: date, months: int) -> date:
    month_index = (value.month - 1) + months
    year = value.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def has_reached_calendar_months(birth: Optional[date], current: date, months: int) -> bool:
    if not birth:
        return False
    return current >= add_calendar_months(birth, months)


def is_overnight(dt: datetime, offset_minutes: int) -> bool:
    local = dt.astimezone(timezone(timedelta(minutes=offset_minutes)))
    return local.hour >= 21 or local.hour < 6


def advisory_key(action: str, suffix: str = "") -> str:
    return f"{action}:{suffix}" if suffix else action


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_time_utc TEXT NOT NULL,
                duration_minutes INTEGER,
                is_accident INTEGER NOT NULL DEFAULT 0,
                note TEXT,
                created_at_utc TEXT NOT NULL
            );
            """
        )
        event_columns = {row["name"] for row in conn.execute("PRAGMA table_info(events)")}
        if "is_accident" not in event_columns:
            conn.execute("ALTER TABLE events ADD COLUMN is_accident INTEGER NOT NULL DEFAULT 0")
        existing = {
            row["key"]: row["value"]
            for row in conn.execute("SELECT key, value FROM settings")
        }
        defaults = {
            "puppy_name": "Puppy",
            "household_name": "Home",
            "timezone_offset_minutes": str(DEFAULT_TZ_OFFSET_MINUTES),
            "activities": json.dumps(DEFAULT_ACTIVITIES),
            "household_members": json.dumps(DEFAULT_HOUSEHOLD_MEMBERS),
            "puppy_birth_date": "",
            SCHEDULE_PROFILE_KEY: json.dumps({"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []}),
            ADVISORY_OVERRIDES_KEY: json.dumps([]),
            "routine_profile_state": json.dumps(DEFAULT_ROUTINE_PROFILE_STATE),
        }
        for key, value in defaults.items():
            if key not in existing:
                conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))


class EventIn(BaseModel):
    activity: str = Field(..., min_length=1, max_length=50)
    actor: str = Field(..., min_length=1, max_length=50)
    event_time_utc: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    is_accident: bool = False
    note: Optional[str] = Field(default="", max_length=500)


class EventUpdate(BaseModel):
    activity: str = Field(..., min_length=1, max_length=50)
    actor: str = Field(..., min_length=1, max_length=50)
    event_time_utc: str
    duration_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    is_accident: bool = False
    note: Optional[str] = Field(default="", max_length=500)


class SettingsIn(BaseModel):
    puppy_name: str = Field(..., min_length=1, max_length=50)
    household_name: str = Field(..., min_length=1, max_length=50)
    timezone_offset_minutes: int = Field(..., ge=-720, le=840)
    activities: List[str] = Field(..., min_items=3, max_items=20)
    household_members: List[str] = Field(default_factory=lambda: DEFAULT_HOUSEHOLD_MEMBERS.copy(), min_items=1, max_items=10)
    puppy_birth_date: Optional[str] = Field(default="")


class RoutineProfileIn(BaseModel):
    base_age_band_id: str = Field(..., min_length=1, max_length=50)
    save_mode: str = Field(..., min_length=1, max_length=20)
    custom_values: Dict[str, int]


class RoutineProposalDecisionIn(BaseModel):
    action: str = Field(..., min_length=1, max_length=20)


class RoutineBlockIn(BaseModel):
    id: Optional[str] = Field(default=None, min_length=1, max_length=80)
    kind: str = Field(..., min_length=1, max_length=40)
    label: str = Field(..., min_length=1, max_length=80)
    start_local_time: Optional[str] = Field(default="")
    duration_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    days_of_week: List[str] = Field(default_factory=list)
    enabled: bool = True
    source: str = Field(default="custom", min_length=1, max_length=20)


class TriggerRuleIn(BaseModel):
    rule_key: str = Field(..., min_length=1, max_length=80)
    enabled: bool = True
    due_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    overdue_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    notes: str = Field(default="", max_length=200)
    source: str = Field(default="custom", min_length=1, max_length=20)


class CareLimitIn(BaseModel):
    need: str = Field(..., min_length=1, max_length=40)
    context: str = Field(..., min_length=1, max_length=40)
    limit_minutes: int = Field(..., ge=1, le=1440)
    source: str = Field(default="custom", min_length=1, max_length=20)
    emphasis: str = Field(default="normal", min_length=1, max_length=20)


class ScheduleProfileIn(BaseModel):
    source: str = Field(default="custom", min_length=1, max_length=20)
    routine_blocks: List[RoutineBlockIn] = Field(default_factory=list)
    trigger_rules: List[TriggerRuleIn] = Field(default_factory=list)
    care_limits: List[CareLimitIn] = Field(default_factory=list)


class AdvisoryActionIn(BaseModel):
    advisory_key: str = Field(..., min_length=1, max_length=120)
    action: str = Field(..., min_length=1, max_length=20)
    defer_minutes: Optional[int] = Field(default=None, ge=1, le=720)


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast_json(self, payload: Dict[str, Any]) -> None:
        dead: List[WebSocket] = []
        for connection in self.connections:
            try:
                await connection.send_json(payload)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)


manager = ConnectionManager()


def get_settings() -> Dict[str, Any]:
    with get_db() as conn:
        raw = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM settings")}
    activities = normalize_activities(json.loads(raw.get("activities", json.dumps(DEFAULT_ACTIVITIES))))
    household_members = normalize_household_members(
        json.loads(raw.get("household_members", json.dumps(DEFAULT_HOUSEHOLD_MEMBERS)))
    )
    schedule_profile = load_json(raw.get(SCHEDULE_PROFILE_KEY), {"source": "default", "routine_blocks": [], "trigger_rules": [], "care_limits": []})
    advisory_overrides = load_json(raw.get(ADVISORY_OVERRIDES_KEY), [])
    return {
        "puppy_name": raw.get("puppy_name", "Puppy"),
        "household_name": raw.get("household_name", "Home"),
        "timezone_offset_minutes": int(raw.get("timezone_offset_minutes", str(DEFAULT_TZ_OFFSET_MINUTES))),
        "activities": activities,
        "household_members": household_members,
        "puppy_birth_date": raw.get("puppy_birth_date", ""),
        "schedule_profile": schedule_profile,
        "advisory_overrides": advisory_overrides,
        "routine_profile_state": raw.get("routine_profile_state", json.dumps(DEFAULT_ROUTINE_PROFILE_STATE)),
    }


def save_json_setting(key: str, value: Any) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value)),
        )


def resolve_age_band(settings: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    birth = parse_date(settings.get("puppy_birth_date"))
    age_weeks = get_age_weeks(settings, now)
    if age_weeks is None:
        age_weeks = 12.0
    if birth:
        current_date = now.date()
        if age_weeks < 10.0:
            resolved = json_clone(AGE_BAND_DEFAULTS[0])
        elif age_weeks < 12.0:
            resolved = json_clone(AGE_BAND_DEFAULTS[1])
        elif age_weeks < 16.0 or not has_reached_calendar_months(birth, current_date, 4):
            resolved = json_clone(AGE_BAND_DEFAULTS[2])
        elif not has_reached_calendar_months(birth, current_date, 6):
            resolved = json_clone(AGE_BAND_DEFAULTS[3])
        else:
            resolved = json_clone(AGE_BAND_DEFAULTS[4])
        resolved["age_weeks"] = round(age_weeks, 1)
        return resolved
    for band in AGE_BAND_DEFAULTS:
        upper = band["max_weeks"]
        if upper is None or age_weeks < upper:
            resolved = json_clone(band)
            resolved["age_weeks"] = round(age_weeks, 1)
            return resolved
    resolved = json_clone(AGE_BAND_DEFAULTS[-1])
    resolved["age_weeks"] = round(age_weeks, 1)
    return resolved


def get_schedule_band_by_id(band_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not band_id:
        return None
    for band in AGE_BAND_DEFAULTS:
        if band["id"] == band_id:
            return json_clone(band)
    return None


def schedule_values_from_band(band: Dict[str, Any]) -> Dict[str, int]:
    return {
        "pee_due": int(band["pee_due"]),
        "pee_overdue": int(band["pee_overdue"]),
        "poop_due": int(band["poop_due"]),
        "poop_overdue": int(band["poop_overdue"]),
        "food_due": int(band["food_due"]),
        "food_overdue": int(band["food_overdue"]),
        "water_due": int(band["water_due"]),
        "water_overdue": int(band["water_overdue"]),
        "awake_due": int(band["awake_due"]),
        "awake_overdue": int(band["awake_overdue"]),
        "sleep_default": int(band["day_sleep_minutes"]),
        "post_food_potty_due": int(band["post_food_potty_due"]),
        "post_food_potty_overdue": int(band["post_food_potty_overdue"]),
    }


def normalize_routine_values(base_values: Dict[str, int], custom_values: Any) -> Dict[str, int]:
    if not isinstance(custom_values, dict):
        return base_values.copy()
    normalized = base_values.copy()
    for field in ROUTINE_FIELDS:
        raw_value = custom_values.get(field, base_values[field])
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = base_values[field]
        normalized[field] = value if 1 <= value <= 1440 else base_values[field]
    for due_key, overdue_key in ROUTINE_VALUE_PAIRS:
        if normalized[due_key] >= normalized[overdue_key]:
            normalized[due_key] = base_values[due_key]
            normalized[overdue_key] = base_values[overdue_key]
    return normalized


def normalize_routine_profile_state(raw_value: Any) -> Dict[str, Any]:
    state = {
        "version": 1,
        "routine_mode": "default_auto",
        "last_reviewed_recommendation_band_id": None,
        "last_proposal_action": None,
        "custom_profile": None,
    }
    parsed = raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
    if not isinstance(parsed, dict):
        return state

    routine_mode = parsed.get("routine_mode")
    if routine_mode in {"default_auto", "custom_manual"}:
        state["routine_mode"] = routine_mode
    reviewed_band_id = parsed.get("last_reviewed_recommendation_band_id")
    if get_schedule_band_by_id(reviewed_band_id):
        state["last_reviewed_recommendation_band_id"] = reviewed_band_id
    last_proposal_action = parsed.get("last_proposal_action")
    if last_proposal_action in {"accepted", "rejected"}:
        state["last_proposal_action"] = last_proposal_action

    custom_profile = parsed.get("custom_profile")
    if state["routine_mode"] == "custom_manual" and isinstance(custom_profile, dict):
        base_age_band_id = custom_profile.get("base_age_band_id")
        base_band = get_schedule_band_by_id(base_age_band_id)
        if base_band:
            state["custom_profile"] = {
                "base_age_band_id": base_age_band_id,
                "updated_at_utc": custom_profile.get("updated_at_utc") or utc_now_iso(),
                "last_saved_mode": custom_profile.get("last_saved_mode")
                if custom_profile.get("last_saved_mode") in {"simple", "advanced"}
                else "simple",
                "custom_values": normalize_routine_values(
                    schedule_values_from_band(base_band),
                    custom_profile.get("custom_values"),
                ),
            }
        else:
            state["routine_mode"] = "default_auto"

    if state["routine_mode"] == "default_auto":
        state["custom_profile"] = None

    return state


def save_routine_profile_state(routine_profile_state: Dict[str, Any]) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ('routine_profile_state', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (json.dumps(routine_profile_state),),
        )


def validate_custom_routine_values(custom_values: Any) -> tuple[Optional[Dict[str, int]], Optional[str]]:
    if not isinstance(custom_values, dict):
        return None, "Custom routine values are required"
    normalized: Dict[str, int] = {}
    for field in ROUTINE_FIELDS:
        if field not in custom_values:
            return None, f"Missing routine field: {field}"
        try:
            value = int(custom_values[field])
        except (TypeError, ValueError):
            return None, f"Invalid routine field: {field}"
        if value < 1 or value > 1440:
            return None, f"Routine field out of range: {field}"
        normalized[field] = value
    for due_key, overdue_key in ROUTINE_VALUE_PAIRS:
        if normalized[due_key] >= normalized[overdue_key]:
            return None, f"{due_key} must be less than {overdue_key}"
    return normalized, None


def age_band_summary(age_weeks: float, band: Dict[str, Any]) -> str:
    return f"At {round(age_weeks, 1)} weeks, the {band['label']} routine is the current recommendation."


def sort_routine_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        blocks,
        key=lambda item: (
            str(item.get("start_local_time") or "99:99"),
            str(item.get("kind") or ""),
            str(item.get("label") or ""),
            str(item.get("id") or ""),
        ),
    )


def normalize_schedule_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    routine_blocks = []
    for index, block in enumerate(profile.get("routine_blocks") or []):
        routine_blocks.append(
            {
                "id": str(block.get("id") or f"custom-block-{index + 1}"),
                "kind": str(block.get("kind") or "sleep"),
                "label": str(block.get("label") or "Routine block"),
                "start_local_time": str(block.get("start_local_time") or ""),
                "duration_minutes": int(block["duration_minutes"]) if block.get("duration_minutes") is not None else None,
                "days_of_week": [day for day in (block.get("days_of_week") or WEEKDAY_IDS) if day in WEEKDAY_IDS] or WEEKDAY_IDS.copy(),
                "enabled": bool(block.get("enabled", True)),
                "source": str(block.get("source") or "custom"),
            }
        )
    trigger_rules = []
    for rule in profile.get("trigger_rules") or []:
        trigger_rules.append(
            {
                "rule_key": str(rule.get("rule_key") or ""),
                "enabled": bool(rule.get("enabled", True)),
                "due_minutes": int(rule["due_minutes"]) if rule.get("due_minutes") is not None else None,
                "overdue_minutes": int(rule["overdue_minutes"]) if rule.get("overdue_minutes") is not None else None,
                "notes": str(rule.get("notes") or ""),
                "source": str(rule.get("source") or "custom"),
            }
        )
    care_limits = []
    for limit in profile.get("care_limits") or []:
        care_limits.append(
            {
                "need": str(limit.get("need") or ""),
                "context": str(limit.get("context") or ""),
                "limit_minutes": int(limit["limit_minutes"]) if limit.get("limit_minutes") is not None else 0,
                "source": str(limit.get("source") or "custom"),
                "emphasis": str(limit.get("emphasis") or "normal"),
            }
        )
    return {
        "source": str(profile.get("source") or "custom"),
        "routine_blocks": sort_routine_blocks(routine_blocks),
        "trigger_rules": trigger_rules,
        "care_limits": care_limits,
    }


def routine_summary_cards(schedule: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "title": "Active age band",
            "primary": f"{schedule['age_label']} ({schedule['age_weeks']} weeks)",
            "secondary": f"Using {schedule['context_label'].lower()} guidance",
        },
        {
            "title": "Awake window",
            "primary": f"{human_minutes_short(schedule['awake_due'])} due / {human_minutes_short(schedule['awake_overdue'])} overdue",
            "secondary": f"Typical {human_minutes_short(schedule['day_sleep_minutes'])} daytime naps",
        },
        {
            "title": "Potty timing",
            "primary": f"{human_minutes_short(schedule['pee_due'])} due / {human_minutes_short(schedule['pee_overdue'])} overdue",
            "secondary": (
                f"Post-food potty {human_minutes_short(schedule['post_food_potty_due'])}-"
                f"{human_minutes_short(schedule['post_food_potty_overdue'])}"
            ),
        },
        {
            "title": "Overnight limit",
            "primary": f"Potty check by {human_minutes_short(schedule['overnight_potty_limit_minutes'])} overnight",
            "secondary": f"Default overnight block {human_minutes_short(schedule['night_sleep_minutes'])}",
        },
        {
            "title": "Food and water",
            "primary": (
                f"Food {human_minutes_short(schedule['food_due'])} / "
                f"Water {human_minutes_short(schedule['water_due'])}"
            ),
            "secondary": f"Water overdue at {human_minutes_short(schedule['water_overdue'])}",
        },
    ]


def default_routine_blocks(schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
    lunch_enabled = schedule["age_weeks"] < 24
    blocks = [
        {
            "id": "default-breakfast",
            "kind": "feeding",
            "label": "Breakfast",
            "start_local_time": "07:00",
            "duration_minutes": 15,
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-morning-nap",
            "kind": "sleep",
            "label": "Morning nap",
            "start_local_time": "09:00",
            "duration_minutes": schedule["day_sleep_minutes"],
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-training",
            "kind": "training",
            "label": "Training block",
            "start_local_time": "11:30",
            "duration_minutes": 20,
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-lunch",
            "kind": "feeding",
            "label": "Midday meal",
            "start_local_time": "12:30",
            "duration_minutes": 15,
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": lunch_enabled,
            "source": "default-age-band",
        },
        {
            "id": "default-midday-nap",
            "kind": "sleep",
            "label": "Midday nap",
            "start_local_time": "13:30",
            "duration_minutes": schedule["day_sleep_minutes"],
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-play",
            "kind": "play",
            "label": "Active play",
            "start_local_time": "16:00",
            "duration_minutes": 25,
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-dinner",
            "kind": "feeding",
            "label": "Dinner",
            "start_local_time": "18:00",
            "duration_minutes": 15,
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-evening-water",
            "kind": "water",
            "label": "Evening water check",
            "start_local_time": "19:30",
            "duration_minutes": 10,
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
        {
            "id": "default-overnight-sleep",
            "kind": "sleep",
            "label": "Overnight sleep",
            "start_local_time": "22:00",
            "duration_minutes": schedule["night_sleep_minutes"],
            "days_of_week": WEEKDAY_IDS.copy(),
            "enabled": True,
            "source": "default-age-band",
        },
    ]
    return sort_routine_blocks(blocks)


def default_trigger_rules(schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "rule_key": "post_food_potty",
            "enabled": True,
            "due_minutes": schedule["post_food_potty_due"],
            "overdue_minutes": schedule["post_food_potty_overdue"],
            "notes": "Prompt a potty break after food.",
            "source": "default-age-band",
        },
        {
            "rule_key": "post_drink_potty",
            "enabled": True,
            "due_minutes": schedule["post_drink_potty_due"],
            "overdue_minutes": schedule["post_drink_potty_overdue"],
            "notes": "Prompt a potty break after drinking.",
            "source": "default-age-band",
        },
        {
            "rule_key": "post_play_potty",
            "enabled": True,
            "due_minutes": schedule["post_play_potty_due"],
            "overdue_minutes": schedule["post_play_potty_overdue"],
            "notes": "Prompt a potty break after active play.",
            "source": "default-age-band",
        },
    ]


def default_care_limits(schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "need": "potty",
            "context": "overnight",
            "limit_minutes": schedule["overnight_potty_limit_minutes"],
            "source": "default-age-band",
            "emphasis": "high",
        }
    ]


def build_schedule_profile_payload(settings: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    active_band = resolve_age_band(settings, now)
    schedule = get_schedule(settings, now)
    profile = normalize_schedule_profile(settings.get("schedule_profile") or {})
    return {
        "profile_version": 1,
        "source": profile["source"] if profile["routine_blocks"] or profile["trigger_rules"] or profile["care_limits"] else "default",
        "active_age_band": {
            "id": schedule["age_band_id"],
            "label": schedule["age_label"],
            "min_weeks": active_band["min_weeks"],
            "max_weeks": active_band["max_weeks"],
        },
        "routine_blocks": profile["routine_blocks"] or default_routine_blocks(schedule),
        "care_limits": profile["care_limits"] or default_care_limits(schedule),
        "trigger_rules": profile["trigger_rules"] or default_trigger_rules(schedule),
    }


def validate_schedule_profile(profile: Dict[str, Any]) -> Optional[str]:
    for rule in profile.get("trigger_rules", []):
        due = rule.get("due_minutes")
        overdue = rule.get("overdue_minutes")
        if due is not None and overdue is not None and due >= overdue:
            return f"Rule {rule.get('rule_key') or 'unknown'} must have due time before overdue time."
    for limit in profile.get("care_limits", []):
        if limit.get("need") == "potty" and limit.get("context") == "overnight" and int(limit.get("limit_minutes") or 0) < 60:
            return "Overnight potty limit must be at least 60 minutes."
    return None


def merge_schedule_profile(base_schedule: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    schedule = json_clone(base_schedule)
    normalized = normalize_schedule_profile(profile)
    trigger_map = {item.get("rule_key"): item for item in normalized["trigger_rules"] if item.get("rule_key")}
    care_limit_map = {
        (item.get("need"), item.get("context")): item
        for item in normalized["care_limits"]
        if item.get("need") and item.get("context")
    }

    for rule_key, due_key, overdue_key in [
        ("post_food_potty", "post_food_potty_due", "post_food_potty_overdue"),
        ("post_drink_potty", "post_drink_potty_due", "post_drink_potty_overdue"),
        ("post_play_potty", "post_play_potty_due", "post_play_potty_overdue"),
    ]:
        override = trigger_map.get(rule_key)
        if not override:
            continue
        if override.get("due_minutes") is not None:
            schedule[due_key] = int(override["due_minutes"])
        if override.get("overdue_minutes") is not None:
            schedule[overdue_key] = int(override["overdue_minutes"])

    overnight_limit = care_limit_map.get(("potty", "overnight"))
    if overnight_limit:
        schedule["overnight_potty_limit_minutes"] = int(overnight_limit["limit_minutes"])

    schedule["profile_source"] = normalized["source"] if normalized["routine_blocks"] or normalized["trigger_rules"] or normalized["care_limits"] else "default"
    schedule["routine_blocks"] = normalized["routine_blocks"]
    schedule["trigger_rules"] = normalized["trigger_rules"]
    schedule["care_limits"] = normalized["care_limits"]
    schedule["routine_summary"] = routine_summary_cards(schedule)
    return schedule


def list_recent_activity(events_desc: List[Dict[str, Any]], activity: str, minutes_window: int, now: datetime) -> Optional[Dict[str, Any]]:
    for event in events_desc:
        if event["activity"] != activity:
            continue
        elapsed = minutes_since(event.get("event_time_utc"), now)
        if elapsed is not None and elapsed <= minutes_window:
            return event
    return None


def find_latest_activity_after(events_desc: List[Dict[str, Any]], activities: List[str], after_iso: Optional[str]) -> Optional[Dict[str, Any]]:
    after_dt = parse_iso(after_iso)
    if not after_dt:
        return None
    activity_set = set(activities)
    for event in events_desc:
        if event["activity"] not in activity_set:
            continue
        event_dt = parse_iso(event.get("event_time_utc"))
        if event_dt and event_dt > after_dt:
            return event
    return None


def build_triggered_by(rule_type: str, details: List[str]) -> List[str]:
    return [f"{rule_type}: {detail}" for detail in details if detail]


def list_events(limit: int = 200) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, activity, actor, event_time_utc, duration_minutes, note, created_at_utc
                 , is_accident
            FROM events
            ORDER BY event_time_utc DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def minutes_since(iso: Optional[str], now: datetime) -> Optional[int]:
    dt = parse_iso(iso)
    if not dt:
        return None
    return max(0, int(round((now - dt).total_seconds() / 60)))


def human_minutes_short(minutes: Optional[int]) -> str:
    if minutes is None:
        return "never"
    if minutes < 1:
        return "now"
    total_minutes = int(minutes)
    hours, remainder = divmod(total_minutes, 60)
    if hours == 0:
        return f"{total_minutes}m"
    if hours < 24:
        return f"{hours}h {remainder}m" if remainder else f"{hours}h"
    days, remaining_hours = divmod(hours, 24)
    return f"{days}d {remaining_hours}h" if remaining_hours else f"{days}d"


def human_ago(minutes: Optional[int]) -> str:
    if minutes is None:
        return "No entries yet"
    if minutes < 1:
        return "just now"
    return f"{human_minutes_short(minutes)} ago"


def get_age_weeks(settings: Dict[str, Any], now: datetime) -> Optional[float]:
    birth = parse_date(settings.get("puppy_birth_date"))
    if not birth:
        return None
    days = (now.date() - birth).days
    if days < 0:
        return 0.0
    return days / 7.0


def build_schedule_from_band(band: Dict[str, Any], settings: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    overnight = is_overnight(now, settings["timezone_offset_minutes"])
    schedule = {
        "age_band_id": band["id"],
        "age_label": band["label"],
        "age_weeks": band["age_weeks"],
        "pee_due": band["pee_due"],
        "pee_overdue": band["pee_overdue"],
        "poop_due": band["poop_due"],
        "poop_overdue": band["poop_overdue"],
        "food_due": band["food_due"],
        "food_overdue": band["food_overdue"],
        "water_due": band["water_due"],
        "water_overdue": band["water_overdue"],
        "awake_due": band["awake_due"],
        "awake_overdue": band["awake_overdue"],
        "post_food_potty_due": band["post_food_potty_due"],
        "post_food_potty_overdue": band["post_food_potty_overdue"],
        "post_drink_potty_due": band["post_drink_potty_due"],
        "post_drink_potty_overdue": band["post_drink_potty_overdue"],
        "post_play_potty_due": band["post_play_potty_due"],
        "post_play_potty_overdue": band["post_play_potty_overdue"],
        "day_sleep_minutes": band["day_sleep_minutes"],
        "night_sleep_minutes": band["night_sleep_minutes"],
        "overnight_potty_limit_minutes": band["overnight_potty_limit_minutes"],
        "context_label": "Overnight" if overnight else "Daytime",
        "is_overnight": overnight,
        "default_sleep_minutes": band["night_sleep_minutes"] if overnight else band["day_sleep_minutes"],
        "profile_source": "default",
        "routine_blocks": [],
        "trigger_rules": [],
        "care_limits": [],
        "routine_summary": [],
    }
    return merge_schedule_profile(schedule, settings.get("schedule_profile") or {})


def build_routine_proposal(current_band: Dict[str, Any], current_values: Dict[str, int], recommended_band: Dict[str, Any]) -> Dict[str, Any]:
    recommended_values = schedule_values_from_band(recommended_band)
    diff_items = []
    for field in ROUTINE_FIELDS:
        if current_values[field] == recommended_values[field]:
            continue
        diff_items.append(
            {
                "field_id": field,
                "label": ROUTINE_FIELD_LABELS[field],
                "current_value": current_values[field],
                "recommended_value": recommended_values[field],
                "change_note": f"Typical {recommended_band['label']} guidance uses {recommended_values[field]} minutes here.",
            }
        )
    return {
        "proposal_id": f"{current_band['id']}-to-{recommended_band['id']}",
        "status": "pending",
        "current_custom_age_band_id": current_band["id"],
        "recommended_age_band_id": recommended_band["id"],
        "headline": f"Your puppy is now in the {recommended_band['label']} stage",
        "summary_text": f"We'd usually adjust the routine toward the {recommended_band['label']} defaults at this age.",
        "diff_items": diff_items,
        "reviewed_at_utc": None,
    }


def resolve_routine_profile(settings: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    age_weeks = get_age_weeks(settings, now)
    if age_weeks is None:
        age_weeks = 12.0

    recommended_band = resolve_age_band(settings, now)
    recommended_schedule = build_schedule_from_band(recommended_band, settings, now)
    recommended_values = schedule_values_from_band(recommended_band)
    routine_profile_state = normalize_routine_profile_state(settings.get("routine_profile_state"))
    custom_profile = routine_profile_state.get("custom_profile")

    if routine_profile_state["routine_mode"] == "custom_manual" and custom_profile:
        current_band = get_schedule_band_by_id(custom_profile["base_age_band_id"]) or recommended_band
        current_band["age_weeks"] = round(age_weeks, 1)
        schedule = build_schedule_from_band(current_band, settings, now)
        effective_values = normalize_routine_values(
            schedule_values_from_band(current_band),
            custom_profile.get("custom_values"),
        )
        profile_source = "custom_saved"
        effective_age_band_id = current_band["id"]
        effective_age_label = current_band["label"]
        last_saved_mode = custom_profile.get("last_saved_mode")
    else:
        current_band = recommended_band
        schedule = recommended_schedule
        effective_values = {
            field_id: (schedule["day_sleep_minutes"] if field_id == "sleep_default" else schedule[field_id])
            for field_id in ROUTINE_FIELDS
        }
        profile_source = "default_current_age"
        effective_age_band_id = recommended_band["id"]
        effective_age_label = recommended_band["label"]
        last_saved_mode = None

    for field_id, value in effective_values.items():
        if field_id == "sleep_default":
            schedule["day_sleep_minutes"] = value
            if not schedule["is_overnight"]:
                schedule["default_sleep_minutes"] = value
            schedule["sleep_default"] = value
        else:
            schedule[field_id] = value
    if schedule["is_overnight"]:
        schedule["default_sleep_minutes"] = schedule["night_sleep_minutes"]
    else:
        schedule["default_sleep_minutes"] = schedule["day_sleep_minutes"]
    schedule["age_band_id"] = effective_age_band_id
    schedule["age_label"] = effective_age_label
    schedule["age_weeks"] = round(age_weeks, 1)
    schedule["routine_mode"] = routine_profile_state["routine_mode"]
    schedule["profile_source"] = profile_source
    schedule["effective_age_band_id"] = effective_age_band_id
    schedule["recommended_age_band_id"] = recommended_band["id"]
    schedule["recommended_age_label"] = recommended_band["label"]
    schedule["defaults"] = recommended_values
    schedule["last_saved_mode"] = last_saved_mode

    routine_proposal = None
    if (
        routine_profile_state["routine_mode"] == "custom_manual"
        and current_band["id"] != recommended_band["id"]
        and routine_profile_state.get("last_reviewed_recommendation_band_id") != recommended_band["id"]
    ):
        routine_proposal = build_routine_proposal(current_band, effective_values, recommended_band)

    return {
        "age_weeks": age_weeks,
        "recommended_band": recommended_band,
        "current_band": current_band,
        "schedule": schedule,
        "routine_profile_state": routine_profile_state,
        "routine_proposal": routine_proposal,
        "summary_text": age_band_summary(age_weeks, recommended_band),
    }


def get_schedule(settings: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    return resolve_routine_profile(settings, now)["schedule"]


def find_last(events_desc: List[Dict[str, Any]], activity: str) -> Optional[Dict[str, Any]]:
    for event in events_desc:
        if event["activity"] == activity:
            return event
    return None


def build_sleep_projection(settings: Dict[str, Any], start_dt: datetime, planned_minutes: int) -> Dict[str, Any]:
    start_schedule = get_schedule(settings, start_dt)
    recommended_minutes = planned_minutes
    warning = None
    if start_schedule["is_overnight"] and planned_minutes > start_schedule["overnight_potty_limit_minutes"]:
        recommended_minutes = start_schedule["overnight_potty_limit_minutes"]
        warning = (
            f"This sleep block reaches the overnight potty limit around "
            f"{local_time_label((start_dt + timedelta(minutes=recommended_minutes)).isoformat(), settings['timezone_offset_minutes'])}."
        )
    elif start_schedule["is_overnight"]:
        warning = None

    recommended_check = start_dt + timedelta(minutes=recommended_minutes)
    if warning:
        reason = warning
    elif start_schedule["is_overnight"]:
        reason = (
            f"Potty check by {local_time_label(recommended_check.isoformat(), settings['timezone_offset_minutes'])} "
            f"based on the current overnight limit."
        )
    else:
        reason = (
            f"Likely okay until {local_time_label(recommended_check.isoformat(), settings['timezone_offset_minutes'])} "
            f"based on the current daytime nap rhythm."
        )
    return {
        "context_label": start_schedule["context_label"],
        "planned_minutes": planned_minutes,
        "recommended_check_time_utc": recommended_check.isoformat(),
        "recommended_check_reason": reason,
        "care_limit_warning": warning,
    }


def latest_sleep_block(events_desc: List[Dict[str, Any]], settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    events_asc = list(reversed(events_desc))
    latest_block = None
    current_now = utc_now()
    for index, event in enumerate(events_asc):
        if event["activity"] != "sleep":
            continue
        start_dt = parse_iso(event["event_time_utc"])
        if not start_dt:
            continue
        start_schedule = get_schedule(settings, start_dt)
        planned = event.get("duration_minutes") or start_schedule["default_sleep_minutes"]
        projection = build_sleep_projection(settings, start_dt, planned)
        projected_end = start_dt + timedelta(minutes=planned)
        actual_end = projected_end
        end_source = "projected"
        for later in events_asc[index + 1:]:
            later_dt = parse_iso(later["event_time_utc"])
            if not later_dt or later_dt <= start_dt:
                continue
            if later["activity"] == "wake":
                actual_end = later_dt
                end_source = "wake"
                break
            if later["activity"] != "sleep" and later_dt < projected_end:
                actual_end = later_dt
                end_source = "activity"
                break
        latest_block = {
            "start_time_utc": event["event_time_utc"],
            "planned_duration_minutes": planned,
            "projected_end_time_utc": projected_end.isoformat(),
            "end_time_utc": actual_end.isoformat(),
            "actual_duration_minutes": max(0, int(round((actual_end - start_dt).total_seconds() / 60))),
            "is_sleeping_now": current_now < actual_end,
            "end_source": end_source,
            "recommended_check_time_utc": projection["recommended_check_time_utc"],
            "recommended_check_reason": projection["recommended_check_reason"],
            "care_limit_warning": projection["care_limit_warning"],
            "start_context_label": projection["context_label"],
        }
    return latest_block


def current_awake_minutes(events_desc: List[Dict[str, Any]], settings: Dict[str, Any], now: datetime) -> Optional[int]:
    block = latest_sleep_block(events_desc, settings)
    if block:
        end_dt = parse_iso(block["end_time_utc"])
        if end_dt:
            if now < end_dt:
                return 0
            return max(0, int(round((now - end_dt).total_seconds() / 60)))
    most_recent = None
    for event in events_desc:
        dt = parse_iso(event["event_time_utc"])
        if dt:
            most_recent = dt
            break
    if not most_recent:
        return None
    return max(0, int(round((now - most_recent).total_seconds() / 60)))


def current_state_anchor_utc(events_desc: List[Dict[str, Any]], sleep_block: Optional[Dict[str, Any]]) -> Optional[str]:
    if sleep_block:
        return sleep_block["start_time_utc"] if sleep_block["is_sleeping_now"] else sleep_block["end_time_utc"]
    for event in events_desc:
        if event.get("event_time_utc"):
            return event["event_time_utc"]
    return None


def urgency(value: Optional[int], due: int, overdue: int) -> str:
    if value is None:
        return "unknown"
    if value >= overdue:
        return "overdue"
    if value >= due:
        return "soon"
    return "ok"


def urgency_label(value: str) -> str:
    return {
        "overdue": "Overdue",
        "soon": "Due soon",
        "unknown": "No data",
        "ok": "On track",
    }.get(value, "On track")


def build_status_tile(
    key: str,
    minutes: Optional[int],
    urgency_value: str,
    *,
    is_tappable: bool,
    label_override: Optional[str] = None,
    display_value_override: Optional[str] = None,
    detail_text: Optional[str] = None,
    tap_activity_override: Optional[str] = None,
    tap_hint_override: Optional[str] = None,
    show_urgency: bool = True,
    readonly_reason: Optional[str] = None,
) -> Dict[str, Any]:
    tap_activity = tap_activity_override if is_tappable else None
    if tap_activity is None and is_tappable:
        tap_activity = key
    return {
        "key": key,
        "label": label_override or ACTIVITY_LABELS[key],
        "minutes": minutes,
        "display_value": display_value_override or human_ago(minutes),
        "detail_text": detail_text,
        "urgency": urgency_value,
        "urgency_label": urgency_label(urgency_value),
        "show_urgency": show_urgency,
        "is_tappable": is_tappable,
        "tap_activity": tap_activity,
        "tap_hint": tap_hint_override or ("Tap to log" if is_tappable else None),
        "readonly_reason": readonly_reason,
    }


def local_time_label(iso: Optional[str], offset_minutes: int) -> str:
    dt = parse_iso(iso)
    if not dt:
        return "unknown"
    local = dt.astimezone(timezone(timedelta(minutes=offset_minutes)))
    if os.name == "nt":
        return local.strftime("%#I:%M %p")
    return local.strftime("%-I:%M %p")


def routine_time_window_label(now: datetime, start_minutes: int, end_minutes: int, offset_minutes: int) -> str:
    if start_minutes <= 0 and end_minutes <= 0:
        return "Due now"
    start_label = local_time_label((now + timedelta(minutes=max(0, start_minutes))).isoformat(), offset_minutes)
    end_label = local_time_label((now + timedelta(minutes=max(0, end_minutes))).isoformat(), offset_minutes)
    if start_minutes <= 0:
        return f"Any time now to about {end_label}"
    return f"Around {start_label} to {end_label}"


def build_routine_item(
    item_id: str,
    kind: str,
    phase: str,
    title: str,
    start_minutes: int,
    end_minutes: int,
    explanation: str,
    now: datetime,
    offset_minutes: int,
    emphasis: str = "normal",
) -> Dict[str, Any]:
    return {
        "id": item_id,
        "kind": kind,
        "phase": phase,
        "title": title,
        "window_start_utc": (now + timedelta(minutes=max(0, start_minutes))).isoformat(),
        "window_end_utc": (now + timedelta(minutes=max(0, end_minutes))).isoformat(),
        "time_label": routine_time_window_label(now, start_minutes, end_minutes, offset_minutes),
        "explanation": explanation,
        "emphasis": emphasis,
    }


def build_routine_overview(
    settings: Dict[str, Any],
    resolved_profile: Dict[str, Any],
    live: Dict[str, Any],
    now: datetime,
) -> Dict[str, Any]:
    schedule = resolved_profile["schedule"]
    proposal = resolved_profile["routine_proposal"]
    offset_minutes = settings["timezone_offset_minutes"]
    has_recent_events = any(
        event_value is not None for event_value in [live["since_pee_minutes"], live["since_food_minutes"], live["since_awake_minutes"]]
    )

    if live["sleep_block"] and live["sleep_block"]["is_sleeping_now"]:
        current_block = {
            "id": "sleep-now",
            "kind": "sleep",
            "phase": "now",
            "title": "Nap time",
            "window_start_utc": live["sleep_block"]["start_time_utc"],
            "window_end_utc": live["sleep_block"]["projected_end_time_utc"],
            "time_label": f"Wake by {local_time_label(live['sleep_block']['projected_end_time_utc'], offset_minutes)}",
            "explanation": "Sleep starts immediately when logged and ends early if wake or another activity is logged.",
            "emphasis": "active",
        }
    else:
        awake_minutes = live["since_awake_minutes"] or 0
        current_block = {
            "id": "awake-now",
            "kind": "awake",
            "phase": "now",
            "title": "Awake stretch",
            "window_start_utc": now.isoformat(),
            "window_end_utc": (now + timedelta(minutes=max(0, schedule["awake_due"] - awake_minutes))).isoformat(),
            "time_label": routine_time_window_label(now, 0, max(0, schedule["awake_due"] - awake_minutes), offset_minutes),
            "explanation": "Recent logs can pull the next potty or nap window forward even when the saved routine stays the same.",
            "emphasis": "active",
        }

    candidate_specs = [
        ("potty", "Potty window", live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"], "Built from time since the last pee."),
        ("food", "Meal window", live["since_food_minutes"], schedule["food_due"], schedule["food_overdue"], "Built from time since the last meal."),
        ("water", "Water check", live["since_water_minutes"], schedule["water_due"], schedule["water_overdue"], "Built from time since the last water log."),
        ("sleep", "Nap window", live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"], "Built from the current awake stretch."),
    ]
    candidates = []
    for kind, title, minutes_since_value, due_value, overdue_value, explanation in candidate_specs:
        since_value = minutes_since_value or 0
        start_minutes = max(0, due_value - since_value)
        end_minutes = max(0, overdue_value - since_value)
        candidates.append(
            build_routine_item(
                item_id=f"{kind}-{title.lower().replace(' ', '-')}",
                kind=kind,
                phase="next",
                title=title,
                start_minutes=start_minutes,
                end_minutes=end_minutes,
                explanation=explanation,
                now=now,
                offset_minutes=offset_minutes,
            )
        )
    candidates.sort(key=lambda item: parse_iso(item["window_start_utc"]) or now)
    next_block = candidates[0] if candidates else None
    agenda = []
    for index, item in enumerate(candidates[:4]):
        agenda.append({**item, "phase": "next" if index == 0 else "later"})

    routine_profile_state = resolved_profile["routine_profile_state"]
    proposal_status = "pending" if proposal else "none"
    if proposal_status == "none":
        if (
            routine_profile_state.get("last_reviewed_recommendation_band_id") == schedule["recommended_age_band_id"]
            and routine_profile_state.get("last_proposal_action") in {"accepted", "rejected"}
        ):
            proposal_status = routine_profile_state["last_proposal_action"]
    if schedule["routine_mode"] == "default_auto":
        source_badge = f"Auto-following {schedule['recommended_age_label']} routine"
    else:
        source_badge = f"Custom routine from {schedule['age_label']}"
    if proposal:
        source_detail = proposal["summary_text"]
    elif has_recent_events:
        source_detail = "Recent logs shift the next window without rewriting the saved routine."
    else:
        source_detail = "No recent logs yet, so the routine is showing the age-based plan."

    return {
        "headline": "Today's rhythm",
        "summary_text": resolved_profile["summary_text"],
        "source_state": {
            "profile_source": schedule["profile_source"],
            "routine_mode": schedule["routine_mode"],
            "guidance_shifted_by_recent_events": has_recent_events,
            "source_badge": source_badge,
            "source_detail": source_detail,
            "proposal_status": proposal_status,
        },
        "current_block": current_block,
        "next_block": next_block,
        "agenda": agenda,
        "plain_language_defaults": [
            f"Potty usually becomes due around every {schedule['pee_due']} to {schedule['pee_overdue']} minutes.",
            f"Awake stretches usually land around {schedule['awake_due']} to {schedule['awake_overdue']} minutes.",
            f"Quick sleep logs use a {schedule['sleep_default']}-minute nap target.",
        ],
    }


def build_routine_editor_state(schedule: Dict[str, Any]) -> Dict[str, Any]:
    simple_fields = []
    for group in SIMPLE_ROUTINE_GROUPS:
        simple_fields.append(
            {
                "id": group["id"],
                "label": group["label"],
                "description": group["description"],
                "fields": [
                    {
                        "id": field_id,
                        "label": ROUTINE_FIELD_LABELS[field_id],
                        "unit": "minutes",
                        "default_value": schedule["defaults"][field_id],
                        "effective_value": schedule[field_id],
                    }
                    for field_id in group["fields"]
                ],
            }
        )
    advanced_fields = [
        {
            "id": field_id,
            "label": ROUTINE_FIELD_LABELS[field_id],
            "unit": "minutes",
            "default_value": schedule["defaults"][field_id],
            "effective_value": schedule[field_id],
        }
        for field_id in ROUTINE_FIELDS
    ]
    return {
        "active_age_band_id": schedule["effective_age_band_id"],
        "active_age_label": schedule["age_label"],
        "routine_mode": schedule["routine_mode"],
        "default_values": schedule["defaults"],
        "effective_values": {field_id: schedule[field_id] for field_id in ROUTINE_FIELDS},
        "last_saved_mode": schedule["last_saved_mode"],
        "simple_fields": simple_fields,
        "advanced_fields": advanced_fields,
    }


def build_advisory(
    key: str,
    title: str,
    reason: str,
    rule_type: str,
    priority: int,
    triggered_by: List[str],
    status: str = "active",
) -> Dict[str, Any]:
    return {
        "advisory_key": key,
        "title": title,
        "reason": reason,
        "rule_type": rule_type,
        "status": status,
        "priority": priority,
        "triggered_by": triggered_by,
        "due_at_utc": None,
        "escalates_at_utc": None,
    }


def active_override_map(settings: Dict[str, Any], now: datetime) -> Dict[str, Dict[str, Any]]:
    overrides: Dict[str, Dict[str, Any]] = {}
    for item in settings.get("advisory_overrides", []):
        key = item.get("advisory_key")
        if not key:
            continue
        expires = parse_iso(item.get("expires_at_utc"))
        if expires and expires <= now:
            continue
        overrides[key] = item
    return overrides


def build_advisory_candidates(events_desc: List[Dict[str, Any]], settings: Dict[str, Any], schedule: Dict[str, Any], live: Dict[str, Any], now: datetime) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    sleep_block = live["sleep_block"]
    if sleep_block and sleep_block["is_sleeping_now"]:
        reason = sleep_block["care_limit_warning"] or sleep_block["recommended_check_reason"]
        rule_type = "care-limit" if sleep_block["care_limit_warning"] else "schedule"
        candidates.append(
            build_advisory(
                advisory_key("sleeping", schedule["context_label"].lower()),
                "Sleeping now",
                reason,
                rule_type,
                10,
                build_triggered_by("schedule", [f"{sleep_block['start_context_label']} sleep block", sleep_block["recommended_check_reason"]]),
            )
        )
        return candidates

    wake_last = find_last(events_desc, "wake")
    potty_after_wake = find_latest_activity_after(events_desc, ["pee", "poop"], (wake_last or {}).get("event_time_utc"))
    if wake_last and live["since_wake_minutes"] is not None and live["since_wake_minutes"] <= 15 and not potty_after_wake:
        candidates.append(
            build_advisory(
                advisory_key("post-wake-potty"),
                "Potty likely due",
                f"Woke up {human_minutes_short(live['since_wake_minutes'])} ago.",
                "behavior-trigger",
                20,
                build_triggered_by("behavior", ["Recent wake event", "Post-wake potty trigger"]),
            )
        )

    food_last = find_last(events_desc, "food")
    potty_after_food = find_latest_activity_after(events_desc, ["pee", "poop"], (food_last or {}).get("event_time_utc"))
    if food_last and live["since_food_minutes"] is not None and schedule["post_food_potty_due"] <= live["since_food_minutes"] and not potty_after_food:
        title = "Potty likely overdue" if live["since_food_minutes"] >= schedule["post_food_potty_overdue"] else "Likely needs potty soon"
        priority = 18 if live["since_food_minutes"] >= schedule["post_food_potty_overdue"] else 22
        candidates.append(
            build_advisory(
                advisory_key("post-food-potty"),
                title,
                f"Ate {human_minutes_short(live['since_food_minutes'])} ago.",
                "behavior-trigger",
                priority,
                build_triggered_by(
                    "behavior",
                    [
                        "Recent meal",
                        f"Post-food potty {human_minutes_short(schedule['post_food_potty_due'])}-{human_minutes_short(schedule['post_food_potty_overdue'])}",
                    ],
                ),
            )
        )

    recent_water = list_recent_activity(events_desc, "water", schedule["post_drink_potty_overdue"], now)
    potty_after_water = find_latest_activity_after(events_desc, ["pee", "poop"], (recent_water or {}).get("event_time_utc"))
    if live["since_water_minutes"] is not None and schedule["post_drink_potty_due"] <= live["since_water_minutes"] <= schedule["post_drink_potty_overdue"]:
        if recent_water and not potty_after_water:
            candidates.append(
                build_advisory(
                    advisory_key("post-drink-potty"),
                    "Potty likely due",
                    f"Drank {human_minutes_short(live['since_water_minutes'])} ago.",
                    "behavior-trigger",
                    24,
                    build_triggered_by("behavior", ["Recent drink", "Post-drink potty trigger"]),
                )
            )

    recent_play = list_recent_activity(events_desc, "play", schedule["post_play_potty_overdue"], now)
    potty_after_play = find_latest_activity_after(events_desc, ["pee", "poop"], (recent_play or {}).get("event_time_utc"))
    if live["since_play_minutes"] is not None and schedule["post_play_potty_due"] <= live["since_play_minutes"] <= schedule["post_play_potty_overdue"]:
        if recent_play and not potty_after_play:
            candidates.append(
                build_advisory(
                    advisory_key("post-play-potty"),
                    "Potty likely due",
                    f"Played {human_minutes_short(live['since_play_minutes'])} ago.",
                    "behavior-trigger",
                    26,
                    build_triggered_by("behavior", ["Recent play", "Post-play potty trigger"]),
                )
            )

    if urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"]) == "overdue":
        candidates.append(
            build_advisory(
                advisory_key("pee-overdue"),
                "Pee break overdue",
                f"Last pee was {human_minutes_short(live['since_pee_minutes'])} ago.",
                "care-limit",
                15,
                build_triggered_by("care-limit", [f"Pee overdue after {human_minutes_short(schedule['pee_overdue'])}"]),
            )
        )
    if urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"]) == "overdue":
        candidates.append(
            build_advisory(
                advisory_key("sleep-overdue"),
                "Needs sleep",
                f"Awake for {human_minutes_short(live['since_awake_minutes'])}.",
                "schedule",
                30,
                build_triggered_by(
                    "schedule",
                    [f"Awake window {human_minutes_short(schedule['awake_due'])}-{human_minutes_short(schedule['awake_overdue'])}"],
                ),
            )
        )
    if urgency(live["since_food_minutes"], schedule["food_due"], schedule["food_overdue"]) == "overdue":
        candidates.append(
            build_advisory(
                advisory_key("food-due"),
                "Food likely due",
                f"Last food was {human_minutes_short(live['since_food_minutes'])} ago.",
                "care-limit",
                35,
                build_triggered_by("care-limit", [f"Food overdue after {human_minutes_short(schedule['food_overdue'])}"]),
            )
        )
    if urgency(live["since_water_minutes"], schedule["water_due"], schedule["water_overdue"]) == "overdue":
        candidates.append(
            build_advisory(
                advisory_key("water-due"),
                "Water likely due",
                f"Last water was {human_minutes_short(live['since_water_minutes'])} ago.",
                "care-limit",
                40,
                build_triggered_by("care-limit", [f"Water overdue after {human_minutes_short(schedule['water_overdue'])}"]),
            )
        )
    if urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"]) == "soon":
        candidates.append(
            build_advisory(
                advisory_key("pee-soon"),
                "Potty soon",
                f"Last pee was {human_minutes_short(live['since_pee_minutes'])} ago.",
                "schedule",
                50,
                build_triggered_by("schedule", [f"Pee due after {human_minutes_short(schedule['pee_due'])}"]),
            )
        )
    if urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"]) == "soon":
        candidates.append(
            build_advisory(
                advisory_key("sleep-soon"),
                "Sleep soon",
                f"Awake for {human_minutes_short(live['since_awake_minutes'])}.",
                "schedule",
                55,
                build_triggered_by("schedule", [f"Awake window due at {human_minutes_short(schedule['awake_due'])}"]),
            )
        )
    if not candidates:
        candidates.append(
            build_advisory(
                advisory_key("all-good"),
                "All good for now",
                "Nothing looks urgent right now.",
                "schedule",
                99,
                build_triggered_by("schedule", ["No active due-soon, overdue, or trigger rules"]),
            )
        )
    return candidates


def build_logic_breakdown(
    events_desc: List[Dict[str, Any]],
    schedule: Dict[str, Any],
    live: Dict[str, Any],
    now: datetime,
    primary_advisory: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    primary_key = primary_advisory.get("advisory_key")

    pee_urgency = urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"])
    potty_detail = "General potty timer is on track."
    if pee_urgency == "soon":
        potty_detail = f"Pee timing reaches due soon at {human_minutes_short(schedule['pee_due'])}."
    elif pee_urgency == "overdue":
        potty_detail = f"Pee timing is past the {human_minutes_short(schedule['pee_overdue'])} overdue mark."
    rows.append(
        {
            "key": "potty-reset",
            "label": "Recent potty reset",
            "status": "ok" if pee_urgency == "ok" else pee_urgency,
            "summary": f"Pee {human_minutes_short(live['since_pee_minutes'])} ago; poop {human_minutes_short(live['since_poop_minutes'])} ago.",
            "detail": potty_detail,
            "is_primary": primary_key in {"pee-overdue", "pee-soon"},
        }
    )

    wake_last = find_last(events_desc, "wake")
    potty_after_wake = find_latest_activity_after(events_desc, ["pee", "poop"], (wake_last or {}).get("event_time_utc"))
    if wake_last and live["since_wake_minutes"] is not None:
        wake_row = {
            "key": "post-wake-potty",
            "label": "After wake potty rule",
            "summary": f"Last wake was {human_minutes_short(live['since_wake_minutes'])} ago.",
            "is_primary": primary_key == "post-wake-potty",
        }
        if potty_after_wake:
            wake_row["status"] = "cleared"
            wake_row["detail"] = f"Cleared by {potty_after_wake['activity']} {human_minutes_short(minutes_since(potty_after_wake.get('event_time_utc'), now))} ago."
        elif live["since_wake_minutes"] <= 15:
            wake_row["status"] = "winner" if wake_row["is_primary"] else "active"
            wake_row["detail"] = "Wake potty reminder stays active for 15 minutes unless a potty event is logged."
        else:
            wake_row["status"] = "idle"
            wake_row["detail"] = "Wake potty reminder only applies for the first 15 minutes after waking."
        rows.append(wake_row)

    food_last = find_last(events_desc, "food")
    potty_after_food = find_latest_activity_after(events_desc, ["pee", "poop"], (food_last or {}).get("event_time_utc"))
    if food_last and live["since_food_minutes"] is not None:
        food_row = {
            "key": "post-food-potty",
            "label": "After food potty rule",
            "summary": f"Last meal was {human_minutes_short(live['since_food_minutes'])} ago.",
            "is_primary": primary_key == "post-food-potty",
        }
        if potty_after_food:
            food_row["status"] = "cleared"
            food_row["detail"] = f"Cleared by {potty_after_food['activity']} {human_minutes_short(minutes_since(potty_after_food.get('event_time_utc'), now))} ago."
        elif live["since_food_minutes"] < schedule["post_food_potty_due"]:
            food_row["status"] = "waiting"
            food_row["detail"] = f"Reminder starts at {human_minutes_short(schedule['post_food_potty_due'])} after a meal."
        elif live["since_food_minutes"] >= schedule["post_food_potty_overdue"]:
            food_row["status"] = "winner" if food_row["is_primary"] else "active"
            food_row["detail"] = (
                f"No pee or poop logged after that meal. The rule escalates after {human_minutes_short(schedule['post_food_potty_overdue'])}."
            )
        else:
            food_row["status"] = "winner" if food_row["is_primary"] else "active"
            food_row["detail"] = (
                f"No pee or poop logged after that meal. The watch window is {human_minutes_short(schedule['post_food_potty_due'])}-"
                f"{human_minutes_short(schedule['post_food_potty_overdue'])} after food."
            )
        rows.append(food_row)

    awake_urgency = urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"])
    awake_detail = f"Sleep window is {human_minutes_short(schedule['awake_due'])}-{human_minutes_short(schedule['awake_overdue'])} awake."
    if awake_urgency == "ok":
        awake_detail = f"On track until roughly {human_minutes_short(schedule['awake_due'])} awake."
    elif awake_urgency == "overdue":
        awake_detail = f"Past the {human_minutes_short(schedule['awake_overdue'])} awake limit."
    rows.append(
        {
            "key": "awake-window",
            "label": "Awake window",
            "status": "winner" if primary_key in {"sleep-overdue", "sleep-soon"} else ("ok" if awake_urgency == "ok" else awake_urgency),
            "summary": f"Awake for {human_minutes_short(live['since_awake_minutes'])}.",
            "detail": awake_detail,
            "is_primary": primary_key in {"sleep-overdue", "sleep-soon"},
        }
    )

    return rows


def apply_advisory_overrides(candidates: List[Dict[str, Any]], settings: Dict[str, Any], now: datetime) -> List[Dict[str, Any]]:
    overrides = active_override_map(settings, now)
    adjusted: List[Dict[str, Any]] = []
    for candidate in candidates:
        override = overrides.get(candidate["advisory_key"])
        if not override:
            adjusted.append(candidate)
            continue
        updated = dict(candidate)
        action = override.get("action")
        if action in {"defer", "dismiss"}:
            updated["status"] = "deferred"
            updated["priority"] += 100
            if override.get("expires_at_utc"):
                updated["reason"] = f"{candidate['reason']} Deferred until {local_time_label(override['expires_at_utc'], settings['timezone_offset_minutes'])}."
        elif action == "acknowledge":
            updated["status"] = "active"
        adjusted.append(updated)
    return adjusted


def build_live_state(settings: Dict[str, Any], events_desc: List[Dict[str, Any]], now: datetime) -> Dict[str, Any]:
    resolved_profile = resolve_routine_profile(settings, now)
    schedule = get_schedule(settings, now)
    schedule_profile = normalize_schedule_profile(settings.get("schedule_profile") or {})
    schedule_profile_source = (
        schedule_profile["source"]
        if schedule_profile["routine_blocks"] or schedule_profile["trigger_rules"] or schedule_profile["care_limits"]
        else "default"
    )
    sleep_block = latest_sleep_block(events_desc, settings)

    live = {
        "since_awake_minutes": current_awake_minutes(events_desc, settings, now),
        "since_pee_minutes": minutes_since((find_last(events_desc, "pee") or {}).get("event_time_utc"), now),
        "since_poop_minutes": minutes_since((find_last(events_desc, "poop") or {}).get("event_time_utc"), now),
        "since_food_minutes": minutes_since((find_last(events_desc, "food") or {}).get("event_time_utc"), now),
        "since_water_minutes": minutes_since((find_last(events_desc, "water") or {}).get("event_time_utc"), now),
        "since_wake_minutes": minutes_since((find_last(events_desc, "wake") or {}).get("event_time_utc"), now),
        "since_play_minutes": minutes_since((find_last(events_desc, "play") or {}).get("event_time_utc"), now),
        "sleep_block": sleep_block,
    }
    awake_anchor_utc = current_state_anchor_utc(events_desc, sleep_block)
    is_sleeping_now = bool(sleep_block and sleep_block["is_sleeping_now"])
    awake_tile_minutes = (
        minutes_since((sleep_block or {}).get("start_time_utc"), now)
        if is_sleeping_now
        else live["since_awake_minutes"]
    )
    awake_tile_urgency = "ok" if is_sleeping_now else urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"])
    awake_tile_label = "Asleep" if is_sleeping_now else "Awake"
    awake_tile_display = human_ago(awake_tile_minutes)
    awake_tile_detail = (
        f"Since {local_time_label(awake_anchor_utc, settings['timezone_offset_minutes'])}"
        if awake_anchor_utc
        else None
    )

    supported_activities = set(settings["activities"])
    tiles = {
        "pee": build_status_tile(
            "pee",
            live["since_pee_minutes"],
            urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"]),
            is_tappable="pee" in supported_activities,
        ),
        "poop": build_status_tile(
            "poop",
            live["since_poop_minutes"],
            urgency(live["since_poop_minutes"], schedule["poop_due"], schedule["poop_overdue"]),
            is_tappable="poop" in supported_activities,
        ),
        "food": build_status_tile(
            "food",
            live["since_food_minutes"],
            urgency(live["since_food_minutes"], schedule["food_due"], schedule["food_overdue"]),
            is_tappable="food" in supported_activities,
        ),
        "water": build_status_tile(
            "water",
            live["since_water_minutes"],
            urgency(live["since_water_minutes"], schedule["water_due"], schedule["water_overdue"]),
            is_tappable="water" in supported_activities,
        ),
        "awake": build_status_tile(
            "awake",
            awake_tile_minutes,
            awake_tile_urgency,
            is_tappable=("sleep" in supported_activities and "wake" in supported_activities),
            label_override=awake_tile_label,
            display_value_override=awake_tile_display,
            detail_text=awake_tile_detail,
            tap_activity_override="wake" if is_sleeping_now else "sleep",
            tap_hint_override="Tap to log",
            show_urgency=False,
        ),
    }

    advisories = apply_advisory_overrides(build_advisory_candidates(events_desc, settings, schedule, live, now), settings, now)
    advisories.sort(key=lambda item: item["priority"])
    primary_advisory = advisories[0]
    logic_breakdown = build_logic_breakdown(events_desc, schedule, live, now, primary_advisory)
    routine_overview = build_routine_overview(settings, resolved_profile, live, now)
    routine_editor = build_routine_editor_state(schedule)
    sleep_projection = {
        "recommended_check_at_utc": sleep_block["recommended_check_time_utc"] if sleep_block else None,
        "recommended_check_reason": sleep_block["recommended_check_reason"] if sleep_block else "Log sleep to project the next guidance checkpoint.",
        "care_limit_warning": sleep_block["care_limit_warning"] if sleep_block else None,
    }

    return {
        **live,
        "tiles": tiles,
        "secondary_quick_actions": [],
        "schedule": schedule,
        "primary_advisory": primary_advisory,
        "active_advisories": advisories,
        "logic_breakdown": logic_breakdown,
        "schedule_profile_summary": {
            "source": schedule_profile_source,
            "active_age_band_id": schedule["age_band_id"],
            "display_label": schedule["age_label"],
        },
        "routine_overview": routine_overview,
        "routine_editor": routine_editor,
        "routine_proposal": resolved_profile["routine_proposal"],
        "sleep_projection": sleep_projection,
        "needs_now": {"title": primary_advisory["title"], "reason": primary_advisory["reason"]},
    }


def dashboard_payload() -> Dict[str, Any]:
    settings = get_settings()
    events = list_events()
    now = utc_now()
    return {
        "type": "snapshot",
        "app_version": APP_VERSION,
        "settings": settings,
        "events": events,
        "server_time_utc": now.isoformat(),
        "live_state": build_live_state(settings, events, now),
    }


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(content=HTML, headers=NO_CACHE_HEADERS)


@app.get("/api/state")
def api_state() -> JSONResponse:
    return JSONResponse(dashboard_payload())


@app.post("/api/events")
async def api_create_event(event: EventIn) -> JSONResponse:
    settings = get_settings()
    allowed = set(settings["activities"])
    if event.activity not in allowed:
        return JSONResponse({"error": "Unknown activity"}, status_code=400)
    event_time = parse_iso(event.event_time_utc) or utc_now()
    duration = event.duration_minutes
    is_accident = normalize_is_accident(event.activity, event.is_accident)
    if event.activity == "play" and duration is None:
        duration = 20
    with get_db() as conn:
        conn.execute(
            "INSERT INTO events (activity, actor, event_time_utc, duration_minutes, is_accident, note, created_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event.activity, event.actor.strip(), event_time.isoformat(), duration, int(is_accident), (event.note or "").strip(), utc_now_iso()),
        )
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload)


@app.put("/api/events/{event_id}")
async def api_update_event(event_id: int, event: EventUpdate) -> JSONResponse:
    settings = get_settings()
    if event.activity not in set(settings["activities"]):
        return JSONResponse({"error": "Unknown activity"}, status_code=400)
    event_time = parse_iso(event.event_time_utc)
    if not event_time:
        return JSONResponse({"error": "Invalid time"}, status_code=400)
    is_accident = normalize_is_accident(event.activity, event.is_accident)
    with get_db() as conn:
        exists = conn.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not exists:
            return JSONResponse({"error": "Event not found"}, status_code=404)
        conn.execute(
            """
            UPDATE events
            SET activity = ?, actor = ?, event_time_utc = ?, duration_minutes = ?, is_accident = ?, note = ?
            WHERE id = ?
            """,
            (event.activity, event.actor.strip(), event_time.isoformat(), event.duration_minutes, int(is_accident), (event.note or "").strip(), event_id),
        )
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload)


@app.delete("/api/events/{event_id}")
async def api_delete_event(event_id: int) -> JSONResponse:
    with get_db() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload)


@app.post("/api/settings")
async def api_settings(settings: SettingsIn) -> JSONResponse:
    birth = settings.puppy_birth_date or ""
    if birth and not parse_date(birth):
        return JSONResponse({"error": "Invalid birth date"}, status_code=400)
    activities = normalize_activities(settings.activities)
    household_members = normalize_household_members(settings.household_members)
    values = {
        "puppy_name": settings.puppy_name.strip(),
        "household_name": settings.household_name.strip(),
        "timezone_offset_minutes": str(settings.timezone_offset_minutes),
        "activities": json.dumps(activities),
        "household_members": json.dumps(household_members),
        "puppy_birth_date": birth,
    }
    with get_db() as conn:
        for key, value in values.items():
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload)


@app.get("/api/schedule-profile")
def api_schedule_profile() -> JSONResponse:
    settings = get_settings()
    now = utc_now()
    return JSONResponse(build_schedule_profile_payload(settings, now))


@app.put("/api/schedule-profile")
async def api_update_schedule_profile(profile: ScheduleProfileIn) -> JSONResponse:
    normalized = normalize_schedule_profile(profile.model_dump())
    error = validate_schedule_profile(normalized)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    save_json_setting(SCHEDULE_PROFILE_KEY, normalized)
    snapshot = dashboard_payload()
    settings = get_settings()
    profile_payload = build_schedule_profile_payload(settings, utc_now())
    await manager.broadcast_json(snapshot)
    return JSONResponse({"schedule_profile": profile_payload, "snapshot": snapshot})


@app.post("/api/advisories/action")
async def api_advisory_action(action: AdvisoryActionIn) -> JSONResponse:
    settings = get_settings()
    now = utc_now()
    overrides = [
        item for item in settings.get("advisory_overrides", [])
        if item.get("advisory_key") != action.advisory_key
    ]
    expires_at = None
    if action.action == "defer":
        expires_at = (now + timedelta(minutes=action.defer_minutes or DEFAULT_DEFER_MINUTES)).isoformat()
    overrides.append(
        {
            "advisory_key": action.advisory_key,
            "action": action.action,
            "expires_at_utc": expires_at,
            "created_at_utc": now.isoformat(),
        }
    )
    save_json_setting(ADVISORY_OVERRIDES_KEY, overrides)
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload)


@app.put("/api/routine-profile")
async def api_save_routine_profile(routine_profile: RoutineProfileIn) -> JSONResponse:
    if routine_profile.save_mode not in {"simple", "advanced"}:
        return JSONResponse({"error": "Invalid save mode"}, status_code=400, headers=NO_CACHE_HEADERS)
    settings = get_settings()
    base_band = get_schedule_band_by_id(routine_profile.base_age_band_id)
    if not base_band:
        return JSONResponse({"error": "Unknown age band"}, status_code=400, headers=NO_CACHE_HEADERS)
    custom_values, error = validate_custom_routine_values(routine_profile.custom_values)
    if error:
        return JSONResponse({"error": error}, status_code=400, headers=NO_CACHE_HEADERS)
    resolved_profile = resolve_routine_profile(settings, utc_now())
    routine_profile_state = normalize_routine_profile_state(settings.get("routine_profile_state"))
    routine_profile_state["routine_mode"] = "custom_manual"
    routine_profile_state["last_reviewed_recommendation_band_id"] = resolved_profile["recommended_band"]["id"]
    routine_profile_state["last_proposal_action"] = None
    routine_profile_state["custom_profile"] = {
        "base_age_band_id": base_band["id"],
        "updated_at_utc": utc_now_iso(),
        "last_saved_mode": routine_profile.save_mode,
        "custom_values": custom_values,
    }
    save_routine_profile_state(routine_profile_state)
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload, headers=NO_CACHE_HEADERS)


@app.delete("/api/routine-profile")
async def api_reset_routine_profile() -> JSONResponse:
    settings = get_settings()
    recommended_band = resolve_routine_profile(settings, utc_now())["recommended_band"]
    routine_profile_state = {
        "version": 1,
        "routine_mode": "default_auto",
        "last_reviewed_recommendation_band_id": recommended_band["id"],
        "last_proposal_action": None,
        "custom_profile": None,
    }
    save_routine_profile_state(routine_profile_state)
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload, headers=NO_CACHE_HEADERS)


@app.post("/api/routine-proposal/{proposal_id}/decision")
async def api_routine_proposal_decision(proposal_id: str, decision: RoutineProposalDecisionIn) -> JSONResponse:
    if decision.action not in {"accept", "reject"}:
        return JSONResponse({"error": "Invalid proposal action"}, status_code=400, headers=NO_CACHE_HEADERS)
    settings = get_settings()
    resolved_profile = resolve_routine_profile(settings, utc_now())
    proposal = resolved_profile["routine_proposal"]
    if not proposal or proposal["proposal_id"] != proposal_id:
        return JSONResponse({"error": "Routine proposal not found"}, status_code=404, headers=NO_CACHE_HEADERS)
    routine_profile_state = normalize_routine_profile_state(settings.get("routine_profile_state"))
    if decision.action == "accept":
        routine_profile_state = {
            "version": 1,
            "routine_mode": "default_auto",
            "last_reviewed_recommendation_band_id": resolved_profile["recommended_band"]["id"],
            "last_proposal_action": "accepted",
            "custom_profile": None,
        }
    else:
        routine_profile_state["last_reviewed_recommendation_band_id"] = resolved_profile["recommended_band"]["id"]
        routine_profile_state["last_proposal_action"] = "rejected"
    save_routine_profile_state(routine_profile_state)
    payload = dashboard_payload()
    await manager.broadcast_json(payload)
    return JSONResponse(payload, headers=NO_CACHE_HEADERS)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json(dashboard_payload())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


HTML = r'''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>Puppy Coordinator</title>
  <style>
    :root{
      --bg:#09111f;
      --card:#101a2b;
      --card-strong:#152238;
      --text:#e5eefc;
      --muted:#91a4c2;
      --border:#22324d;
      --blue:#4f8cff;
      --blue-dark:#3b76e6;
      --green-bg:#0f2d1d;
      --green-border:#34d399;
      --green-text:#b9f7d2;
      --yellow-bg:#33290d;
      --yellow-border:#f5c451;
      --yellow-text:#fde7a6;
      --red-bg:#34161d;
      --red-border:#fb7185;
      --red-text:#fecdd3;
      --gray-bg:#172236;
      --gray-border:#5b6f92;
      --gray-text:#d7e3f7;
      --input:#0c1525;
      --input-border:#31425f;
      --pill-bg:#1d3557;
      --pill-text:#cfe0ff;
      --toast-bg:#153423;
      --toast-border:#2f855a;
      --toast-text:#d7ffe8;
      --shadow:0 18px 40px rgba(0,0,0,.34);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    *{box-sizing:border-box}
    body{margin:0;background:radial-gradient(circle at top, #172842 0%, var(--bg) 48%, #060b14 100%);color:var(--text)}
    .wrap{max-width:960px;margin:0 auto;padding:16px 14px 48px}
    .card{background:var(--card);border:1px solid var(--border);border-radius:16px;box-shadow:var(--shadow);padding:14px}
    .header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px}
    h1{font-size:1.35rem;margin:0}
    .sub{color:var(--muted);font-size:.95rem;margin-top:4px}
    .live{display:flex;align-items:center;gap:8px;font-size:.86rem;color:var(--muted)}
    .dot{width:10px;height:10px;border-radius:999px;background:#5b6f92}
    .dot.online{background:#22c55e}
    .banner{margin-bottom:14px;padding:14px 16px;border-radius:16px;background:linear-gradient(135deg, #18345f, #10213d);border:1px solid #40639a}
    .banner-title{font-size:1.05rem;font-weight:800}
    .banner-reason{color:#c7dcff;margin-top:4px;font-size:.95rem}
    .tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:14px}
    .tile{border-radius:16px;padding:12px;border:1px solid var(--border);position:relative;min-height:118px;display:flex;flex-direction:column;align-items:flex-start;width:100%;text-align:left}
    .tile .label{font-size:.8rem;font-weight:700;letter-spacing:.02em}
    .tile .value{font-size:1.35rem;font-weight:800;margin-top:6px}
    .tile .meta{font-size:.78rem;margin-top:6px;opacity:.9}
    .tile-hint{margin-top:auto;padding-top:10px;font-size:.72rem;font-weight:700;letter-spacing:.01em;opacity:.92}
    .tile-button{appearance:none;cursor:pointer}
    .tile-button:focus-visible{outline:2px solid #cfe0ff;outline-offset:2px}
    .tile-button.pending,.tile-button[disabled]{cursor:wait;opacity:.78}
    .tile-readonly{cursor:default}
    .tile.on-track{background:var(--green-bg);border-color:var(--green-border);color:var(--green-text)}
    .tile.soon{background:var(--yellow-bg);border-color:var(--yellow-border);color:var(--yellow-text)}
    .tile.overdue{background:var(--red-bg);border-color:var(--red-border);color:var(--red-text)}
    .tile.unknown{background:var(--gray-bg);border-color:var(--gray-border);color:var(--gray-text)}
    .tile.awake-wide{grid-column:span 2}
    .section-title{font-size:1rem;font-weight:800;margin:0 0 10px}
    .actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
    .btn{appearance:none;border:0;border-radius:14px;padding:12px 10px;font-weight:800;font-size:.96rem;cursor:pointer}
    .btn-blue{background:var(--blue);color:white}
    .btn-blue:active{transform:scale(.98);background:var(--blue-dark)}
    .btn-small{padding:8px 10px;font-size:.86rem;border-radius:12px}
    .btn[disabled]{cursor:not-allowed;opacity:.4}
    .btn-icon{width:2.5rem;min-width:2.5rem;height:2.5rem;padding:0;font-size:1rem;line-height:1;display:inline-flex;align-items:center;justify-content:center;background:var(--card-strong);color:var(--text);border:1px solid var(--border)}
    .toast{position:sticky;top:8px;z-index:5;margin-bottom:10px;display:none;padding:10px 12px;border-radius:12px;background:var(--toast-bg);color:var(--toast-text);border:1px solid var(--toast-border)}
    .toast.error{background:#40202b;color:#ffc7d1;border-color:#7f3344}
    .toast.show{display:block}
    .row{display:flex;align-items:center;justify-content:space-between;gap:10px}
    .row.wrap{flex-wrap:wrap}
    .event-list{display:grid;gap:10px}
    .event{border:1px solid var(--border);border-radius:14px;padding:12px;background:var(--card-strong)}
    .event.flash{animation:flash 1.4s ease}
    @keyframes flash{0%{background:#18345f}100%{background:var(--card-strong)}}
    .event-top{display:flex;align-items:center;justify-content:space-between;gap:8px}
    .pill{display:inline-block;border-radius:999px;background:var(--pill-bg);color:var(--pill-text);padding:4px 8px;font-size:.75rem;font-weight:700}
    .pill-accident{background:#43202b;color:#ffc5d0}
    .small{font-size:.85rem}
    .muted{color:var(--muted)}
    details{margin-top:14px}
    details.card{overflow:hidden}
    summary{cursor:pointer;font-weight:800}
    .settings-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
    .settings-grid > div,.edit-grid > div,.editor-grid > div{min-width:0}
    label{font-size:.82rem;font-weight:700;color:var(--muted);display:block;margin-bottom:6px}
    input, select, textarea{width:100%;max-width:100%;min-width:0;box-sizing:border-box;padding:10px 12px;border-radius:12px;border:1px solid var(--input-border);font:inherit;background:var(--input);color:var(--text)}
    input::placeholder, textarea::placeholder{color:#70829f}
    textarea{min-height:84px;resize:vertical}
    .edit-panel{display:none;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}
    .edit-panel.open{display:block}
    .edit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .datetime-pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,8.25rem);gap:8px;align-items:end;overflow:hidden}
    .datetime-pair > *{min-width:0;max-width:100%;justify-self:stretch}
    .datetime-pair .time-box{min-width:0}
    .datetime-pair input{min-width:0;max-width:100%;overflow:hidden}
    input[type="date"],input[type="time"],input[type="datetime-local"]{display:block;width:100%;inline-size:100%;max-width:100%;min-width:0;box-sizing:border-box;background-clip:padding-box;-webkit-appearance:none;appearance:none;line-height:1.2}
    input[type="date"]::-webkit-date-and-time-value,input[type="time"]::-webkit-date-and-time-value,input[type="datetime-local"]::-webkit-date-and-time-value{min-width:0;text-align:left}
    input[type="date"]::-webkit-datetime-edit,input[type="time"]::-webkit-datetime-edit,input[type="datetime-local"]::-webkit-datetime-edit{padding:0;min-width:0;max-width:100%;display:block}
    input[type="date"]::-webkit-datetime-edit-fields-wrapper,input[type="time"]::-webkit-datetime-edit-fields-wrapper,input[type="datetime-local"]::-webkit-datetime-edit-fields-wrapper{padding:0;min-width:0;max-width:100%;display:flex}
    .checkbox-row{display:flex;align-items:center;gap:10px;min-height:42px}
    .checkbox-row input{width:1.05rem;height:1.05rem;accent-color:var(--blue)}
    .checkbox-chip{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:12px;background:var(--card-strong);border:1px solid var(--border);color:var(--text)}
    .checkbox-chip input{width:1.05rem;height:1.05rem;accent-color:var(--blue)}
    .actions-inline{display:flex;gap:8px;align-items:center}
    .log-nav{display:grid;grid-template-columns:2.5rem 5.75rem 2.5rem;align-items:center;justify-items:center;gap:8px}
    .btn-ghost{background:var(--card-strong);color:#c9dcff;border:1px solid var(--border)}
    .btn-danger{background:#40202b;color:#ffc7d1}
    .schedule-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
    .schedule-item{padding:10px;border-radius:12px;background:var(--card-strong);border:1px solid var(--border)}
    .routine-badge{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;background:#173253;border:1px solid #40639a;color:#d7e7ff;font-size:.78rem;font-weight:700}
    .routine-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
    .routine-panel{margin-top:12px;padding:12px;border-radius:12px;background:var(--card-strong);border:1px solid var(--border)}
    .routine-diff{display:grid;gap:8px;margin-top:10px}
    .routine-diff-item{padding:10px;border-radius:12px;background:rgba(255,255,255,.02);border:1px solid var(--border)}
    .routine-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
    .routine-group{padding:12px;border-radius:12px;background:rgba(255,255,255,.02);border:1px solid var(--border)}
    .routine-group h4{margin:0 0 6px;font-size:.95rem}
    .hidden{display:none !important}
    .editor-stack{display:grid;gap:10px;margin-top:10px}
    .editor-card{padding:12px;border-radius:12px;background:var(--card-strong);border:1px solid var(--border);min-width:0}
    .editor-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:10px}
    .source-chip{display:inline-flex;align-items:center;padding:2px 8px;border-radius:999px;border:1px solid var(--border);font-size:.74rem;color:var(--muted)}
    .routine-meta{display:flex;align-items:center;gap:8px;justify-content:space-between;flex-wrap:wrap}
    .log-day{width:5.75rem;font-size:.92rem;font-weight:700;color:var(--muted);text-align:center;font-variant-numeric:tabular-nums}
    .footer-version{margin-top:18px;text-align:center;font-size:.82rem;color:var(--muted)}
    @media (max-width:760px){
      .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
      .actions{grid-template-columns:repeat(2,minmax(0,1fr))}
      .settings-grid,.edit-grid,.schedule-list,.editor-grid,.routine-fields{grid-template-columns:1fr}
      .datetime-pair{grid-template-columns:1fr}
      .wrap{padding:12px 12px 40px}
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div>
        <h1 id="title">Puppy Coordinator</h1>
        <div class="sub" id="subtitle">Shared puppy log</div>
      </div>
      <div class="live"><span id="ws-dot" class="dot"></span><span id="ws-status">Connecting</span></div>
    </div>

    <div id="toast" class="toast"></div>

    <div class="banner card">
      <div class="banner-title" id="needs-title">All good for now</div>
      <div class="banner-reason" id="needs-reason">Nothing looks urgent right now</div>
    </div>

    <div id="quick-stats" class="tiles"></div>

    <details class="card">
      <summary>&#9881; Settings</summary>
      <form id="settings-form">
        <div class="settings-grid">
          <div>
            <label>Puppy name</label>
            <input id="puppy-name" maxlength="50">
          </div>
          <div>
            <label>Household name</label>
            <input id="household-name" maxlength="50">
          </div>
          <div>
            <label>Birth date</label>
            <input id="puppy-birth-date" type="date">
          </div>
          <div>
            <label>Household members</label>
            <input id="household-members">
          </div>
        </div>
        <div style="margin-top:10px">
          <button class="btn btn-blue" type="submit">Save settings</button>
        </div>
      </form>
      <div class="routine-panel" style="margin-top:14px">
        <div class="section-title" style="margin:0">Schedule and logic</div>
        <div id="schedule-blurb" class="small muted" style="margin-top:10px"></div>
        <div id="schedule-list" class="schedule-list"></div>
        <div class="small muted" style="margin-top:10px">
          The app shows the active age band, schedule guardrails, recent behavior triggers, and passive sleep guidance.
          Sleep is logged as a start-only event. Wake or later activity closes the block, and overnight potty limits are emphasized when they matter.
        </div>
      </div>
      <div class="routine-panel" style="margin-top:14px">
        <div class="section-title" style="margin:0">Expected routine</div>
        <div id="routine-blurb" class="small muted" style="margin-top:10px"></div>
        <div id="routine-list" class="schedule-list"></div>
        <div id="routine-proposal" class="routine-panel hidden"></div>
        <div class="routine-actions">
          <button id="routine-adjust-btn" class="btn btn-blue btn-small" type="button">Adjust routine</button>
          <button id="routine-advanced-btn" class="btn btn-ghost btn-small" type="button">Advanced editing</button>
          <button id="routine-reset-btn" class="btn btn-ghost btn-small hidden" type="button">Reset to age defaults</button>
        </div>
        <div id="routine-simple-editor" class="routine-panel hidden"></div>
        <div id="routine-advanced-editor" class="routine-panel hidden"></div>
      </div>
    </details>

    <div class="card" style="margin-top:14px;margin-bottom:14px">
      <div class="row wrap" style="margin-bottom:10px">
        <div class="section-title" style="margin:0">Recent activity</div>
        <div class="log-nav">
          <button id="log-older" class="btn btn-small btn-icon" type="button" aria-label="Earlier days" title="Earlier days">&laquo;</button>
          <div id="log-day-label" class="log-day">Today</div>
          <button id="log-newer" class="btn btn-small btn-icon" type="button" aria-label="Newer days" title="Newer days">&raquo;</button>
        </div>
      </div>
      <div id="event-list" class="event-list"></div>
    </div>

    <div id="app-version" class="footer-version"></div>
  </div>

  <script>
    let state = null;
    let ws = null;
    let lastSavedId = null;
    let currentLogDayIndex = 0;
    const pendingActivities = new Set();

    const els = {
      title: document.getElementById('title'),
      subtitle: document.getElementById('subtitle'),
      wsDot: document.getElementById('ws-dot'),
      wsStatus: document.getElementById('ws-status'),
      toast: document.getElementById('toast'),
      quickStats: document.getElementById('quick-stats'),
      eventList: document.getElementById('event-list'),
      logNewer: document.getElementById('log-newer'),
      logOlder: document.getElementById('log-older'),
      logDayLabel: document.getElementById('log-day-label'),
      appVersion: document.getElementById('app-version'),
      needsTitle: document.getElementById('needs-title'),
      needsReason: document.getElementById('needs-reason'),
      settingsForm: document.getElementById('settings-form'),
      puppyName: document.getElementById('puppy-name'),
      householdName: document.getElementById('household-name'),
      puppyBirthDate: document.getElementById('puppy-birth-date'),
      householdMembers: document.getElementById('household-members'),
      scheduleBlurb: document.getElementById('schedule-blurb'),
      scheduleList: document.getElementById('schedule-list'),
      routineBlurb: document.getElementById('routine-blurb'),
      routineList: document.getElementById('routine-list'),
      routineProposal: document.getElementById('routine-proposal'),
      routineAdjustBtn: document.getElementById('routine-adjust-btn'),
      routineAdvancedBtn: document.getElementById('routine-advanced-btn'),
      routineResetBtn: document.getElementById('routine-reset-btn'),
      routineSimpleEditor: document.getElementById('routine-simple-editor'),
      routineAdvancedEditor: document.getElementById('routine-advanced-editor')
    };

    function escapeHtml(value) {
      return String(value || '')
        .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
    }

    function parseUtc(iso) {
      return iso ? new Date(iso) : null;
    }

    function humanMinutesShort(minutes) {
      if (minutes === null || minutes === undefined) return 'never';
      if (minutes < 1) return 'now';
      if (minutes < 60) return `${minutes}m`;
      const h = Math.floor(minutes / 60);
      const m = minutes % 60;
      if (h < 24) return m ? `${h}h ${m}m` : `${h}h`;
      const d = Math.floor(h / 24);
      const rh = h % 24;
      return rh ? `${d}d ${rh}h` : `${d}d`;
    }

    function humanAgo(minutes) {
      if (minutes === null || minutes === undefined) return 'No entries yet';
      if (minutes < 1) return 'just now';
      return `${humanMinutesShort(minutes)} ago`;
    }

    function editorMinutesHint(minutes) {
      const value = Number(minutes || 0);
      if (!Number.isFinite(value) || value <= 0) return '';
      return humanMinutesShort(value);
    }

    function formatWhen(iso) {
      const d = parseUtc(iso);
      if (!d) return 'Unknown time';
      return d.toLocaleString([], { month:'numeric', day:'numeric', hour:'numeric', minute:'2-digit' });
    }

    function toLocalInputValue(date = new Date()) {
      const off = date.getTimezoneOffset();
      const local = new Date(date.getTime() - off * 60000);
      return local.toISOString().slice(0, 16);
    }

    function localDateValue(date = new Date()) {
      return toLocalInputValue(date).slice(0, 10);
    }

    function localTimeValue(date = new Date()) {
      return toLocalInputValue(date).slice(11, 16);
    }

    function splitLocalDateTime(date) {
      const value = toLocalInputValue(date || new Date());
      return { date: value.slice(0, 10), time: value.slice(11, 16) };
    }

    function normalizeDateInput(value) {
      const match = String(value || '').trim().match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
      if (!match) return null;
      const year = Number(match[1]);
      const month = Number(match[2]);
      const day = Number(match[3]);
      const candidate = new Date(year, month - 1, day);
      if (
        Number.isNaN(candidate.getTime())
        || candidate.getFullYear() !== year
        || candidate.getMonth() !== month - 1
        || candidate.getDate() !== day
      ) return null;
      return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    function normalizeTimeInput(value) {
      const match = String(value || '').trim().match(/^(\d{1,2}):(\d{1,2})$/);
      if (!match) return null;
      const hour = Number(match[1]);
      const minute = Number(match[2]);
      if (!Number.isInteger(hour) || !Number.isInteger(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
      return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
    }

    function combineLocalDateTime(dateValue, timeValue) {
      const safeDate = normalizeDateInput(dateValue || localDateValue());
      const safeTime = normalizeTimeInput(timeValue || '12:00');
      if (!safeDate || !safeTime) return null;
      const [year, month, day] = safeDate.split('-').map(Number);
      const [hour, minute] = safeTime.split(':').map(Number);
      const local = new Date(year, month - 1, day, hour, minute, 0, 0);
      if (Number.isNaN(local.getTime())) return null;
      return local;
    }

    function canMarkAccident(activity) {
      return activity === 'pee' || activity === 'poop';
    }

    function statusMeta(key, live) {
      if (key === 'sleep') {
        const block = live.sleep_block;
        if (!block) return { value: 'No sleep logged yet' };
        if (block.is_sleeping_now) return { value: `Asleep ${humanMinutesShort(block.actual_duration_minutes)}` };
        return { value: `${humanMinutesShort(block.actual_duration_minutes)} sleep` };
      }
      const map = {
        pee: live.since_pee_minutes,
        poop: live.since_poop_minutes,
        food: live.since_food_minutes,
        water: live.since_water_minutes,
        awake: live.since_awake_minutes
      };
      return { value: humanAgo(map[key]) };
    }

    function tileClass(key, urgency) {
      const urgencyClass = urgency === 'overdue' ? 'overdue' : urgency === 'soon' ? 'soon' : urgency === 'unknown' ? 'unknown' : 'on-track';
      return `tile ${urgencyClass}`;
    }

    function tileAriaLabel(tile, isPending) {
      const parts = [tile.label, tile.display_value];
      if (tile.detail_text) parts.push(tile.detail_text);
      parts.push(tile.urgency_label);
      if (isPending) parts.push('Logging now');
      else if (tile.tap_hint) parts.push(tile.tap_hint);
      else if (tile.readonly_reason) parts.push(tile.readonly_reason);
      return parts.join('. ');
    }

    function renderStats() {
      const order = ['pee', 'poop', 'food', 'water', 'awake'];
      els.quickStats.innerHTML = order.map(key => {
        const tile = state.live_state.tiles[key];
        const urgency = tile ? tile.urgency : 'unknown';
        const extraClass = key === 'awake' ? ' awake-wide' : '';
        const isPending = Boolean(tile?.tap_activity) && pendingActivities.has(tile.tap_activity);
        const hint = isPending ? 'Logging...' : tile?.tap_hint;
        const showUrgency = tile?.show_urgency !== false;
        const body = `
          <div class="label">${escapeHtml(tile?.label || key)}</div>
          <div class="value">${escapeHtml(tile?.display_value || 'No entries yet')}</div>
          ${tile?.detail_text ? `<div class="meta">${escapeHtml(tile.detail_text)}</div>` : ''}
          ${showUrgency ? `<div class="meta"><strong>${escapeHtml(tile?.urgency_label || 'On track')}</strong></div>` : ''}
          ${hint ? `<div class="tile-hint">${escapeHtml(hint)}</div>` : ''}
        `;
        if (tile?.is_tappable && tile.tap_activity) {
          return `
            <button class="${tileClass(key, urgency)} tile-button${isPending ? ' pending' : ''}${extraClass}" type="button" ${isPending ? 'disabled' : ''} onclick="quickLog('${tile.tap_activity}', 'tile')" aria-label="${escapeHtml(tileAriaLabel(tile, isPending))}">
              ${body}
            </button>
          `;
        }
        return `
          <div class="${tileClass(key, urgency)} tile-readonly${extraClass}" aria-label="${escapeHtml(tileAriaLabel(tile, false))}">
            ${body}
          </div>
        `;
      }).join('');
    }

    function renderBanner() {
      const advisory = state.live_state.primary_advisory || state.live_state.needs_now;
      const driverText = advisory.triggered_by?.length ? ` Triggered by ${advisory.triggered_by.join('; ')}.` : '';
      const statusText = advisory.status && advisory.status !== 'active' ? ` Status: ${advisory.status}.` : '';
      els.needsTitle.textContent = advisory.title;
      els.needsReason.textContent = `${advisory.reason}${driverText}${statusText}`;
    }

    function describeSleepEvent(event) {
      if (!event || event.activity !== 'sleep') return '';
      if (event.duration_minutes) {
        return `Legacy sleep block planned for ${humanMinutesShort(Number(event.duration_minutes))}.`;
      }
      return 'Sleep start logged. Wake or the next activity will close the block.';
    }

    function eventDayKey(event) {
      const when = parseUtc(event.event_time_utc);
      if (!when) return 'unknown';
      const year = when.getFullYear();
      const month = String(when.getMonth() + 1).padStart(2, '0');
      const day = String(when.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }

    function eventDayLabel(dayKey) {
      if (dayKey === 'unknown') return 'Unknown day';
      const date = new Date(`${dayKey}T12:00:00`);
      return date.toLocaleDateString([], { month:'short', day:'numeric' });
    }

    function groupedEventsByDay() {
      const groups = [];
      for (const event of state.events) {
        const dayKey = eventDayKey(event);
        const last = groups[groups.length - 1];
        if (!last || last.dayKey !== dayKey) groups.push({ dayKey, events: [event] });
        else last.events.push(event);
      }
      return groups;
    }

    function renderEvents() {
      const groups = groupedEventsByDay();
      if (currentLogDayIndex > Math.max(groups.length - 1, 0)) currentLogDayIndex = 0;
      const activeGroup = groups[currentLogDayIndex];
      els.logDayLabel.textContent = activeGroup ? eventDayLabel(activeGroup.dayKey) : 'No activity yet';
      els.logNewer.disabled = currentLogDayIndex <= 0;
      els.logOlder.disabled = currentLogDayIndex >= groups.length - 1;

      els.eventList.innerHTML = (activeGroup?.events || []).map(event => `
        <div class="event ${lastSavedId === event.id ? 'flash' : ''}" id="event-${event.id}">
          <div class="event-top">
            <div>
              <span class="pill">${escapeHtml(event.activity)}</span>
              ${event.is_accident ? '<span class="pill pill-accident" style="margin-left:6px">Accident</span>' : ''}
              <strong style="margin-left:8px">${escapeHtml(event.actor)}</strong>
            </div>
            <div class="actions-inline">
              <button class="btn btn-small btn-ghost" type="button" onclick="toggleEdit(${event.id})">Edit</button>
              <button class="btn btn-small btn-danger" type="button" onclick="deleteEvent(${event.id})">Delete</button>
            </div>
          </div>
          <div class="small muted" style="margin-top:8px">${formatWhen(event.event_time_utc)}</div>
          ${event.note ? `<div class="small" style="margin-top:8px">${escapeHtml(event.note)}</div>` : ''}
          ${event.activity === 'sleep' ? `<div class="small muted" style="margin-top:6px">${escapeHtml(describeSleepEvent(event))}</div>` : ''}
          <div id="edit-${event.id}" class="edit-panel">
            <div class="edit-grid">
              <div>
                <label>Activity</label>
                <select id="edit-activity-${event.id}">${state.settings.activities.map(a => `<option value="${escapeHtml(a)}" ${a === event.activity ? 'selected' : ''}>${escapeHtml(a)}</option>`).join('')}</select>
              </div>
              <div>
                <label>Actor</label>
                <select id="edit-actor-${event.id}">${state.settings.household_members.map(a => `<option value="${escapeHtml(a)}" ${a === event.actor ? 'selected' : ''}>${escapeHtml(a)}</option>`).join('')}</select>
              </div>
              <div>
                <label>When</label>
                <div class="datetime-pair">
                  <input id="edit-date-${event.id}" type="date" value="${splitLocalDateTime(parseUtc(event.event_time_utc) || new Date()).date}">
                  <input id="edit-time-${event.id}" class="time-box" type="time" value="${splitLocalDateTime(parseUtc(event.event_time_utc) || new Date()).time}">
                </div>
              </div>
              <div id="edit-accident-wrap-${event.id}" class="checkbox-row" style="${canMarkAccident(event.activity) ? '' : 'visibility:hidden'}">
                <input id="edit-accident-${event.id}" type="checkbox" ${event.is_accident ? 'checked' : ''}>
                <label for="edit-accident-${event.id}" style="margin:0;color:var(--text)">Accident</label>
              </div>
              <div style="grid-column:1/-1">
                <label>Note</label>
                <textarea id="edit-note-${event.id}">${escapeHtml(event.note || '')}</textarea>
              </div>
            </div>
            <div class="actions-inline" style="margin-top:10px">
              <button class="btn btn-small btn-blue" type="button" onclick="saveEdit(${event.id})">Save</button>
              <button class="btn btn-small btn-ghost" type="button" onclick="toggleEdit(${event.id}, false)">Cancel</button>
            </div>
          </div>
        </div>
      `).join('') || '<div class="small muted">No activity yet.</div>';

      (activeGroup?.events || []).forEach(event => {
        const activitySelect = document.getElementById(`edit-activity-${event.id}`);
        if (activitySelect) {
          activitySelect.addEventListener('change', () => {
            const accidentWrap = document.getElementById(`edit-accident-wrap-${event.id}`);
            const accidentInput = document.getElementById(`edit-accident-${event.id}`);
            accidentWrap.style.visibility = canMarkAccident(activitySelect.value) ? 'visible' : 'hidden';
            if (!canMarkAccident(activitySelect.value)) accidentInput.checked = false;
          });
        }
      });
      if (lastSavedId) {
        const el = document.getElementById(`event-${lastSavedId}`);
        if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        setTimeout(() => { lastSavedId = null; renderEvents(); }, 1600);
      }
    }

    function renderSettings() {
      els.title.textContent = `${state.settings.puppy_name} Coordinator`;
      els.subtitle.textContent = `Shared puppy log for ${state.settings.household_name}`;
      els.appVersion.textContent = `Version ${state.app_version || 'unknown'}`;
      els.puppyName.value = state.settings.puppy_name;
      els.householdName.value = state.settings.household_name;
      els.puppyBirthDate.value = state.settings.puppy_birth_date || '';
      els.householdMembers.value = state.settings.household_members.join(', ');
    }

    function getRoutineFieldIds() {
      return (state.live_state.routine_editor?.advanced_fields || []).map(field => field.id);
    }

    function renderSimpleRoutineEditor() {
      const editor = state.live_state.routine_editor;
      const groups = editor?.simple_fields || [];
      els.routineSimpleEditor.innerHTML = `
        <div class="section-title" style="margin:0">Simple routine changes</div>
        <div class="small muted" style="margin-top:4px">Adjust the most common routine changes without opening every threshold.</div>
        <div class="routine-fields">
          ${groups.map(group => `
            <div class="routine-group">
              <h4>${escapeHtml(group.label)}</h4>
              <div class="small muted">${escapeHtml(group.description || '')}</div>
              <div class="routine-fields">
                ${group.fields.map(field => `
                  <div>
                    <label>${escapeHtml(field.label)}</label>
                    <input id="routine-simple-${field.id}" type="number" min="1" max="1440" value="${field.effective_value}">
                    <div class="small muted" style="margin-top:4px">Default ${field.default_value}m</div>
                  </div>
                `).join('')}
              </div>
            </div>
          `).join('')}
        </div>
        <div class="routine-actions">
          <button class="btn btn-blue btn-small" type="button" onclick="saveRoutineProfile('simple')">Save changes</button>
          <button class="btn btn-ghost btn-small" type="button" onclick="toggleRoutineEditor('simple', false)">Cancel</button>
        </div>
      `;
    }

    function renderAdvancedRoutineEditor() {
      const editor = state.live_state.routine_editor;
      const fields = editor?.advanced_fields || [];
      els.routineAdvancedEditor.innerHTML = `
        <div class="section-title" style="margin:0">Advanced routine editing</div>
        <div class="small muted" style="margin-top:4px">These exact values drive the routine explanation and the advisory timing rules.</div>
        <div class="routine-fields">
          ${fields.map(field => `
            <div>
              <label>${escapeHtml(field.label)}</label>
              <input id="routine-advanced-${field.id}" type="number" min="1" max="1440" value="${field.effective_value}">
              <div class="small muted" style="margin-top:4px">Default ${field.default_value}m</div>
            </div>
          `).join('')}
        </div>
        <div class="routine-actions">
          <button class="btn btn-blue btn-small" type="button" onclick="saveRoutineProfile('advanced')">Save advanced changes</button>
          <button class="btn btn-ghost btn-small" type="button" onclick="toggleRoutineEditor('advanced', false)">Cancel</button>
        </div>
      `;
    }

    function collectRoutineValues(prefix) {
      const editor = state.live_state.routine_editor;
      const values = { ...(editor.effective_values || {}) };
      getRoutineFieldIds().forEach(fieldId => {
        const input = document.getElementById(`routine-${prefix}-${fieldId}`);
        if (input) values[fieldId] = Number(input.value || values[fieldId] || 0);
      });
      return values;
    }

    function toggleRoutineEditor(kind, force) {
      const panel = kind === 'advanced' ? els.routineAdvancedEditor : els.routineSimpleEditor;
      const other = kind === 'advanced' ? els.routineSimpleEditor : els.routineAdvancedEditor;
      const open = force === undefined ? panel.classList.contains('hidden') : force;
      panel.classList.toggle('hidden', !open);
      other.classList.add('hidden');
    }
    window.toggleRoutineEditor = toggleRoutineEditor;

    async function saveRoutineProfile(saveMode) {
      const prefix = saveMode === 'advanced' ? 'advanced' : 'simple';
      const editor = state.live_state.routine_editor;
      const res = await fetch('/api/routine-profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_age_band_id: editor.active_age_band_id,
          save_mode: saveMode,
          custom_values: collectRoutineValues(prefix),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(data.error || 'Could not save routine', 'error');
        return;
      }
      state = data;
      renderAll();
      els.routineSimpleEditor.classList.add('hidden');
      els.routineAdvancedEditor.classList.add('hidden');
      showToast('Routine updated');
    }
    window.saveRoutineProfile = saveRoutineProfile;

    async function resetRoutineProfile() {
      const res = await fetch('/api/routine-profile', { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok) {
        showToast(data.error || 'Could not reset routine', 'error');
        return;
      }
      state = data;
      renderAll();
      els.routineSimpleEditor.classList.add('hidden');
      els.routineAdvancedEditor.classList.add('hidden');
      showToast('Routine reset to age defaults');
    }
    window.resetRoutineProfile = resetRoutineProfile;

    async function decideRoutineProposal(action) {
      const proposal = state.live_state.routine_proposal;
      if (!proposal) return;
      const res = await fetch(`/api/routine-proposal/${proposal.proposal_id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(data.error || 'Could not update proposal', 'error');
        return;
      }
      state = data;
      renderAll();
      showToast(action === 'accept' ? 'Applied age-based routine update' : 'Kept the current custom routine');
    }
    window.decideRoutineProposal = decideRoutineProposal;

    function renderSchedule() {
      const live = state.live_state;
      const s = state.live_state.schedule;
      const primary = live.primary_advisory || { title: 'All good for now', reason: 'Nothing looks urgent right now.', triggered_by: [] };
      const projection = live.sleep_projection || {};
      const logicBreakdown = live.logic_breakdown || [];
      const sourceLabel = live.schedule_profile_summary?.source === 'default' ? 'default guidance' : 'custom routine + guidance';
      const statusLabel = {
        winner: 'Driving banner',
        active: 'Active rule',
        cleared: 'Cleared',
        waiting: 'Waiting',
        idle: 'Inactive',
        ok: 'On track',
        soon: 'Due soon',
        overdue: 'Overdue',
        unknown: 'No data',
      };
      const cards = [
        {
          title: 'Current recommendation',
          primary: primary.title,
          secondary: primary.reason,
        },
        {
          title: 'Why this is showing',
          primary: primary.triggered_by?.length ? primary.triggered_by.join(' | ') : 'No active trigger details',
          secondary: `${s.context_label} rules using ${sourceLabel}`,
        },
        ...logicBreakdown.map(item => ({
          title: item.label,
          primary: statusLabel[item.status] || item.status,
          secondary: `${item.summary || ''}${item.detail ? ` ${item.detail}` : ''}`.trim(),
        })),
        {
          title: 'Sleep projection',
          primary: projection.recommended_check_at_utc ? `Check again around ${formatWhen(projection.recommended_check_at_utc)}` : 'Log sleep to project the next guidance checkpoint',
          secondary: projection.care_limit_warning || projection.recommended_check_reason || 'No active sleep projection yet.',
        },
        ...(s.routine_summary || []),
      ];
      els.scheduleBlurb.textContent = `${state.settings.puppy_birth_date ? `Using birth date ${state.settings.puppy_birth_date}. ` : ''}Current schedule: ${s.age_label} (${s.age_weeks} weeks), ${s.context_label.toLowerCase()} mode, ${sourceLabel}. Cards below show which rules are active, cleared, or still waiting.`;
      els.scheduleList.innerHTML = cards.map(card => `
        <div class="schedule-item">
          <div><strong>${escapeHtml(card.title)}</strong></div>
          <div class="small" style="margin-top:4px">${escapeHtml(card.primary || '')}</div>
          <div class="small muted">${escapeHtml(card.secondary || '')}</div>
        </div>
      `).join('');
    }

    function renderRoutine() {
      const overview = state.live_state.routine_overview;
      const proposal = state.live_state.routine_proposal;
      const schedule = state.live_state.schedule;

      els.routineBlurb.innerHTML = `
        <div class="routine-badge">${escapeHtml(overview.source_state.source_badge)}</div>
        <div style="margin-top:10px"><strong>${escapeHtml(overview.summary_text)}</strong></div>
        <div class="small muted" style="margin-top:6px">${escapeHtml(overview.source_state.source_detail)}</div>
      `;

      const cards = [];
      if (overview.current_block) {
        cards.push(`
          <div class="schedule-item">
            <div><strong>Now</strong></div>
            <div style="margin-top:6px">${escapeHtml(overview.current_block.title)}</div>
            <div class="small muted" style="margin-top:4px">${escapeHtml(overview.current_block.time_label)}</div>
            <div class="small muted">${escapeHtml(overview.current_block.explanation)}</div>
          </div>
        `);
      }
      if (overview.next_block) {
        cards.push(`
          <div class="schedule-item">
            <div><strong>Next</strong></div>
            <div style="margin-top:6px">${escapeHtml(overview.next_block.title)}</div>
            <div class="small muted" style="margin-top:4px">${escapeHtml(overview.next_block.time_label)}</div>
            <div class="small muted">${escapeHtml(overview.next_block.explanation)}</div>
          </div>
        `);
      }
      (overview.agenda || []).slice(1).forEach(item => {
        cards.push(`
          <div class="schedule-item">
            <div><strong>Later today</strong></div>
            <div style="margin-top:6px">${escapeHtml(item.title)}</div>
            <div class="small muted" style="margin-top:4px">${escapeHtml(item.time_label)}</div>
            <div class="small muted">${escapeHtml(item.explanation)}</div>
          </div>
        `);
      });
      (overview.plain_language_defaults || []).forEach(text => {
        cards.push(`
          <div class="schedule-item">
            <div><strong>Helpful default</strong></div>
            <div class="small muted" style="margin-top:6px">${escapeHtml(text)}</div>
          </div>
        `);
      });
      els.routineList.innerHTML = cards.join('');

      if (proposal) {
        els.routineProposal.classList.remove('hidden');
        els.routineProposal.innerHTML = `
          <div class="section-title" style="margin:0">${escapeHtml(proposal.headline)}</div>
          <div class="small muted" style="margin-top:4px">${escapeHtml(proposal.summary_text)}</div>
          <div class="routine-diff">
            ${proposal.diff_items.map(item => `
              <div class="routine-diff-item">
                <div><strong>${escapeHtml(item.label)}</strong></div>
                <div class="small muted" style="margin-top:4px">Current ${item.current_value}m, recommended ${item.recommended_value}m</div>
                <div class="small muted">${escapeHtml(item.change_note)}</div>
              </div>
            `).join('')}
          </div>
          <div class="routine-actions">
            <button class="btn btn-blue btn-small" type="button" onclick="decideRoutineProposal('accept')">Accept recommendation</button>
            <button class="btn btn-ghost btn-small" type="button" onclick="decideRoutineProposal('reject')">Keep my routine</button>
          </div>
        `;
      } else {
        els.routineProposal.classList.add('hidden');
        els.routineProposal.innerHTML = '';
      }

      renderSimpleRoutineEditor();
      renderAdvancedRoutineEditor();
      els.routineResetBtn.classList.toggle('hidden', schedule.routine_mode !== 'custom_manual');
    }

    function renderAll() {
      if (!state) return;
      renderBanner();
      renderStats();
      renderEvents();
      renderSettings();
      renderSchedule();
      renderRoutine();
    }

    function showToast(text, kind = 'success') {
      els.toast.textContent = text;
      els.toast.classList.toggle('error', kind === 'error');
      els.toast.classList.add('show');
      setTimeout(() => els.toast.classList.remove('show'), 1800);
    }

    async function loadState() {
      const stateRes = await fetch('/api/state');
      state = await stateRes.json();
      currentLogDayIndex = 0;
      renderAll();
    }

    async function quickLog(activity, source = 'quick-action') {
      if (pendingActivities.has(activity)) return;
      pendingActivities.add(activity);
      renderStats();
      const actor = state.settings.household_members[0] || 'McCaul';
      const payload = { activity, actor, event_time_utc: new Date().toISOString() };
      if (activity === 'play') payload.duration_minutes = 20;
      try {
        const res = await fetch('/api/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        pendingActivities.delete(activity);
        if (!res.ok) {
          renderStats();
          showToast(data.error || `Could not log ${activity}`);
          return;
        }
        state = data;
        currentLogDayIndex = 0;
        lastSavedId = state.events[0]?.id || null;
        renderAll();
        if (activity === 'sleep') {
          showToast(`Sleep logged. ${state.live_state.sleep_projection.recommended_check_reason}`);
        } else if (source === 'tile') {
          showToast(`${activity.charAt(0).toUpperCase() + activity.slice(1)} logged from tile`);
        } else {
          showToast(`${activity.charAt(0).toUpperCase() + activity.slice(1)} logged`);
        }
      } catch (error) {
        console.error(error);
        pendingActivities.delete(activity);
        renderStats();
        showToast(`Could not log ${activity}`);
      }
    }
    window.quickLog = quickLog;

    function toggleEdit(id, force) {
      const panel = document.getElementById(`edit-${id}`);
      if (!panel) return;
      const open = force === undefined ? !panel.classList.contains('open') : force;
      panel.classList.toggle('open', open);
    }
    window.toggleEdit = toggleEdit;

    async function saveEdit(id) {
      const activity = document.getElementById(`edit-activity-${id}`).value;
      const actor = document.getElementById(`edit-actor-${id}`).value;
      const dateValue = document.getElementById(`edit-date-${id}`).value;
      const timeValue = document.getElementById(`edit-time-${id}`).value;
      const note = document.getElementById(`edit-note-${id}`).value.trim();
      const eventTime = combineLocalDateTime(dateValue, timeValue);
      if (!eventTime) {
        alert('Could not read the date and time.');
        return;
      }
      const is_accident = canMarkAccident(activity) ? document.getElementById(`edit-accident-${id}`).checked : false;
      const res = await fetch(`/api/events/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity,
          actor,
          event_time_utc: eventTime.toISOString(),
          duration_minutes: activity === 'play' ? 20 : null,
          is_accident,
          note,
        })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Could not update event');
        return;
      }
      state = data;
      currentLogDayIndex = 0;
      renderAll();
      showToast('Event updated');
    }
    window.saveEdit = saveEdit;

    async function deleteEvent(id) {
      const res = await fetch(`/api/events/${id}`, { method: 'DELETE' });
      const data = await res.json();
      state = data;
      currentLogDayIndex = 0;
      renderAll();
      showToast('Event deleted');
    }
    window.deleteEvent = deleteEvent;

    els.settingsForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const household_members = els.householdMembers.value.split(',').map(x => x.trim()).filter(Boolean);
      const payload = {
        puppy_name: els.puppyName.value.trim(),
        household_name: els.householdName.value.trim(),
        timezone_offset_minutes: state.settings.timezone_offset_minutes,
        activities: state.settings.activities,
        household_members,
        puppy_birth_date: els.puppyBirthDate.value
      };
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Could not save settings');
        return;
      }
      state = data;
      currentLogDayIndex = 0;
      renderAll();
      showToast('Settings saved');
    });
    els.routineAdjustBtn.addEventListener('click', () => toggleRoutineEditor('simple'));
    els.routineAdvancedBtn.addEventListener('click', () => toggleRoutineEditor('advanced'));
    els.routineResetBtn.addEventListener('click', resetRoutineProfile);

    els.logNewer.addEventListener('click', () => {
      currentLogDayIndex = Math.max(0, currentLogDayIndex - 1);
      renderEvents();
    });
    els.logOlder.addEventListener('click', () => {
      const maxIndex = Math.max(groupedEventsByDay().length - 1, 0);
      currentLogDayIndex = Math.min(maxIndex, currentLogDayIndex + 1);
      renderEvents();
    });

    function connectWs() {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
      ws = new WebSocket(`${proto}://${window.location.host}/ws`);
      ws.onopen = () => {
        els.wsDot.classList.add('online');
        els.wsStatus.textContent = 'Live';
      };
      ws.onmessage = (event) => {
        state = JSON.parse(event.data);
        renderAll();
      };
      ws.onclose = () => {
        els.wsDot.classList.remove('online');
        els.wsStatus.textContent = 'Reconnecting';
        setTimeout(connectWs, 1500);
      };
    }

    setInterval(() => {
      if (state) {
        renderBanner();
        renderStats();
      }
    }, 30000);

    loadState().then(connectWs);
  </script>
</body>
</html>
'''

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=APP_PORT, reload=False)
