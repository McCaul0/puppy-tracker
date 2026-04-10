from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

APP_TITLE = "Puppy Coordinator"
APP_VERSION = os.environ.get("PUPPY_TRACKER_VERSION", "v14.2 test")
DB_PATH = Path(os.environ.get("PUPPY_TRACKER_DB", "puppy_tracker.db"))
APP_PORT = int(os.environ.get("PUPPY_TRACKER_PORT", "8000"))
DEFAULT_TZ_OFFSET_MINUTES = int(os.environ.get("PUPPY_TZ_OFFSET_MINUTES", "-240"))

DEFAULT_ACTIVITIES = ["pee", "poop", "food", "water", "sleep", "wake", "play"]
DEFAULT_HOUSEHOLD_MEMBERS = ["McCaul", "Jess"]
REST_ACTIVITIES = {"sleep"}

app = FastAPI(title=APP_TITLE)


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
        if not item or item == "accident" or item in cleaned:
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
    return {
        "puppy_name": raw.get("puppy_name", "Puppy"),
        "household_name": raw.get("household_name", "Home"),
        "timezone_offset_minutes": int(raw.get("timezone_offset_minutes", str(DEFAULT_TZ_OFFSET_MINUTES))),
        "activities": activities,
        "household_members": household_members,
        "puppy_birth_date": raw.get("puppy_birth_date", ""),
    }


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


def get_age_weeks(settings: Dict[str, Any], now: datetime) -> Optional[float]:
    birth = parse_date(settings.get("puppy_birth_date"))
    if not birth:
        return None
    days = (now.date() - birth).days
    if days < 0:
        return 0.0
    return days / 7.0


