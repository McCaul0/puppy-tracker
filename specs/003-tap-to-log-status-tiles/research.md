# Research: Tap-To-Log Status Tiles

## Decision 1: Limit the first cut to tiles with a clear one-to-one event mapping

- **Decision**: Make only `pee`, `poop`, `food`, and `water` tappable in the first cut. Keep
  `awake` read-only, and treat any future sleep-status surface as read-only unless it can
  represent a single obvious action as safely as the current quick-log button.
- **Rationale**: These four tiles already describe the same real-world event the user would be
  logging. `awake` is derived from sleep boundaries and other events, so tapping it would blur
  status and action meaning. This keeps FR-004 and FR-009 explicit instead of relying on
  ambiguous heuristics.
- **Alternatives considered**:
  - Make every tile tappable: rejected because derived-state tiles would become misleading.
  - Only make overdue tiles tappable: rejected because actionability would change by state and
    become harder to learn.

## Decision 2: Keep tile actionability stable instead of changing it with urgency

- **Decision**: A supported tile is always tappable when its activity exists in current settings,
  regardless of whether its urgency is `on-track`, `soon`, `overdue`, or `unknown`. The only
  temporary exception is the in-flight pending state while a request is being submitted.
- **Rationale**: The tile should communicate urgency, not gate whether it can be used. Stable
  actionability is easier to recognize, reduces surprise, and avoids edge cases where a tile
  flips between button and static card behavior as timers update.
- **Alternatives considered**:
  - Only allow taps when due or overdue: rejected because it makes logging inconsistent with the
    one-tap-first model.
  - Disable tiles with `unknown` timing: rejected because no prior data should not prevent
    first-time logging.

## Decision 3: Reuse the current event-creation path and enrich the dashboard snapshot

- **Decision**: Keep `POST /api/events` as the write path for tile taps and extend
  `GET /api/state` so each tile explicitly declares whether it is tappable, what activity it
  maps to, and what lightweight hint text or disabled reason should be shown.
- **Rationale**: The existing event endpoint already triggers the correct persistence,
  recomputation, websocket broadcast, and recent-activity refresh behavior. A richer snapshot
  keeps actionability rules server-defined so both the live app and `test_app` stay aligned.
- **Alternatives considered**:
  - Add a dedicated tile-action endpoint: rejected because it duplicates event creation rules.
  - Keep all tap logic client-only: rejected because supported mappings and fallback quick-action
    choices would drift between entrypoints.

## Decision 4: Reduce surface duplication by shrinking the quick-action area

- **Decision**: Remove primary quick-action buttons for the supported tile activities and keep a
  smaller secondary quick-log surface only for actions not represented by tappable tiles, namely
  `play`, `sleep`, and `wake`.
- **Rationale**: The spec and constitution both push toward one clear default path and fewer
  competing concepts on the dashboard. Leaving duplicate primary buttons for `pee`, `poop`,
  `food`, and `water` would weaken the main goal of simplification.
- **Alternatives considered**:
  - Keep the full quick-action strip unchanged: rejected because the dashboard would still have
    duplicate primary logging surfaces.
  - Remove quick actions entirely: rejected because unsupported actions still need a fast path.

## Decision 5: Preserve speed by using feedback and recovery instead of confirmation

- **Decision**: A tile tap should immediately submit the matching event, temporarily lock that
  tile while the request is in flight, show a success toast when the save completes, and show a
  clear error if the save fails. Recovery remains the existing recent-activity edit/delete path.
- **Rationale**: Confirmation dialogs would violate the one-tap-first model. A pending lock
  reduces accidental duplicate taps, while success and error feedback keeps the dashboard
  truthful and predictable. Edit/delete already provide the correction path required by FR-007.
- **Alternatives considered**:
  - Add a confirmation step before every tile log: rejected because it adds friction to the
    default flow.
  - Add no feedback beyond the visual refresh: rejected because users may miss what just changed,
    especially when the tap clears urgency immediately.
