# Feature Specification: Simplify Expected Routine Editing

**Feature Branch**: `002-simplify-routine-editing`  
**Created**: 2026-04-11  
**Status**: Released on `master`  
**Input**: User description: "Simplify Expected Routine Editing so first-time users understand the expected routine without feeling overwhelmed or abandoning the tab."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand The Routine Without Editing (Priority: P1)

As a puppy owner, I want to open the expected routine area and immediately understand my
puppy's current routine and the next expected care block without being dropped into a dense
editing surface.

**Why this priority**: The reported problem is first-open abandonment caused by the feature
feeling too complicated before users even understand what they are looking at.

**Independent Test**: A first-time user can open the expected routine area, identify the
active routine and upcoming care expectations, and leave with a clear understanding without
editing anything.

**Acceptance Scenarios**:

1. **Given** a user opens the expected routine area for the first time, **When** the section
   expands, **Then** the first view emphasizes understanding the current routine rather than a
   full editing interface.
2. **Given** the puppy has an active expected routine, **When** the user views the simplified
   routine area, **Then** they can see the current age band, the next expected care block, and
   whether guidance is default or customized.
3. **Given** the routine has not been customized yet, **When** the user opens the routine
   area, **Then** the app explains the current default routine in plain language instead of
   presenting an intimidating blank or dense editor.
4. **Given** the user is trying to understand what the day looks like, **When** they open the
   simplified routine area, **Then** the app presents a calendar-inspired day view or agenda
   that feels familiar and easy to scan without resembling a dense business scheduling tool.

---

### User Story 2 - Make Common Changes With Low Friction (Priority: P2)

As a puppy owner, I want to make simple routine adjustments without feeling like I need to
manage a full configuration system.

**Why this priority**: Understanding the routine is the first problem, but the feature still
needs a practical path for common changes or it will not be useful after the first read.

**Independent Test**: A user can make a routine change they consider simple, save it, and see
the updated guidance without needing to interpret every advanced field.

**Acceptance Scenarios**:

1. **Given** a user wants to make a common routine change, **When** they choose to adjust the
   routine, **Then** the app offers a lower-complexity path that does not require editing every
   routine detail.
2. **Given** the user saves a simplified routine change, **When** the save completes,
   **Then** the schedule explanation and active guidance immediately reflect the updated
   routine.
3. **Given** a user decides not to change anything, **When** they leave the routine area,
   **Then** no accidental routine edits or confusing draft state remain.
4. **Given** a user is following the default routine, **When** the puppy ages into a new
   recommendation band, **Then** the expected routine updates automatically to the new default
   guidance without requiring manual editing.
5. **Given** a user has a customized routine, **When** the puppy ages into a new recommendation
   band, **Then** the app preserves the saved custom routine and shows a reviewable proposal for
   what would usually change at the new age.
6. **Given** the app shows a reviewable age-based adjustment proposal, **When** the user accepts
   or rejects it, **Then** the app applies that choice clearly and does not leave the proposal in
   an ambiguous state.

---

### User Story 3 - Reach Advanced Controls Deliberately (Priority: P3)

As a more engaged puppy owner, I want advanced routine controls to remain available when I
need them, but not forced on everyone by default.

**Why this priority**: The product still needs depth for users who want detailed control, but
the advanced layer should no longer dominate the first-open experience.

**Independent Test**: A user can intentionally enter an advanced routine-editing mode, review
or change detailed controls, and return to the simpler understanding view without losing
context.

**Acceptance Scenarios**:

1. **Given** a user wants deeper control over the routine, **When** they opt into advanced
   editing, **Then** the app exposes the full routine controls with a clear indication that the
   user has moved beyond the simpler view.
2. **Given** a user already has customized routine data, **When** they open the simplified
   routine area, **Then** the app accurately represents their current routine without requiring
   immediate entry into advanced editing.
3. **Given** a user enters advanced editing and then backs out, **When** they return to the
   default routine view, **Then** the app preserves orientation and does not make the routine
   feel harder to understand than before.

---

### Edge Cases

- What happens when the user has existing customized routine data that does not fit a simpler
  presentation cleanly?
- How does the app behave when there is no customized routine and the user is seeing only the
  age-based default routine?
- What happens when the planned routine includes overlapping, tightly spaced, or off-schedule
  blocks that would be hard to show clearly in a simplified day view?
- What happens when a user starts exploring advanced controls but leaves without saving?
- How does the system explain routine expectations when the puppy is off schedule because recent
  real events conflict with the planned routine?
- What happens when the active recommendation is urgent and the user opens the routine area
  mainly to understand why the app is recommending something now?
- What happens when the puppy ages into a new recommendation band while the user is on a custom
  routine and rejects the proposed changes?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present the expected routine in a first-open view that is focused
  on understanding the current routine rather than immediately exposing the full editing
  surface.
- **FR-002**: The first-open routine view MUST clearly show the active routine context,
  including the current age band, the current routine source, and the next expected care block
  or time window.