def get_schedule(settings: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    age_weeks = get_age_weeks(settings, now)
    if age_weeks is None:
        age_weeks = 12.0

    if age_weeks < 10:
        label = "8-10 weeks"
        schedule = {
            "pee_due": 45, "pee_overdue": 60,
            "poop_due": 180, "poop_overdue": 240,
            "food_due": 240, "food_overdue": 300,
            "water_due": 90, "water_overdue": 120,
            "awake_due": 45, "awake_overdue": 60,
            "sleep_default": 120,
            "post_food_potty_due": 10, "post_food_potty_overdue": 20,
        }
    elif age_weeks < 12:
        label = "10-12 weeks"
        schedule = {
            "pee_due": 60, "pee_overdue": 90,
            "poop_due": 240, "poop_overdue": 300,
            "food_due": 300, "food_overdue": 360,
            "water_due": 120, "water_overdue": 180,
            "awake_due": 60, "awake_overdue": 75,
            "sleep_default": 120,
            "post_food_potty_due": 10, "post_food_potty_overdue": 25,
        }
    elif age_weeks < 16:
        label = "12-16 weeks"
        schedule = {
            "pee_due": 120, "pee_overdue": 180,
            "poop_due": 300, "poop_overdue": 420,
            "food_due": 360, "food_overdue": 480,
            "water_due": 180, "water_overdue": 240,
            "awake_due": 90, "awake_overdue": 120,
            "sleep_default": 120,
            "post_food_potty_due": 15, "post_food_potty_overdue": 30,
        }
    elif age_weeks < 24:
        label = "4-6 months"
        schedule = {
            "pee_due": 180, "pee_overdue": 240,
            "poop_due": 420, "poop_overdue": 540,
            "food_due": 480, "food_overdue": 720,
            "water_due": 240, "water_overdue": 300,
            "awake_due": 180, "awake_overdue": 240,
            "sleep_default": 120,
            "post_food_potty_due": 15, "post_food_potty_overdue": 30,
        }
    else:
        label = "6+ months"
        schedule = {
            "pee_due": 240, "pee_overdue": 360,
            "poop_due": 540, "poop_overdue": 720,
            "food_due": 600, "food_overdue": 720,
            "water_due": 300, "water_overdue": 360,
            "awake_due": 240, "awake_overdue": 300,
            "sleep_default": 120,
            "post_food_potty_due": 15, "post_food_potty_overdue": 35,
        }

    schedule["age_weeks"] = round(age_weeks, 1)
    schedule["age_label"] = label
    return schedule


def find_last(events_desc: List[Dict[str, Any]], activity: str) -> Optional[Dict[str, Any]]:
    for event in events_desc:
        if event["activity"] == activity:
            return event
    return None


def latest_sleep_block(events_desc: List[Dict[str, Any]], schedule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    events_asc = list(reversed(events_desc))
    latest_block = None
    current_now = utc_now()
    for index, event in enumerate(events_asc):
        if event["activity"] != "sleep":
            continue
        start_dt = parse_iso(event["event_time_utc"])
        if not start_dt:
            continue
        planned = event.get("duration_minutes") or schedule["sleep_default"]
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
        }
    return latest_block


def current_awake_minutes(events_desc: List[Dict[str, Any]], schedule: Dict[str, Any], now: datetime) -> Optional[int]:
    block = latest_sleep_block(events_desc, schedule)
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


def urgency(value: Optional[int], due: int, overdue: int) -> str:
    if value is None:
        return "unknown"
    if value >= overdue:
        return "overdue"
    if value >= due:
        return "soon"
    return "ok"


def local_time_label(iso: Optional[str], offset_minutes: int) -> str:
    dt = parse_iso(iso)
    if not dt:
        return "unknown"
    local = dt.astimezone(timezone(timedelta(minutes=offset_minutes)))
    if os.name == "nt":
        return local.strftime("%#I:%M %p")
    return local.strftime("%-I:%M %p")


def needs_now(events_desc: List[Dict[str, Any]], settings: Dict[str, Any], schedule: Dict[str, Any], live: Dict[str, Any]) -> Dict[str, str]:
    if live["sleep_block"] and live["sleep_block"]["is_sleeping_now"]:
        wake_by = live["sleep_block"]["projected_end_time_utc"]
        return {
            "title": "Sleeping now",
            "reason": f"Wake by {local_time_label(wake_by, settings['timezone_offset_minutes'])}",
        }

    food_last = find_last(events_desc, "food")
    food_minutes = live["since_food_minutes"]
    if food_last and food_minutes is not None:
        if schedule["post_food_potty_due"] <= food_minutes < schedule["post_food_potty_overdue"]:
            return {"title": "Likely needs potty soon", "reason": f"Ate {food_minutes}m ago"}
        if food_minutes >= schedule["post_food_potty_overdue"] and live["since_pee_minutes"] is not None and live["since_pee_minutes"] > schedule["pee_due"] // 2:
            return {"title": "Potty likely overdue", "reason": f"Ate {food_minutes}m ago and last pee was {live['since_pee_minutes']}m ago"}

    if urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"]) == "overdue":
        return {"title": "Pee break overdue", "reason": f"Last pee was {live['since_pee_minutes']}m ago"}
    if urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"]) == "overdue":
        return {"title": "Needs sleep", "reason": f"Awake for {live['since_awake_minutes']}m"}
    if urgency(live["since_food_minutes"], schedule["food_due"], schedule["food_overdue"]) == "overdue":
        return {"title": "Food likely due", "reason": f"Last food was {live['since_food_minutes']}m ago"}
    if urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"]) == "soon":
        return {"title": "Potty soon", "reason": f"Last pee was {live['since_pee_minutes']}m ago"}
    if urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"]) == "soon":
        return {"title": "Sleep soon", "reason": f"Awake for {live['since_awake_minutes']}m"}
    return {"title": "All good for now", "reason": "Nothing looks urgent right now"}


def build_live_state(settings: Dict[str, Any], events_desc: List[Dict[str, Any]], now: datetime) -> Dict[str, Any]:
    schedule = get_schedule(settings, now)
    sleep_block = latest_sleep_block(events_desc, schedule)

    live = {
        "since_awake_minutes": current_awake_minutes(events_desc, schedule, now),
        "since_pee_minutes": minutes_since((find_last(events_desc, "pee") or {}).get("event_time_utc"), now),
        "since_poop_minutes": minutes_since((find_last(events_desc, "poop") or {}).get("event_time_utc"), now),
        "since_food_minutes": minutes_since((find_last(events_desc, "food") or {}).get("event_time_utc"), now),
        "since_water_minutes": minutes_since((find_last(events_desc, "water") or {}).get("event_time_utc"), now),
        "sleep_block": sleep_block,
    }

    tiles = {
        "pee": {"minutes": live["since_pee_minutes"], "urgency": urgency(live["since_pee_minutes"], schedule["pee_due"], schedule["pee_overdue"])},
        "poop": {"minutes": live["since_poop_minutes"], "urgency": urgency(live["since_poop_minutes"], schedule["poop_due"], schedule["poop_overdue"])},
        "food": {"minutes": live["since_food_minutes"], "urgency": urgency(live["since_food_minutes"], schedule["food_due"], schedule["food_overdue"])},
        "water": {"minutes": live["since_water_minutes"], "urgency": urgency(live["since_water_minutes"], schedule["water_due"], schedule["water_overdue"])},
        "awake": {"minutes": live["since_awake_minutes"], "urgency": urgency(live["since_awake_minutes"], schedule["awake_due"], schedule["awake_overdue"])},
        "sleep": {"minutes": sleep_block["actual_duration_minutes"] if sleep_block else None, "urgency": "ok" if sleep_block and sleep_block["is_sleeping_now"] else "unknown"},
    }

    return {
        **live,
        "tiles": tiles,
        "schedule": schedule,
        "needs_now": needs_now(events_desc, settings, schedule, live),
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
def index() -> str:
    return HTML


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
    if event.activity == "sleep" and duration is None:
        duration = get_schedule(settings, event_time)["sleep_default"]
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
    .tile{border-radius:16px;padding:12px;border:1px solid var(--border)}
    .tile .label{font-size:.8rem;font-weight:700;letter-spacing:.02em}
    .tile .value{font-size:1.35rem;font-weight:800;margin-top:6px}
    .tile .meta{font-size:.78rem;margin-top:6px;opacity:.9}
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
    summary{cursor:pointer;font-weight:800}
    .settings-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
    .settings-grid > div,.edit-grid > div{min-width:0}
    label{font-size:.82rem;font-weight:700;color:var(--muted);display:block;margin-bottom:6px}
    input, select, textarea{width:100%;padding:10px 12px;border-radius:12px;border:1px solid var(--input-border);font:inherit;background:var(--input);color:var(--text)}
    input::placeholder, textarea::placeholder{color:#70829f}
    textarea{min-height:84px;resize:vertical}
    .edit-panel{display:none;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}
    .edit-panel.open{display:block}
    .edit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .datetime-pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(6.75rem,8.25rem);gap:8px;align-items:end}
    .datetime-pair > *{min-width:0}
    .datetime-pair .time-box{min-width:0}
    .datetime-pair input{text-align:left;min-width:0}
    input[type="date"],input[type="time"],input[type="datetime-local"]{min-width:0}
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
    .log-day{width:5.75rem;font-size:.92rem;font-weight:700;color:var(--muted);text-align:center;font-variant-numeric:tabular-nums}
    .footer-version{margin-top:18px;text-align:center;font-size:.82rem;color:var(--muted)}
    @media (max-width:760px){
      .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
      .actions{grid-template-columns:repeat(2,minmax(0,1fr))}
      .settings-grid,.edit-grid,.schedule-list{grid-template-columns:1fr}
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

    <div class="card" style="margin-bottom:14px">
      <div class="row" style="margin-bottom:10px">
        <div class="section-title">Log an activity</div>
        <select id="device-actor" style="max-width:10rem"></select>
      </div>
      <div id="quick-actions" class="actions"></div>
      <div class="checkbox-chip" style="margin-top:10px">
        <input id="quick-accident" type="checkbox">
        <label for="quick-accident" style="margin:0;color:var(--text)">Mark the next pee or poop as an accident</label>
      </div>
    </div>

    <details class="card">
      <summary>Schedule and logic</summary>
      <div id="schedule-blurb" class="small muted" style="margin-top:10px"></div>
      <div id="schedule-list" class="schedule-list"></div>
      <div class="small muted" style="margin-top:10px">
        The app uses age based schedule guardrails, time since key activities, and a few fixed triggers.
        Sleep starts are assumed immediately. A later Wake or any other later activity can end the sleep early.
      </div>
    </details>

    <details class="card">
      <summary>Settings</summary>
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
    const DEVICE_ACTOR_KEY = 'puppy_tracker_device_actor';

    const els = {
      title: document.getElementById('title'),
      subtitle: document.getElementById('subtitle'),
      wsDot: document.getElementById('ws-dot'),
      wsStatus: document.getElementById('ws-status'),
      toast: document.getElementById('toast'),
      quickStats: document.getElementById('quick-stats'),
      quickActions: document.getElementById('quick-actions'),
      quickAccident: document.getElementById('quick-accident'),
      eventList: document.getElementById('event-list'),
      logNewer: document.getElementById('log-newer'),
      logOlder: document.getElementById('log-older'),
      logDayLabel: document.getElementById('log-day-label'),
      appVersion: document.getElementById('app-version'),
      needsTitle: document.getElementById('needs-title'),
      needsReason: document.getElementById('needs-reason'),
      deviceActor: document.getElementById('device-actor'),
      settingsForm: document.getElementById('settings-form'),
      puppyName: document.getElementById('puppy-name'),
      householdName: document.getElementById('household-name'),
      puppyBirthDate: document.getElementById('puppy-birth-date'),
      householdMembers: document.getElementById('household-members'),
      scheduleBlurb: document.getElementById('schedule-blurb'),
      scheduleList: document.getElementById('schedule-list')
    };

    function escapeHtml(value) {
      return String(value || '')
        .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
    }

    function getDeviceActor() {
      return window.localStorage.getItem(DEVICE_ACTOR_KEY) || '';
    }

    function setDeviceActor(value) {
      if (value) window.localStorage.setItem(DEVICE_ACTOR_KEY, value);
      else window.localStorage.removeItem(DEVICE_ACTOR_KEY);
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

    function combineLocalDateTime(dateValue, timeValue) {
      const safeDate = dateValue || localDateValue();
      const safeTime = timeValue || '12:00';
      return new Date(`${safeDate}T${safeTime}`);
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

    function renderStats() {
      const live = state.live_state;
      const order = ['pee', 'poop', 'food', 'water', 'awake'];
      const labels = {pee:'Pee', poop:'Poop', food:'Food', water:'Water', awake:'Awake'};
      els.quickStats.innerHTML = order.map(key => {
        const t = live.tiles[key];
        const meta = statusMeta(key, live);
        const urgency = t ? t.urgency : 'unknown';
        const urgencyLabel = urgency === 'overdue' ? 'Overdue' : urgency === 'soon' ? 'Due soon' : urgency === 'unknown' ? 'No data' : 'On track';
        const extraClass = key === 'awake' ? ' awake-wide' : '';
        return `
          <div class="${tileClass(key, urgency)}${extraClass}">
            <div class="label">${labels[key]}</div>
            <div class="value">${escapeHtml(meta.value)}</div>
            <div class="meta"><strong>${urgencyLabel}</strong></div>
          </div>
        `;
      }).join('');
    }

    function renderBanner() {
      els.needsTitle.textContent = state.live_state.needs_now.title;
      els.needsReason.textContent = state.live_state.needs_now.reason;
    }

    function quickButtons() {
      return [
        { key: 'pee', label: 'Pee' },
        { key: 'poop', label: 'Poop' },
        { key: 'food', label: 'Food' },
        { key: 'water', label: 'Water' },
        { key: 'play', label: 'Play' },
        { key: 'sleep', label: 'Sleep' },
        { key: 'wake', label: 'Wake' },
      ];
    }

    function renderActions() {
      els.quickActions.innerHTML = quickButtons().map(item => `
        <button class="btn btn-blue" type="button" onclick="quickLog('${item.key}')">${item.label}</button>
      `).join('');
      els.quickAccident.checked = false;
    }

    function sleepDurationHours(event) {
      const minutes = Number(event?.duration_minutes || 120);
      return Math.max(1, Math.round(minutes / 60));
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
          ${event.activity === 'sleep' ? `<div class="small muted" style="margin-top:6px">Sleep for ${sleepDurationHours(event)}h</div>` : ''}
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
              <div id="edit-sleep-wrap-${event.id}" style="${event.activity === 'sleep' ? '' : 'display:none'}">
                <label>Sleep for</label>
                <input id="edit-sleep-hours-${event.id}" type="number" min="1" step="1" inputmode="numeric" value="${event.activity === 'sleep' ? sleepDurationHours(event) : 2}">
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
            const sleepWrap = document.getElementById(`edit-sleep-wrap-${event.id}`);
            const accidentWrap = document.getElementById(`edit-accident-wrap-${event.id}`);
            const accidentInput = document.getElementById(`edit-accident-${event.id}`);
            sleepWrap.style.display = activitySelect.value === 'sleep' ? '' : 'none';
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
      const saved = getDeviceActor();
      els.deviceActor.innerHTML = state.settings.household_members.map(a => `<option value="${escapeHtml(a)}" ${a === saved ? 'selected' : ''}>${escapeHtml(a)}</option>`).join('');
      if (!saved && state.settings.household_members[0]) {
        setDeviceActor(state.settings.household_members[0]);
        els.deviceActor.value = state.settings.household_members[0];
      }
    }

    function renderSchedule() {
      const s = state.live_state.schedule;
      els.scheduleBlurb.textContent = `${state.settings.puppy_birth_date ? `Using birth date ${state.settings.puppy_birth_date}. ` : ''}Current schedule: ${s.age_label} (${s.age_weeks} weeks).`;
      const items = [
        ['Pee due', `${s.pee_due}m`, `Overdue at ${s.pee_overdue}m`],
        ['Poop due', `${s.poop_due}m`, `Overdue at ${s.poop_overdue}m`],
        ['Food due', `${s.food_due}m`, `Overdue at ${s.food_overdue}m`],
        ['Water due', `${s.water_due}m`, `Overdue at ${s.water_overdue}m`],
        ['Sleep due', `${s.awake_due}m awake`, `Overdue at ${s.awake_overdue}m awake`],
        ['Post-food potty', `${s.post_food_potty_due}m`, `Overdue at ${s.post_food_potty_overdue}m`],
      ];
      els.scheduleList.innerHTML = items.map(([a,b,c]) => `<div class="schedule-item"><div><strong>${a}</strong></div><div class="small muted" style="margin-top:4px">${b}</div><div class="small muted">${c}</div></div>`).join('');
    }

    function renderAll() {
      if (!state) return;
      renderBanner();
      renderStats();
      renderActions();
      renderEvents();
      renderSettings();
      renderSchedule();
    }

    function showToast(text) {
      els.toast.textContent = text;
      els.toast.classList.add('show');
      setTimeout(() => els.toast.classList.remove('show'), 1800);
    }

    async function loadState() {
      const res = await fetch('/api/state');
      state = await res.json();
      currentLogDayIndex = 0;
      renderAll();
    }

    async function quickLog(activity) {
      const actor = getDeviceActor() || state.settings.household_members[0] || 'McCaul';
      const payload = { activity, actor, event_time_utc: new Date().toISOString() };
      if (canMarkAccident(activity)) payload.is_accident = els.quickAccident.checked;
      if (activity === 'sleep') payload.duration_minutes = state.live_state.schedule.sleep_default;
      if (activity === 'play') payload.duration_minutes = 20;
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Could not save event');
        return;
      }
      state = data;
      currentLogDayIndex = 0;
      lastSavedId = state.events[0]?.id || null;
      if (canMarkAccident(activity)) els.quickAccident.checked = false;
      renderAll();
      if (activity === 'sleep') {
        showToast(`Sleep logged for ${humanMinutesShort(state.live_state.schedule.sleep_default)}`);
      } else {
        showToast(`${activity.charAt(0).toUpperCase() + activity.slice(1)} logged`);
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
      const is_accident = canMarkAccident(activity) ? document.getElementById(`edit-accident-${id}`).checked : false;
      let duration_minutes = null;
      if (activity === 'sleep') {
        const sleepHours = Number(document.getElementById(`edit-sleep-hours-${id}`).value || 2);
        duration_minutes = Math.max(60, Math.round(sleepHours) * 60);
      }
      const res = await fetch(`/api/events/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity,
          actor,
          event_time_utc: eventTime.toISOString(),
          duration_minutes,
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
      const currentActor = getDeviceActor();
      if (!household_members.includes(currentActor) && household_members[0]) {
        setDeviceActor(household_members[0]);
      }
      renderAll();
      showToast('Settings saved');
    });

    els.deviceActor.addEventListener('change', () => {
      setDeviceActor(els.deviceActor.value);
      showToast(`This device defaults to ${els.deviceActor.value}`);
    });
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
