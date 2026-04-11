# Puppy Coordinator Backlog

This file is the high-level backlog for future product and workflow work.

Use the constitution for enduring rules and constraints.
Use this backlog for candidate features and improvements that may later become
Spec Kit feature specs.

## How To Use This Backlog

- Keep items high level until they are important enough to spec
- Move an item into Spec Kit when you are ready to define behavior, scope, and
  implementation details
- Update or remove items freely as priorities change

## Next Up

### Tap-To-Log Status Tiles

Why it matters:
- The status tiles and quick-log buttons are nearly the same surface for core
  activities
- Letting status tiles act as the entry path could simplify the home screen and
  reduce duplicate controls

Likely first scope:
- allow core status tiles to log the matching event directly
- keep separate buttons only for actions that do not have a matching status
  tile
- preserve one-tap logging and keep the status meaning clear even when the tile
  becomes tappable

### Simplify Expected Routine Editing

Why it matters:
- The newer schedule block editor appears to be too heavy for some users on
  first open
- A 50 percent first-open abandonment signal suggests the current interaction
  may be asking for too much too early

Likely first scope:
- identify the first-open pain points in the schedule block area
- propose a lighter-weight presentation that feels less intimidating
- consider separating read-only schedule explanation from advanced routine
  editing
- validate whether the right fix is simplification, progressive disclosure, or
  a different editor model entirely

## Later

### PIN Or Password Auth

Why it matters:
- The app is currently optimized for trusted LAN use
- Auth is the clearest path to safer access if usage expands beyond a tightly
  controlled home setup

Likely first scope:
- simple household PIN or password gate
- low-friction remember-this-device behavior
- preserve fast logging once inside the app

### Export And Day History Tools

Why it matters:
- The app stores useful local history, but it is still hard to review or export
  outside the live interface

Likely first scope:
- filter by day or date range
- export event history in a simple format such as CSV or JSON
- keep derived-state rules intact during export

### Adjustable Schedule Profile

Why it matters:
- Default age-based guidance is useful, but real puppies vary
- The current expected-routine controls may need product simplification before
  wider customization is encouraged

Likely first scope:
- allow overrides to the default schedule profile
- support reset back to defaults
- keep overrides separate from event history

### Push Notifications

Why it matters:
- Notifications could make the app more proactive instead of purely reactive

Likely first scope:
- opt-in potty reminders
- simple due-soon or overdue notification rules
- only after auth and deployment expectations are clearer

### Roles And Activity Audit History

Why it matters:
- More accountability and recoverability will matter as the app grows

Likely first scope:
- record who changed what
- preserve edit/delete history for review
- avoid slowing down the quick-log path

## Workflow And Release Improvements

### Safer Release And Migration Workflow

Why it matters:
- The project already has a release-candidate flow in `test_app`
- Safer promotion steps and migration support would reduce production risk

Likely first scope:
- explicit migration checklist for schema-sensitive changes
- more structured promotion steps
- clearer rollback notes

### Better Regression Coverage

Why it matters:
- The app relies heavily on behavior that is easy to regress quietly:
  one-tap logging, banner priority, sleep resolution, and edit recalculation

Likely first scope:
- stronger manual regression coverage
- targeted automated checks for critical derived-state logic
- release validation around `test_app`

## Parked Ideas

### Multi-Puppy Support

Why it is parked:
- The current product is intentionally single-household and single-puppy
  focused
- This would affect the event model, UI simplicity, and recommendation logic

### Smarter Adaptive Guidance

Why it is parked:
- Pattern detection or ML-style adaptation is explicitly outside current scope
- The app still has simpler, higher-value product work ahead of it

## When To Promote A Backlog Item Into Spec Kit

An item is ready for `$speckit-specify` when:

- you want to work on it soon
- you can describe the user value in plain language
- you want to make tradeoffs explicit before coding
- the change is large enough that a spec will help avoid regressions
