# Puppy Coordinator Data Contract

This document describes the persisted data and API shapes currently implemented by [`app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py).

It is the technical companion to the behavioral spec.

## Purpose

Use this doc to answer:

- what data exists
- what each field means
- what values are allowed
- what normalization happens
- what would require a migration

## Runtime Configuration

Environment variables:

- `PUPPY_TRACKER_DB`
  Purpose: SQLite database path.
  Default: `puppy_tracker.db`
- `PUPPY_TRACKER_PORT`
  Purpose: HTTP port.
  Default: `8000`
- `PUPPY_TZ_OFFSET_MINUTES`
  Purpose: household timezone offset used for some server-rendered labels and schedule context.
  Default: `-240`

## Database Schema

### `settings`

Key-value table.

Columns:

- `key TEXT PRIMARY KEY`
- `value TEXT NOT NULL`

Known keys:

- `puppy_name`
  Example: `Puppy`
- `household_name`
  Example: `Home`
- `timezone_offset_minutes`
  Stored as a string integer.
  Example: `-240`
- `activities`
  Stored as JSON array of strings.
  Current defaults: `["pee", "poop", "food", "water", "sleep", "wake", "play"]`
- `household_members`
  Stored as JSON array of strings.
  Example: `["McCaul", "Jess"]`
- `puppy_birth_date`
  Stored as ISO date string or empty string.
  Example: `2026-01-15`
- `routine_profile_state`
  Stored as JSON object describing whether the routine is auto-following the current age band or
  using a saved custom routine.
  Example: `{"version":1,"routine_mode":"default_auto","last_reviewed_recommendation_band_id":"10_to_12_weeks","last_proposal_action":null,"custom_profile":null}`

Normalization on save/read:

- activities are trimmed
- activities are lowercased
- blank activities are removed
- duplicate activities are removed
- deprecated `accident` activity is removed
- default activities are always re-added if missing
- household members are trimmed
- blank household members are removed
- duplicate household members are removed
- if no valid household members remain, defaults are restored

### `events`

Event log table.

Columns:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `activity TEXT NOT NULL`
- `actor TEXT NOT NULL`
- `event_time_utc TEXT NOT NULL`
- `duration_minutes INTEGER`
- `is_accident INTEGER NOT NULL DEFAULT 0`
- `note TEXT`
- `created_at_utc TEXT NOT NULL`

Field meanings:

- `id`
  Stable row identifier.
- `activity`
  Current supported values are expected to come from settings activities.
  Default activity set: `pee`, `poop`, `food`, `water`, `sleep`, `wake`, `play`
- `actor`
  Household member name used when the event was logged.
- `event_time_utc`
  ISO-8601 UTC timestamp representing when the activity happened.
- `duration_minutes`
  Optional numeric duration.
  Used most meaningfully for `sleep`.
  Defaulted in server logic for some quick actions.
- `is_accident`
  Boolean stored as `0` or `1`.
  Only meaningful for `pee` and `poop`.
  Forced to `0` for all other activities.
- `note`
  Optional free text note.
- `created_at_utc`
  ISO-8601 UTC timestamp representing when the row was inserted.

## API Contract

### `GET /api/state`

Returns a dashboard snapshot containing:

- `type`
- `settings`
- `events`
- `server_time_utc`
- `live_state`

### `POST /api/events`

Creates an event.

Accepted body:

- `activity: string`
- `actor: string`
- `event_time_utc: string | null`
- `duration_minutes: integer | null`
- `is_accident: boolean`
- `note: string | null`

Validation:

- `activity` length 1-50
- `actor` length 1-50
- `duration_minutes` 0-1440 when provided
- `note` max length 500
- `activity` must exist in current settings activities
- `is_accident` is only honored for `pee` and `poop`

Server behavior:

- invalid or missing event time falls back to current server UTC time
- `sleep` defaults duration to schedule `sleep_default`
- `play` defaults duration to `20`

### `PUT /api/events/{event_id}`

Updates an existing event.

Accepted body:

- `activity: string`
- `actor: string`
- `event_time_utc: string`
- `duration_minutes: integer | null`
- `is_accident: boolean`
- `note: string | null`

Validation:

- same field limits as create
- event time must parse as ISO datetime
- target event must exist
- `is_accident` is reset to `false` when the edited activity is not `pee` or `poop`

### `DELETE /api/events/{event_id}`

Deletes an event by numeric ID.

### `POST /api/settings`

Saves settings.

Accepted body:

- `puppy_name: string`
- `household_name: string`
- `timezone_offset_minutes: integer`
- `activities: string[]`
- `household_members: string[]`
- `puppy_birth_date: string`

Validation:

- `puppy_name` length 1-50
- `household_name` length 1-50
- `timezone_offset_minutes` between `-720` and `840`
- `activities` item count 3-20 before normalization
- `household_members` item count 1-10 before normalization
- `puppy_birth_date` must be empty or ISO date

### `PUT /api/routine-profile`

Saves a simplified routine profile.

Accepted body:

- `base_age_band_id: string`
- `save_mode: "simple" | "advanced"`
- `custom_values: object`

Validation:

- `base_age_band_id` must match a known age band
- every routine field must be present
- every routine field must be numeric and between `1` and `1440`
- every `*_due` value must stay below its matching `*_overdue` value

### `DELETE /api/routine-profile`

Resets the routine back to automatic age-following behavior.

### `POST /api/routine-proposal/{proposal_id}/decision`

Accepted body:

- `action: "accept" | "reject"`

Accepting returns the routine to auto-following mode for the current age band.
Rejecting keeps the saved custom routine and suppresses the current recommendation prompt.

## Derived Behavior Contract

These values are not stored directly; they are derived from settings plus recent events:

- `since_awake_minutes`
- `since_pee_minutes`
- `since_poop_minutes`
- `since_food_minutes`
- `since_water_minutes`
- `sleep_block`
- `tiles`
- `secondary_quick_actions`
- `schedule`
- `routine_overview`
- `routine_editor`
- `routine_proposal`
- `needs_now`

Tile behavior notes:

- `tiles` include status/urgency display data plus tap-to-log metadata for supported activities.
- `pee`, `poop`, `food`, and `water` tiles can act as one-tap logging targets.
- `awake` remains read-only and is marked as derived state.
- `secondary_quick_actions` is limited to actions that remain supported but do not belong on a status tile.

Important derived rules:

- sleep ends at the first later `wake` event
- if no `wake` exists, sleep can end early on the first later non-sleep activity before the projected end
- awake time is derived from the latest sleep block end when available
- otherwise awake falls back to time since the most recent valid event

## Current Gaps

- no explicit schema version is stored in the DB
- no migration system exists
- no multi-flag subtype model exists beyond the single `is_accident` boolean

## Migration Triggers

Any of the following should be treated as a migration-worthy change:

- adding columns to `events`
- changing meaning of an existing field
- changing event activity semantics
- changing settings key names
- introducing a schema version
- expanding event flags or subtypes beyond the current `is_accident` model
