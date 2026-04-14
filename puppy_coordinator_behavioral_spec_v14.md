# Puppy Coordinator Behavioral Spec (v14.4)

# 1. Core Principles

- One tap logging is the default path
- Users correct data after, not before
- System assumes reasonable defaults
- Output must guide action, not display raw data
- Minimize user effort, maximize puppy outcome

# 2. Global Invariants (Must Never Break)

- Logging a core activity requires 1 tap or less
- No required typing for core flows
- Banner always shows exactly one recommendation
- Sleep is always auto-closed by the next wake or later activity
- Awake time is derived, never manually entered
- System must function with partial or missing data
- UI must not introduce duplicate concepts

# 3. Core Components

## 3.1 Needs Banner

### Purpose
Tell the user the single most important action right now.

### User Interaction
None. Passive.

### System Behavior
System selects exactly one recommendation using priority:

1. Overdue potty
2. Overdue food
3. Overdue sleep
4. Due-soon potty
5. Due-soon food
6. Due-soon sleep
7. Otherwise -> "All good for now"

### Edge Cases

- No data -> "No data yet"
- Conflicting signals -> highest priority wins

### Constraints

- Must never show multiple actions
- Must never be blank

### Examples

- "Take her out. Last pee was 95m ago."
- "All good for now"

## 3.2 Status Tiles

### Purpose
Provide fast situational awareness across key needs.

### Tiles

- Pee
- Poop
- Food
- Water
- Awake

### Format
"Pee, 36m ago, Due soon"

### States

- On track
- Due soon
- Overdue
- Unknown when there is not enough data

### Behavior

- Entire tile color reflects state
- Awake tile can span wider than the others
- Awake tile is also the sleep/wake logging tile
- Awake tile copy should read in this order: state, elapsed time, `Since ...`, optional action hint
- Tiles update immediately after any event change

### Constraints

- No duplicate timing concepts
- No stale values after event changes

## 3.3 Sleep System

### Purpose
Track rest and protect against overtired periods and accidents.

### Behavior

- Sleep logs start time = now
- Sleep assumes a target wake time from the current schedule
- Wake ends sleep
- Any later non-sleep activity can end sleep early

### Rules

- No overlapping sleep periods
- Sleep duration is derived from start -> resolved end
- End source may be projected wake, wake event, or later activity

### Edge Cases

- Interrupted sleep recalculates duration
- Missing wake is resolved by next activity or projected end

### Constraints

- Sleep must never remain logically open after a later wake or activity

## 3.4 Awake State

### Purpose
Primary driver of recommendations.

### Behavior

- Awake = time since last sleep ended
- If no sleep block is available, awake can fall back to time since the most recent valid event
- The `Awake` tile shows whether the puppy is currently awake or asleep
- Tapping the `Awake` tile logs `sleep` when awake or `wake` when asleep

### Constraints

- Never manually entered

## 3.5 Activity Log

Editable history of events.

### Behavior

- Shows newest events first
- Supports edit and delete
- Changes recalculate live state immediately

## 3.6 Edit System

User can modify:

- time
- activity
- actor
- note
- sleep target or duration where relevant

### Constraints

- Edit flow supports correction after quick logging
- Editing must update derived state immediately

## 3.7 Schedule Logic

Defines thresholds for urgency states and default sleep targets.

### Current Inputs

- puppy birth date when known
- otherwise a reasonable default age assumption

### Future Direction

- The active schedule band should be visible to the human
- The system should eventually expose the expected routine for the puppy's current age in plain language
- The underlying thresholds should be captured as a versioned schedule profile so they can be adjusted later without changing the event model
- The advanced schedule and expected routine controls should live inside Settings rather than on the default dashboard surface
- See [`docs/FUTURE_RELEASE_SCHEDULE_PROFILE.md`](C:\Users\mccau\Codex Projects\puppy_tracker\docs\FUTURE_RELEASE_SCHEDULE_PROFILE.md) for the implementation proposal to carry into a future release

## 3.8 Settings Surface

### Direction

- Keep the default dashboard as simple as possible
- Put `Schedule and logic` and `Expected routine` inside a compact settings drawer
- Do not show a standalone quick-action strip, actor chooser, or accident toggle on the dashboard

## 3.9 Version Indicator

Displayed near Live status when present in the UI.

## 3.10 Elimination Events

### Direction

- Pee and poop remain core elimination actions
- Accident meaning should be attached to elimination events, not represented as a standalone activity

### Constraints

- Accidents still reset the relevant timers
- UI should not create a duplicate concept by offering both an accident event type and an accident flag for the same outcome

# 4. System Logic

## 4.1 Potty Timing

Potty guidance is age-based and should use the active schedule band.

## 4.2 Food Timing

Food guidance is age-based and should use the active schedule band.

## 4.3 Water Timing

Water guidance is age-based and should use the active schedule band.

## 4.4 Awake Timing

Sleep guidance is age-based and should use the active schedule band.

## 4.5 Banner Logic

Priority order:

1. Sleeping now
2. Potty likely overdue after food
3. Pee overdue
4. Sleep overdue
5. Food overdue
6. Potty soon
7. Sleep soon
8. Otherwise -> All good for now

### Constraints

- Banner must show exactly one recommendation
- Banner must be explainable in plain language

## 4.6 State Transitions

States:

- Awake
- Sleeping

Transitions:

- Sleep -> Sleeping
- Wake -> Awake
- Any later non-sleep activity -> Awake

# 5. Data Model Direction

Each event needs:

- stable id
- activity type
- actor
- event timestamp in UTC
- optional note
- created-at timestamp

Future elimination detail can extend this with an accident flag without reintroducing a standalone Accident activity.

# 6. Default Value System

All quick actions assume:

- current time
- valid context
- a reasonable default duration when needed for sleep or play

# 7. Do Not Regress

- No required typing for core logging
- No multi-step logging for core actions
- No duplicate concepts
- No stale derived state after edits
- No mismatch between quick-log behavior and edit behavior

# 8. Non-Goals

- No notifications yet
- No ML
- No multi-puppy support yet

# 9. Future

- Accident flag on elimination events
- Notifications
- Adaptive timing
- Pattern detection
- Safer release workflow and migration support

# Summary

Decision assistant, not just a tracker.
