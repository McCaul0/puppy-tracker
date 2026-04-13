# Tasks: Tap-To-Log Status Tiles

**Input**: Design documents from `C:\Users\mccau\Codex Projects\puppy_tracker\specs\003-tap-to-log-status-tiles\`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Add and run focused automated validation for the tile-action snapshot and logging flow,
plus the required release-candidate manual regression docs because the dashboard behavior and API
snapshot change.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated
independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the feature-specific validation path used across the tap-to-log work

- [X] T001 Add tap-to-log status tile integration coverage in `C:\Users\mccau\Codex Projects\puppy_tracker\tests\integration\test_tap_to_log_status_tiles.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared dashboard snapshot metadata and fallback quick-action model required by all stories

**CRITICAL**: No user story work should begin until this phase is complete

- [X] T002 Add tappable status-tile metadata and `secondary_quick_actions` derivation in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py`
- [X] T003 [P] Mirror tappable status-tile metadata and `secondary_quick_actions` derivation in `C:\Users\mccau\Codex Projects\puppy_tracker\app.py`

**Checkpoint**: The server snapshot can now describe which tiles are tappable and which quick actions remain outside the tile grid

---

## Phase 3: User Story 1 - Log Core Events From Status Tiles (Priority: P1) MVP

**Goal**: Let owners tap supported status tiles to log the matching event and see guidance refresh immediately

**Independent Test**: Tap `pee`, `poop`, `food`, and `water` on the dashboard and confirm the event saves, the banner and tiles recalculate, and the new event appears in recent activity

### Implementation for User Story 1

- [X] T004 [US1] Render supported status tiles as the primary tap-to-log surface and reduce the quick-action strip to unsupported actions in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py`
- [X] T005 [US1] Sync the supported-tile logging surface and reduced quick-action strip in `C:\Users\mccau\Codex Projects\puppy_tracker\app.py`

**Checkpoint**: Supported tile logs work end-to-end and the dashboard no longer shows duplicate primary buttons for those activities

---

## Phase 4: User Story 2 - Keep Status Meaning Clear While Tiles Become Tappable (Priority: P2)

**Goal**: Preserve status readability and keep read-only tiles from looking actionable

**Independent Test**: Scan the dashboard and confirm supported tiles still read as status cards first, while `awake` remains clearly read-only

### Implementation for User Story 2

- [X] T006 [US2] Add lightweight tap affordances, accessible labels, and read-only derived-tile treatment in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py`
- [X] T007 [US2] Sync lightweight affordances, accessible labels, and read-only derived-tile treatment in `C:\Users\mccau\Codex Projects\puppy_tracker\app.py`

**Checkpoint**: The dashboard remains easy to scan and users can still distinguish status meaning from actionability

---

## Phase 5: User Story 3 - Avoid Accidental Or Confusing Logging (Priority: P3)

**Goal**: Make tile logging feel safe with clear feedback and recovery paths

**Independent Test**: Rapidly tap a supported tile, verify repeated in-flight submissions are blocked, and confirm success or failure feedback is obvious without corrupting visible state

### Implementation for User Story 3

- [X] T008 [US3] Add in-flight tile locking plus success and error feedback for tile-based logging in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py`
- [X] T009 [US3] Sync in-flight tile locking plus success and error feedback in `C:\Users\mccau\Codex Projects\puppy_tracker\app.py`

**Checkpoint**: Tile-based logging feels safe, predictable, and recoverable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Sync release-candidate docs and validate the feature end-to-end

- [X] T010 Update the dashboard snapshot contract for tappable tiles in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DATA_CONTRACT.md`
- [X] T011 Update the release-candidate manual regression flow for tappable tiles in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\MANUAL_TEST_SCRIPT.md`
- [X] T012 [P] Update the release-candidate changelog for tap-to-log status tiles in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\CHANGELOG.md`
- [X] T013 [P] Update release smoke-test expectations for tappable tiles in `C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\RELEASE_CHECKLIST.md`
- [X] T014 Run tap-to-log validation in `C:\Users\mccau\Codex Projects\puppy_tracker\tests\integration\test_tap_to_log_status_tiles.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all story work
- **US1 (Phase 3)**: Starts after Foundational; recommended MVP
- **US2 (Phase 4)**: Starts after Foundational and refines the surfaces introduced in US1
- **US3 (Phase 5)**: Starts after Foundational and builds on the logging flow from US1
- **Polish (Phase 6)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1**: No dependency on later stories once foundational snapshot metadata exists
- **US2**: Builds on the tile rendering introduced in US1
- **US3**: Builds on the tile submission flow introduced in US1

### Within Each User Story

- Server-side snapshot changes should land before client rendering changes
- Rendering changes should land before feedback and regression validation
- Documentation and validation should happen after the app behavior is stable

### Parallel Opportunities

- T002 and T003 can proceed in parallel once the task shape is agreed
- T012 and T013 can proceed in parallel during polish

---

## Parallel Example: User Story 1

```text
Task: "Render supported status tiles as the primary tap-to-log surface and reduce the quick-action strip to unsupported actions in C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py"
Task: "Sync the supported-tile logging surface and reduced quick-action strip in C:\Users\mccau\Codex Projects\puppy_tracker\app.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases
2. Complete User Story 1
3. Validate supported tile logging end-to-end
4. Stop and review before refining affordances and safety behavior

### Incremental Delivery

1. Add the shared tile-action contract
2. Ship supported tile logging
3. Refine status clarity and read-only treatment
4. Add accidental-log protection and feedback
5. Sync release docs and run validation

### Validation-First Wrap-Up

1. Confirm the snapshot contract exposes tappable tile metadata
2. Confirm the dashboard uses tiles as the main supported logging surface
3. Confirm pending/error handling keeps the UI truthful
4. Update release-candidate docs
5. Run the focused tap-to-log validation test

---

## Notes

- Tasks are written against the current single-app plus `test_app` structure in this repository
- The plan intentionally keeps write behavior on `POST /api/events` instead of adding a tile-specific endpoint
- Release-candidate docs are part of the feature because the dashboard contract and regression flow change
