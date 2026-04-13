# Feature Specification: Tap-To-Log Status Tiles

**Feature Branch**: `003-tap-to-log-status-tiles`  
**Created**: 2026-04-11  
**Status**: Draft  
**Input**: User description: "Tap-to-log status tiles so core status tiles can act as the main one-tap logging path without losing their status meaning."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Log Core Events From Status Tiles (Priority: P1)

As a puppy owner, I want to tap a core status tile to log the matching event so I can use one
clear surface for both understanding what is due and recording what just happened.

**Why this priority**: This is the core value of the feature and the smallest slice that
delivers the intended simplification of the home screen.

**Independent Test**: A user can tap a core status tile, create the matching event in one
action, and immediately see the status and guidance update.

**Acceptance Scenarios**:

1. **Given** a core activity tile is shown on the dashboard, **When** the user taps that tile,
   **Then** the system logs the matching activity in one action.
2. **Given** the logged activity changes the active recommendation or urgency state, **When**
   the tile tap succeeds, **Then** the dashboard recalculates and shows the updated guidance
   immediately.
3. **Given** the same dashboard is open on a second device, **When** a tile is used to log an
   event, **Then** the second device reflects the update without a manual refresh.

---

### User Story 2 - Keep Status Meaning Clear While Tiles Become Tappable (Priority: P2)

As a puppy owner, I want status tiles to remain readable and trustworthy even after they become
tappable, so I never have to guess whether a tile is telling me something or asking me to do
something.

**Why this priority**: If the tiles become ambiguous, the feature would trade one kind of UI
duplication for a more serious clarity problem.

**Independent Test**: A user can look at the dashboard and still explain what each tile means,
while also recognizing that supported tiles can be used to log events.

**Acceptance Scenarios**:

1. **Given** the dashboard is visible, **When** the user scans the tiles, **Then** the tile
   still clearly communicates the need status, elapsed time, and urgency state.
2. **Given** a tile supports tap-to-log behavior, **When** the user views it, **Then** the tile
   gives a clear but lightweight indication that it can be tapped to log the matching event.
3. **Given** a tile represents a concept that should not be logged directly from the tile,
   **When** the dashboard is shown, **Then** that tile is not presented as a tap-to-log action.

---

### User Story 3 - Avoid Accidental Or Confusing Logging (Priority: P3)

As a puppy owner, I want tap-to-log tiles to feel safe and predictable, so I do not create
accidental events while trying to read the dashboard.

**Why this priority**: Fast logging is valuable only if it does not make the dashboard feel
fragile or easy to misuse.

**Independent Test**: A user can use the tappable tiles confidently, understand what happened
after a tap, and recover cleanly if they realize they logged something by mistake.

**Acceptance Scenarios**:

1. **Given** a user taps a supported status tile, **When** the log action is accepted, **Then**
   the system confirms the event in a way that makes the result obvious.
2. **Given** a user accidentally logs an event from a tile, **When** they notice the mistake,
   **Then** the event remains recoverable through the existing edit or delete path.
3. **Given** a tile is tapped while the system cannot complete the action, **When** the failure
   occurs, **Then** the user receives a clear error and the visible dashboard state remains
   truthful.

---

### Edge Cases

- What happens when a tile is due or overdue but the user taps it repeatedly in quick
  succession?
- How does the dashboard behave when a tile is tappable on one state but should be read-only in
  another?
- What happens when a tap-to-log action immediately changes the primary recommendation, such as
  clearing a due-soon or overdue state?
- How does the system distinguish between tiles that represent loggable activities and tiles
  that represent derived state, such as awake time?
- What happens when network interruption or a transient error occurs after the user taps a tile?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow supported status tiles to create the matching activity in a
  single tap.
- **FR-002**: The system MUST preserve the tile's primary role as a status display showing the
  current elapsed time, urgency, and care meaning.
- **FR-003**: The system MUST make it clear which tiles support tap-to-log behavior and which do
  not.
- **FR-004**: The system MUST limit tap-to-log behavior to activities that have a clear
  one-to-one relationship between the tile and the event being logged.
- **FR-005**: The system MUST recalculate guidance, tile urgency, and recent activity
  immediately after a successful tile-based log action.
- **FR-006**: The system MUST preserve existing multi-device live update behavior for tile-based
  log actions.
- **FR-007**: The system MUST preserve existing edit and delete recovery paths for events
  created through a tile tap.
- **FR-008**: The system MUST provide clear feedback after a successful or failed tile-based
  log action.
- **FR-009**: The system MUST avoid making read-only or derived-state tiles appear tappable when
  they are not valid one-tap logging targets.
- **FR-010**: The system MUST preserve the single primary recommendation and must not let
  tap-to-log interactions make the dashboard harder to interpret.
- **FR-011**: The system MUST continue to support a fast one-tap logging path for activities
  that are not represented by a tappable status tile.
- **FR-012**: The system MUST avoid introducing duplicate or competing primary logging surfaces
  that make the dashboard feel busier than before.

### Key Entities *(include if feature involves data)*

- **Status Tile**: A dashboard element that communicates elapsed time, urgency, and care status
  for a core need.
- **Tile Log Action**: A direct one-tap event creation path initiated from a supported status
  tile.
- **Supported Tile Activity**: A core activity whose tile meaning and logging action match
  closely enough to be safe and intuitive.
- **Tile Feedback State**: The visible confirmation or error state that tells the user what
  happened after tapping a tile.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In first-use evaluation, at least 90% of users can correctly identify which
  tiles can be tapped to log an event.
- **SC-002**: At least 85% of users can complete a core logging action from the dashboard
  without using separate quick-action buttons for supported tile activities.
- **SC-003**: At least 90% of users still correctly interpret what each core tile is telling
  them after the tap-to-log behavior is introduced.
- **SC-004**: In validation scenarios, tile-based log actions update the dashboard and live
  guidance correctly in 100% of core supported cases.
- **SC-005**: User confusion about whether the tile is informational or actionable decreases in
  follow-up evaluation compared with the pre-feature dashboard.

## Assumptions

- The app remains a single-household, single-puppy dashboard where speed and clarity matter more
  than deep workflow customization.
- Only tiles with a strong one-to-one mapping to a loggable activity should become tap targets
  in the first cut.
- The existing dashboard guidance model, recent activity log, and recovery paths remain in
  place.
- The first cut should reduce surface duplication without making the dashboard feel harder to
  scan.
- Activities that are not safely represented by status tiles should continue to use another
  one-tap entry path.
