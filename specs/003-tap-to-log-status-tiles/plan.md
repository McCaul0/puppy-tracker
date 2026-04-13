# Implementation Plan: Tap-To-Log Status Tiles

**Branch**: `003-tap-to-log-status-tiles` | **Date**: 2026-04-11 | **Spec**: [spec.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\spec.md)
**Input**: Feature specification from `C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\spec.md`

## Summary

Make the dashboard's core status tiles the primary one-tap logging surface for activities whose
status meaning already matches a single safe event: `pee`, `poop`, `food`, and `water`.
`awake` remains a read-only derived-status tile, while unsupported actions such as `play`,
`sleep`, and `wake` stay on a secondary quick-log path. The implementation should simplify the
dashboard by removing duplicated primary buttons for supported activities, keep tile urgency and
elapsed-time meaning obvious, and preserve the existing edit/delete recovery model if a tile is
tapped by mistake.

Technically, this feature can stay within the current FastAPI plus vanilla JavaScript app by
extending the derived dashboard snapshot with explicit tile action metadata, reusing the existing
`POST /api/events` event creation path for tile taps, and updating the client rendering so
supported tiles become accessible tap targets with lightweight affordances, pending protection,
and clear success or failure feedback. Because the dashboard contract and release behavior change,
the plan includes the required `test_app/docs` updates.

## Technical Context

**Language/Version**: Python 3.11+ (current workspace uses Python 3.13.5)  
**Primary Dependencies**: FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn, vanilla browser JavaScript  
**Storage**: SQLite via the existing `settings` and `events` tables; no schema change required for the first cut  
**Testing**: Manual regression via `test_app/docs/MANUAL_TEST_SCRIPT.md`, plus targeted FastAPI/integration coverage for dashboard snapshot metadata and supported tile logging behavior  
**Target Platform**: Mobile-first LAN-hosted web app used from phone browsers with websocket live updates  
**Project Type**: Single FastAPI web application with mirrored live and `test_app` entrypoints  
**Performance Goals**: Tile taps should feel as fast as today's quick actions, recompute guidance immediately, and propagate to connected devices without manual refresh  
**Constraints**: Preserve one-tap logging, keep exactly one banner recommendation, keep derived-state integrity, reduce dashboard duplication, preserve edit/delete recovery paths, avoid making read-only tiles look actionable, and keep the phone UI easy to scan  
**Scale/Scope**: One household, one puppy, low concurrency, two-device live usage, and a bounded first cut limited to safe one-to-one tile mappings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Preserve one-tap logging for core actions; no required typing or confirmation on the
  default path.  
  PASS: supported tiles log their matching activity directly, and unsupported actions remain
  one-tap through the secondary quick-log path.
- Preserve decision-first guidance; the banner must still resolve to exactly one primary
  recommendation in plain language.  
  PASS: the banner remains passive and authoritative; tile action affordances are secondary.
- Preserve derived-state integrity; sleep auto-closing, awake derivation, and immediate
  recalculation after edits/deletes must remain valid.  
  PASS: tile taps still create ordinary event rows through the existing event pipeline, so all
  current recomputation rules remain in force.
- Avoid duplicate concepts in UI copy, event types, and data modeling.  
  PASS WITH SCOPE GUARD: supported activities move to tiles as the primary surface, and the
  dashboard should not continue to show equivalent primary quick-action buttons for the same
  actions.
- If persistence, API behavior, or release workflow changes, include the required updates to
  `test_app/docs` in the plan scope.  
  PASS WITH REQUIRED DOC SYNC: update `DATA_CONTRACT.md`, `MANUAL_TEST_SCRIPT.md`,
  `README.md`, and any release notes affected by the simplified logging surface.

## Project Structure

### Documentation (this feature)

```text
specs/003-tap-to-log-status-tiles/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- dashboard-tile-actions.md
`-- tasks.md
```

### Source Code (repository root)

```text
app.py
requirements.txt
docs/
test_app/
|-- app.py
`-- docs/
tests/
|-- contract/
|-- guidance/
`-- integration/
```

**Structure Decision**: Extend the existing single-app layout in place. Keep `app.py` and
`test_app/app.py` aligned for shipped behavior, add any focused automated coverage under
`tests/`, and treat `test_app/docs` as required release-candidate documentation for the tile
action contract and regression flow.

## Phase 0: Research Summary

See [research.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\research.md).
Key outcomes:

- support tap-to-log on `pee`, `poop`, `food`, and `water` only; keep `awake` read-only because
  it is derived state rather than a directly loggable action
- keep tile actionability stable across urgency states so users do not have to relearn whether a
  tile is tappable from one moment to the next
- reuse `POST /api/events` and extend the dashboard snapshot with tile-action metadata instead of
  introducing a separate tile-only endpoint
- shrink the quick-action area to unsupported actions so the dashboard has one obvious primary
  surface for supported logs
- use pending locks plus toast-style success/error feedback instead of confirmations, preserving
  speed while reducing accidental double taps

## Phase 1: Design Summary

See [data-model.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\data-model.md),
[dashboard-tile-actions.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\contracts\dashboard-tile-actions.md),
and [quickstart.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\quickstart.md).

Design highlights:

- the server remains the source of truth for which tiles are tappable and which secondary quick
  actions remain visible
- supported tiles expose enough metadata for accessible button rendering without hiding their
  urgency, elapsed time, or read-only meaning
- tile taps create the same kind of event rows as existing quick actions, so live recalculation,
  websocket sync, recent activity, edit, and delete continue to work unchanged
- accidental logs remain recoverable through the existing recent-activity edit/delete path
- the first cut does not introduce new persistence, new event types, or state-specific tap rules

## Post-Design Constitution Check

- One-tap logging remains intact because supported tiles become the default path and unsupported
  actions remain available without required forms.
- Single-banner guidance remains intact because tile affordances are lightweight and do not add
  competing recommendations.
- Derived-state integrity remains intact because tile taps still flow through the ordinary event
  creation and recomputation pipeline.
- Duplicate concepts are reduced because supported quick-action buttons are removed from the main
  dashboard surface.
- Documentation updates remain first-class deliverables because the user-visible dashboard
  contract and manual regression expectations change.

## Complexity Tracking

No constitution violations are currently required.