- **FR-002a**: The first-open routine view MUST use a calendar-inspired day view, agenda view,
  or similarly familiar schedule presentation that helps users understand the day's flow at a
  glance without requiring them to interpret a dense editing interface.
- **FR-002b**: The simplified schedule presentation MUST highlight what is happening now and
  what is expected next.
- **FR-003**: The system MUST explain the default routine in plain language when the user has
  not customized the routine.
- **FR-003a**: When the user is following the default routine, the effective routine MUST advance
  automatically as the puppy ages into a new recommendation band.
- **FR-004**: The system MUST provide a lower-complexity path for common routine adjustments so
  users can make typical changes without navigating every advanced routine field.
- **FR-004a**: When the user has a customized routine and the puppy ages into a new recommendation
  band, the system MUST preserve the saved custom routine and MUST NOT auto-apply the new
  recommendation.
- **FR-004b**: When a new age-based recommendation is available for a customized routine, the
  system MUST present a reviewable proposal that explains the recommended changes in plain language.
- **FR-004c**: The age-based proposal flow MUST allow the user to explicitly accept or reject the
  proposed changes.
- **FR-004d**: If the user rejects an age-based proposal, the system MUST preserve the current
  custom routine and mark the proposal as handled until a later recommendation change requires a
  new review.
- **FR-005**: The system MUST preserve access to advanced routine controls for users who want
  deeper customization.
- **FR-006**: The system MUST make the boundary between simple routine understanding, simple
  adjustment, and advanced editing clear to the user.
- **FR-007**: The system MUST preserve the existing routine meaning and guidance recalculation
  behavior after any saved routine change.
- **FR-008**: The system MUST continue to show whether active routine guidance is coming from
  defaults, user customization, or recent real events.
- **FR-009**: The system MUST preserve one-tap logging and the single primary recommendation as
  the main dashboard path while the routine area is simplified.
- **FR-010**: The system MUST allow users to exit the routine area without creating accidental
  edits or unclear unsaved state.
- **FR-011**: The system MUST accurately represent already-customized routine data in the
  simplified routine experience, even when the user does not open advanced controls.
- **FR-012**: The system MUST avoid introducing duplicate or conflicting schedule concepts that
  make the routine harder to interpret than before.
- **FR-013**: The simplified schedule presentation MUST feel supportive and familiar rather than
  like a rigid business calendar, so routine guidance remains approachable for household use.
- **FR-014**: The system MUST make it clear whether the active routine is auto-following the
  current age recommendation, using a saved custom routine, or awaiting a user decision on a new
  age-based proposal.

### Key Entities *(include if feature involves data)*

- **Routine Overview**: The user-facing explanation of the current expected routine, including
  what the puppy is generally expected to do next and why.
- **Schedule View**: A calendar-inspired day or agenda presentation that shows the expected flow
  of the puppy's day in a familiar, easy-to-scan format.
- **Simple Routine Adjustment**: A lower-complexity change path for common updates to the
  expected routine without exposing every detailed setting.
- **Advanced Routine Editing Mode**: A deliberate deeper customization mode for users who want
  full routine control.
- **Routine Source State**: The explanation of whether the active routine is coming from
  defaults, customized routine data, or recent real-life events affecting guidance.
- **Age-Based Adjustment Proposal**: A reviewable set of recommended schedule changes shown when a
  puppy has aged into a new recommendation band but the user is still using a custom routine.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In first-use evaluation, at least 90% of users can explain what the expected
  routine section is showing within 30 seconds of opening it.
- **SC-002**: In first-use evaluation, at least 90% of users can identify the next expected
  care block or routine expectation without entering advanced editing.
- **SC-003**: The first-open abandonment rate for the expected routine area decreases from the
  reported 50% baseline to below 20%.
- **SC-003a**: In first-use evaluation, at least 85% of users describe the routine surface as
  easy to follow or familiar rather than confusing or overly technical.
- **SC-004**: At least 85% of users can complete a common routine adjustment on their first try
  without needing advanced controls.
- **SC-005**: In regression validation, saved routine changes continue to update active guidance
  and routine explanations correctly in 100% of core scenarios.

## Assumptions

- The app remains a single-household, single-puppy product with LAN-first usage expectations.
- The existing underlying schedule and advisory model remains in place; this feature changes
  how routine understanding and editing are presented rather than redefining core care logic.
- Advanced routine controls remain valuable for some users, but they should become a deliberate
  deeper step rather than the default first-open experience.
- The first cut should optimize for clarity and confidence over maximum configurability on the
  initial view.
- A calendar-inspired day or agenda view is a reasonable first-cut pattern because many users
  already understand that mental model, but the design should stay lighter and friendlier than
  a work calendar.
- The release should preserve current routine data and should not require users to rebuild
  customized schedules from scratch.
- Default-following users should get age-based routine updates automatically, while custom-routine
  users should review and explicitly accept or reject new age-based recommendations.
- The simplified dashboard keeps one-tap logging on the status tiles, including the awake/asleep
  toggle on the `Awake` tile, while routine and schedule configuration live under `Settings`.
