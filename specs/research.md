# Research: Simplify Expected Routine Editing

## Decision 1: Use one derived agenda instead of a second calendar model

- Decision: Build the routine surface from the existing schedule thresholds plus recent events,
  then present that derived state as a soft agenda with `Now`, `Next`, and `Later today`.
- Rationale: The current app already computes age-band thresholds, sleep state, awake time, and
  the primary recommendation. Reusing that logic keeps the banner, tiles, and routine overview
  aligned. It also avoids introducing a second source of truth that could drift from the
  advisory model.
- Alternatives considered:
  - Full visual calendar with fixed hourly slots. Rejected because the product is interval-based,
    not appointment-based, and the result would feel too rigid for household use.
  - Static explanatory copy only. Rejected because it would help understanding somewhat but would
    not satisfy the requested calendar-inspired day or agenda mental model.
  - Separate routine planner route. Rejected for the first cut because it would hide the routine
    behind extra navigation and increase implementation scope.

## Decision 2: Keep defaults in code and store routine mode plus custom profile state in SQLite

- Decision: Persist routine state as one JSON object that distinguishes `default_auto` from
  `custom_manual`, stores a locked custom base age band for customized routines, and records the
  last reviewed recommendation band.
- Rationale: Default schedules can then auto-advance by age without special handling, while
  customized routines remain stable across age transitions until the user explicitly accepts a new
  recommendation.
- Alternatives considered:
  - Store all default schedules in SQLite. Rejected because it adds migration and admin overhead
    without solving an immediate product need.
  - Store only overrides against the currently active band. Rejected because a later age-band
    change would silently alter the effective custom routine.
  - Make edits apply across all future age bands. Rejected for the first cut because it adds
    unclear product behavior when the puppy ages into a different band.

## Decision 3: Simple adjustments and advanced editing should write to the same fields

- Decision: The simple adjustment surface will edit a curated subset of the schedule profile,
  but the saved payload will still be the same exact threshold override object used by advanced
  editing.
- Rationale: This keeps the system mentally consistent. The simple view is a friendlier way to
  change the same routine, not a different customization system.
- Alternatives considered:
  - Separate "simple adjustment" data model. Rejected because it creates duplicate concepts and
    awkward synchronization rules.
  - Advanced-only editing. Rejected because it does not solve the first-time-user overwhelm that
    motivated the feature.

## Decision 4: Add dedicated routine-profile save/reset and proposal-decision APIs

- Decision: Extend `GET /api/state` with routine overview and proposal data, introduce dedicated
  save/reset endpoints for routine customization, and add an explicit accept/reject endpoint for
  age-based proposals.
- Rationale: The existing settings endpoint is about household metadata and activity names. A
  dedicated routine API keeps routine editing and proposal review isolated, simplifies validation,
  and makes the new contract easier to test.
- Alternatives considered:
  - Fold routine editing into `POST /api/settings`. Rejected because it mixes unrelated concerns
    and increases the chance of accidental edits.
  - Frontend-only temporary editing with no persistence. Rejected because the feature requires
    saved routine changes to affect guidance.

## Decision 4a: Proposal review must support explicit accept and reject outcomes

- Decision: When a customized routine is older than the current recommendation band, the app
  should present a proposal that the user can accept or reject, with both outcomes saved.
- Rationale: Users need control over their custom routine. Accepting should update the saved
  routine toward the new recommendation, while rejecting should preserve the current routine and
  suppress the proposal until a later recommendation change.
- Alternatives considered:
  - Auto-apply the new recommendation. Rejected because it breaks trust for customized routines.
  - Show informational text with no decision. Rejected because it leaves the app in a nagging,
    unresolved state.

## Decision 5: Agenda emphasis should be "supportive rhythm," not exhaustive detail

- Decision: The default first-open routine view should foreground the active age band, source
  state, current block, next block, and a short list of upcoming windows. Raw thresholds remain
  available but not dominant.
- Rationale: The feature goal is quick comprehension for first-time users. Showing the entire
  threshold table first would preserve the current overwhelm.
- Alternatives considered:
  - Keep the current dense threshold list and just restyle it. Rejected because it does not
    materially change the cognitive load.
  - Hide all numeric detail. Rejected because users still need to understand what has been saved
    and advanced controls must remain available.

## Decision 6: Documentation and release-candidate sync are mandatory

- Decision: Treat `test_app` as in-scope for implementation if the plan is executed, including
  API contract docs and manual regression guidance.
- Rationale: The constitution requires release-candidate parity for persistence, API, and
  user-facing behavior changes. Routine editing touches all three.
- Alternatives considered:
  - Update live app only. Rejected because it breaks the documented release discipline.
