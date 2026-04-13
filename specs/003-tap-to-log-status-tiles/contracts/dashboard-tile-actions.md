# Contract: Dashboard Tile Actions

## Purpose

Define the user-visible dashboard snapshot fields needed for tile-based logging while keeping
`POST /api/events` as the only event write endpoint.

## Read Contract

### `GET /api/state`

The existing snapshot remains the source of truth and gains richer tile metadata plus a derived
secondary quick-action list.

#### Tile object shape

Each entry in `live_state.tiles` should follow this shape:

```json
{
  "key": "pee",
  "label": "Pee",
  "minutes": 36,
  "display_value": "36m ago",
  "urgency": "soon",
  "urgency_label": "Due soon",
  "is_tappable": true,
  "tap_activity": "pee",
  "tap_hint": "Tap to log",
  "readonly_reason": null
}
```

Read-only derived tiles should instead look like:

```json
{
  "key": "awake",
  "label": "Awake",
  "minutes": 84,
  "display_value": "1h 24m ago",
  "urgency": "soon",
  "urgency_label": "Due soon",
  "is_tappable": false,
  "tap_activity": null,
  "tap_hint": null,
  "readonly_reason": "Derived state"
}
```

#### Secondary quick actions

Add a derived list at `live_state.secondary_quick_actions`:

```json
[
  { "activity": "play", "label": "Play" },
  { "activity": "sleep", "label": "Sleep" },
  { "activity": "wake", "label": "Wake" }
]
```

Rules:

- Supported tile activities must not also appear in `secondary_quick_actions`.
- The list should reflect current configured activities, omitting anything disabled in settings.
- The field is intended for dashboard rendering only and does not replace the event model.

## Write Contract

### `POST /api/events`

No endpoint shape change is required. Tile taps submit the same body used by current quick
actions:

```json
{
  "activity": "pee",
  "actor": "McCaul",
  "event_time_utc": "2026-04-11T16:20:00Z"
}
```

Rules:

- Tile taps use the mapped `tap_activity`.
- Tile taps do not introduce a tile-specific event subtype.
- Successful responses return the full updated dashboard snapshot as they do today.
- Failed responses return an error without mutating visible dashboard state on the client.

## Client Rendering Expectations

- Supported tiles should render with button semantics and remain visually recognizable as status
  tiles first.
- The affordance for tappable tiles should be lightweight, such as hint text or an icon label,
  rather than a competing CTA block.
- Read-only tiles must not use hover, focus, cursor, or aria behavior that implies clickability.
- The active tile should be disabled while a submission is in flight to reduce accidental double
  logging.

## Live Update Expectations

- A successful tile tap must update the local device immediately from the response snapshot.
- Connected secondary devices must receive the recomputed snapshot through the existing websocket
  broadcast flow.
- The recent activity list, tile urgency, and banner recommendation must all reflect the new
  event in the same update cycle.
