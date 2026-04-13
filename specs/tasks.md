# Tasks: Simplify Expected Routine Editing

**Input**: Design documents from `/specs/002-simplify-routine-editing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/routine-profile-api.md, quickstart.md

**Tests**: Add automated contract and integration tests for the new routine profile state and
proposal decisions, plus manual regression/doc sync because this feature changes user behavior,
persistence, API shape, and release workflow.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the branch with the planning artifacts and create feature-specific test files.

- [X] T001 Create the implementation task scaffold in `specs/002-simplify-routine-editing/tasks.md`
- [X] T002 [P] Create routine contract test file in `tests/contract/test_routine_profile_api.py`
- [X] T003 [P] Create routine integration test file in `tests/integration/test_simplified_routine_flow.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared routine-profile state and derivation primitives all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add routine profile state models, defaults, and helpers in `app.py`
- [X] T005 Add routine profile persistence helpers for `routine_profile_state` in `app.py`
- [X] T006 Add effective routine/profile-source/proposal derivation helpers in `app.py`
- [X] T007 Mirror the shared routine profile foundation in `test_app/app.py`

**Checkpoint**: Foundation ready. User story work can begin.

---

## Phase 3: User Story 1 - Understand The Routine Without Editing (Priority: P1) 🎯 MVP

**Goal**: Replace the dense schedule threshold card with a calmer overview that explains the day’s routine and auto-advances when the user is still following defaults.

**Independent Test**: A first-time user can open the routine area, understand the current age-based routine, see `Now / Next / Later today`, and a default-following routine updates automatically when the puppy ages into a new recommendation band.

### Tests for User Story 1

- [X] T008 [P] [US1] Add routine overview state contract assertions to `tests/contract/test_routine_profile_api.py`
- [X] T009 [P] [US1] Add default auto-advance integration coverage to `tests/integration/test_simplified_routine_flow.py`

### Implementation for User Story 1

- [X] T010 [US1] Extend `/api/state` routine overview payload generation in `app.py`
- [X] T011 [US1] Replace the default routine UI with the agenda-style overview in `app.py`
- [X] T012 [US1] Mirror the overview API and UI behavior in `test_app/app.py`

**Checkpoint**: User Story 1 is fully functional and testable on its own.

---

## Phase 4: User Story 2 - Make Common Changes With Low Friction (Priority: P2)

**Goal**: Let users save a simplified custom routine, keep it stable across age transitions, and review age-based proposals with explicit accept or reject actions.

**Independent Test**: A user can save a simple custom routine, see the app hold that routine when the puppy ages, and explicitly accept or reject the new recommendation.

### Tests for User Story 2

- [X] T013 [P] [US2] Add routine save/reset/proposal decision contract coverage to `tests/contract/test_routine_profile_api.py`
- [X] T014 [P] [US2] Add custom routine age-transition accept/reject integration coverage to `tests/integration/test_simplified_routine_flow.py`

### Implementation for User Story 2

- [X] T015 [US2] Add routine profile save/reset/decision endpoints in `app.py`
- [X] T016 [US2] Implement the simple-adjustment editor and proposal review UI in `app.py`
- [X] T017 [US2] Mirror the save/reset/decision endpoints and UI in `test_app/app.py`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Reach Advanced Controls Deliberately (Priority: P3)

**Goal**: Preserve exact threshold editing for engaged users without making it the default first-open experience.

**Independent Test**: A user can intentionally open advanced controls, review or change exact thresholds, cancel safely, and return to the simplified overview without losing context.

### Tests for User Story 3

- [X] T018 [P] [US3] Add advanced-edit contract assertions to `tests/contract/test_routine_profile_api.py`
- [X] T019 [P] [US3] Add advanced-edit integration coverage to `tests/integration/test_simplified_routine_flow.py`

### Implementation for User Story 3

- [X] T020 [US3] Expose advanced-edit field metadata and validation in `app.py`
- [X] T021 [US3] Add deliberate advanced-edit UI state and cancel behavior in `app.py`
- [X] T022 [US3] Mirror advanced-edit behavior in `test_app/app.py`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish release-candidate parity, regression coverage, and documentation for the completed feature.

- [X] T023 Update routine profile contract documentation in `test_app/docs/DATA_CONTRACT.md`
- [X] T024 Update manual regression coverage in `test_app/docs/MANUAL_TEST_SCRIPT.md`
- [X] T025 [P] Update release notes/decisions for the feature in `test_app/docs/CHANGELOG.md` and `test_app/docs/DECISIONS.md`
- [X] T026 [P] Update supporting release-candidate docs in `test_app/README.md` and `test_app/docs/RELEASE_CHECKLIST.md`
- [X] T027 Run the targeted automated routine tests for `tests/contract/test_routine_profile_api.py` and `tests/integration/test_simplified_routine_flow.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies
- **Phase 2**: Depends on Phase 1 and blocks all story work
- **Phase 3**: Depends on Phase 2 and is the MVP
- **Phase 4**: Depends on Phase 3 because it extends the same routine surface and API
- **Phase 5**: Depends on Phases 3 and 4
- **Phase 6**: Depends on all desired story phases being complete

### User Story Dependencies

- **US1 (P1)**: Starts after the foundational routine-profile helpers exist
- **US2 (P2)**: Builds on US1’s overview payload and UI, but remains independently testable once added
- **US3 (P3)**: Builds on the same editor state from US2 and remains independently testable once added

### Within Each User Story

- Tests should be written before or alongside implementation and should fail before the final implementation is complete
- Backend state/contract updates precede UI rendering that depends on them
- Main app and `test_app` changes touching the same feature behavior should remain aligned before the phase is marked complete

### Parallel Opportunities

- T002 and T003 can run in parallel
- T008 and T009 can run in parallel
- T013 and T014 can run in parallel
- T018 and T019 can run in parallel
- T025 and T026 can run in parallel

---

## Parallel Example: User Story 2

```text
Task: "Add routine save/reset/proposal decision contract coverage in tests/contract/test_routine_profile_api.py"
Task: "Add custom routine age-transition accept/reject integration coverage in tests/integration/test_simplified_routine_flow.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Setup
2. Complete Foundational
3. Complete User Story 1
4. Validate the routine overview independently

### Incremental Delivery

1. Ship the simpler overview and default auto-aging path
2. Add simple customization plus proposal accept/reject
3. Add advanced editing deliberately, not by default
4. Sync `test_app` docs and regression coverage before closing

### Notes

- Keep one underlying schedule-profile model across overview, simple editing, advanced editing, and proposal review
- Preserve one-tap logging and the single recommendation banner throughout
- Do not silently rewrite a customized routine when the puppy ages into a new recommendation band
