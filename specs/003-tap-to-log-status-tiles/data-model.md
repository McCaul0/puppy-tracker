# Data Model: Tap-To-Log Status Tiles

## Overview

This feature does not require a database migration. It changes the derived dashboard model and
client interaction model around existing `events`.

## Existing Persistent Entity

### Event

- **Purpose**: Record a logged puppy activity.
- **Existing fields**:
  - `id`
  - `activity`
  - `actor`
  - `event_time_utc`
  - `duration_minutes`
  - `is_accident`
  - `note`
  - `created_at_utc`
- **Feature impact**:
  - Tile taps create ordinary `Event` rows using the existing activity types.
  - No new event type is introduced for tile taps.
  - Supported tile taps always create the default version of the matching event.
  - Edit/delete remain the correction path after a mistaken tile log.

## New Derived Entities

### StatusTileView

- **Purpose**: Represent one dashboard tile as both a status surface and, when valid, a direct
  logging target.
- **Fields**:
  - `key`: stable tile identifier such as `pee`
  - `label`: user-facing name such as `Pee`
  - `minutes`: elapsed time value or `null`
  - `display_value`: rendered elapsed copy such as `36m ago` or `No entries yet`
  - `urgency`: one of `on-track`, `soon`, `overdue`, `unknown`
  - `urgency_label`: user-facing urgency copy such as `Due soon`
  - `is_tappable`: boolean
  - `tap_activity`: matching event activity or `null`
  - `tap_hint`: lightweight affordance copy such as `Tap to log`
  - `readonly_reason`: explanation when `is_tappable` is false
- **Rules**:
  - `pee`, `poop`, `food`, and `water` are tappable when present in supported activities.
  - `awake` is always read-only because it represents derived state.
  - Tile actionability should not vary by urgency state.

### SecondaryQuickAction

- **Purpose**: Represent actions that still need a fast path outside the tile grid.
- **Fields**:
  - `activity`
  - `label`
  - `kind`: `secondary-log`
- **Rules**:
  - First-cut members are `play`, `sleep`, and `wake`.
  - Activities promoted to tappable tiles should not also appear here as primary buttons.

### TileFeedbackState

- **Purpose**: Describe the client-visible outcome of a tap attempt.
- **Fields**:
  - `status`: `idle`, `pending`, `success`, or `error`
  - `activity`
  - `message`
- **Rules**:
  - `pending` is client-local and temporarily disables repeated submission for that tile.
  - `success` and `error` should be communicated with the existing toast mechanism.
  - A failed request must not change the visible dashboard state.

## State Transitions

### Supported tile tap

1. User taps a tappable tile.
2. Client enters `pending` for that tile and submits `POST /api/events`.
3. Server creates a standard `Event` row and recomputes `live_state`.
4. Server returns the updated snapshot and broadcasts it to connected clients.
5. Client clears `pending`, refreshes tiles/banner/recent activity, and shows success feedback.

### Failed tile tap

1. User taps a tappable tile.
2. Client enters `pending`.
3. Request fails.
4. Client clears `pending`, preserves the pre-tap dashboard state, and shows an error message.

### Mistaken tile tap

1. User taps a tappable tile and the event saves successfully.
2. Event appears in recent activity like any other quick log.
3. User fixes the mistake through existing edit or delete actions.

## Validation Rules

- Only tiles with a one-to-one mapping to a current event activity may set `is_tappable = true`.
- Read-only or derived-state tiles must not expose `tap_activity`.
- The dashboard must continue to expose exactly one primary recommendation in `needs_now`.
- Successful tile logs must trigger the same immediate recomputation and websocket update as any
  other event creation.
