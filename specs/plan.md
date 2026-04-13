# Implementation Plan: Simplify Expected Routine Editing

**Branch**: `002-simplify-routine-editing` | **Date**: 2026-04-11 | **Spec**: [spec.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\002-simplify-routine-editing\spec.md)
**Input**: Feature specification from `/specs/002-simplify-routine-editing/spec.md`

## Summary

Replace the current raw "Schedule and logic" threshold grid with a supportive routine overview
that derives a soft agenda from the existing age-band schedule and recent events. Preserve the
current one-tap logging path and banner logic, add a lower-complexity adjustment surface for
common routine changes, and keep exact threshold editing behind an explicit advanced mode. The
feature will use one underlying schedule-profile model so the overview, simple adjustments,
advanced editing, and age-upgrade proposal flow all describe the same routine instead of
introducing a second calendar system.

## Technical Context

**Language/Version**: Python 3.13.5 with inline browser JavaScript and HTML/CSS  
**Primary Dependencies**: FastAPI 0.116.1, Pydantic 2.11.7, Uvicorn, SQLite standard library driver  
**Storage**: SQLite `settings` key/value table plus `events` table; new routine profile state stored as JSON in `settings`  
**Testing**: `pytest` contract/integration coverage for API and derivation logic, plus `test_app/docs/MANUAL_TEST_SCRIPT.md` regression coverage  
**Target Platform**: LAN-first mobile-friendly web app opened from phone browsers and secondary household devices  
**Project Type**: Single-process web application with server-rendered page shell and inline client logic in `app.py`  
**Performance Goals**: Keep routine understanding available from the existing dashboard load path with no extra blocking fetches and no noticeable delay on a local network  
**Constraints**: Preserve one-tap logging, preserve the single banner recommendation, preserve current schedule meaning, avoid a rigid work-calendar feel, stay additive to current API behavior, update `test_app` and release docs if persistence or API shape changes  
**Scale/Scope**: One household, one puppy, one shared dashboard, low concurrent usage, hundreds to low-thousands of stored events

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: One-tap logging remains unchanged and stays visually primary above the routine area.
- `PASS`: The banner continues to resolve from the same advisory priority order; the new routine
  surface explains guidance but does not compete with it.
- `PASS`: Derived-state integrity is preserved by building the agenda from the same schedule and
  recent event calculations already used by the banner and tiles.
- `PASS`: The plan uses one schedule-profile model for overview, editing, and age-upgrade review,
  avoiding a second competing routine concept.
- `PASS WITH REQUIRED DOC SYNC`: This feature changes persisted settings and JSON state shape, so
  `test_app/app.py` and the relevant docs under `test_app/docs` are in scope for implementation.

## Project Structure

### Documentation (this feature)

```text
specs/002-simplify-routine-editing/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- routine-profile-api.md
`-- tasks.md
```

### Source Code (repository root)

```text
app.py
docs/
|-- FUTURE_RELEASE_SCHEDULE_PROFILE.md
specs/
|-- 002-simplify-routine-editing/
test_app/
|-- app.py
|-- docs/
|   |-- DATA_CONTRACT.md
|   |-- MANUAL_TEST_SCRIPT.md
|   `-- CHANGELOG.md
tests/
|-- contract/
|-- guidance/
`-- integration/
```

**Structure Decision**: Keep the existing single-file FastAPI application structure for the first
cut. Backend derivation logic, JSON contracts, and the routine UI remain in `app.py`, with the
release-candidate mirror in `test_app/app.py`. This avoids a repo-wide refactor while still
creating clean feature artifacts under `specs/002-simplify-routine-editing/`.

## Implementation Strategy

### UX Shape

- Replace the current `details > Schedule and logic` grid with a friendlier routine card that
  defaults to understanding mode.
- Present three layers in one place:
  1. `Overview`: age band, routine source, current block, next expected block, and a short
     agenda for the rest of the day.
  2. `Simple adjustments`: a deliberate edit mode for common changes to potty rhythm, meal
     rhythm, awake window, and nap length.
  3. `Age-upgrade review`: a proposal card for customized routines when the puppy has aged into
     a new recommendation band, with explicit accept and reject actions.
  4. `Advanced editing`: a secondary disclosure with exact threshold fields for the currently
     effective custom routine.
- Use a soft agenda layout with windows and supportive copy such as `Now`, `Next`, and `Later
  today`, not a drag-and-drop calendar or rigid hourly grid.

### Backend Shape

- Keep code-defined default schedule bands as the source of truth.
- Add `routine_profile_state` to the `settings` table as a JSON document that records:
  - `routine_mode`: `default_auto` or `custom_manual`
  - `custom_base_age_band_id` when the user has a saved custom routine
  - exact custom routine values
  - last reviewed recommendation band metadata
- Extend dashboard state with:
  - `live_state.routine_overview`
  - additional routine-source metadata on `live_state.schedule`
  - `live_state.routine_editor`
  - `live_state.routine_proposal`
- Add a dedicated routine profile save/reset API and a proposal-decision API rather than
  overloading the general settings endpoint.

### Scope Cuts For This First Implementation

- Default-following users auto-advance by age band.
- Customized routines stay anchored to the band they were last saved from until the user accepts
  a newer recommendation.
- The agenda covers `now`, `next`, and a limited set of upcoming routine windows for the current
  day; it is not a multi-day planner.
- Water remains represented in the raw schedule/profile data and may appear in explanatory copy,
  but it does not need to dominate the first-pass agenda UI.
- Advanced editing remains available inline behind explicit disclosure; it does not need a
  separate route or full-screen editor.

## Planned Artifacts

- [research.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\002-simplify-routine-editing\research.md): Decision log for the derived-agenda model, routine mode storage, proposal review flow, and API approach.
- [data-model.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\002-simplify-routine-editing\data-model.md): Canonical schedule-profile, custom routine, proposal, and agenda entities.
- [contracts/routine-profile-api.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\002-simplify-routine-editing\contracts\routine-profile-api.md): Additive API contract for state exposure plus save/reset and accept/reject behavior.
- [quickstart.md](C:\Users\mccau\Codex Projects\puppy_tracker\specs\002-simplify-routine-editing\quickstart.md): Implementation and regression walkthrough for the feature.

## Complexity Tracking

No constitution exceptions are required for this plan.
