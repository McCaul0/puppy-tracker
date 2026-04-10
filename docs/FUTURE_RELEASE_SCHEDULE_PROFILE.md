# Future Release Proposal: Visible Age-Based Schedule Profile

## Why this exists

The app already uses schedule logic to decide what is due soon or overdue, but that logic is not currently visible to the human and cannot be adjusted in the UI.

We do not want to change the current `test_app` right before promotion, but we do want a concrete capture of the next-step design so it is easy to implement in a later release.

## Product goal

Add a place in the app where the human can:

- see the expected routine for the puppy's current age
- understand why the banner and tiles are recommending something
- adjust the default schedule when their puppy differs from the generic model

## Recommended model

Treat the expected routine as a versioned `schedule profile`.

Each profile should contain:

- profile name
- puppy age band it applies to
- expected potty interval
- expected food interval
- expected water interval if used
- expected awake window
- expected nap duration or sleep target rules
- due-soon threshold
- overdue threshold
- explanatory notes shown to the human

## Recommended data shape

For a future release, store schedule guidance separately from event history.

Suggested structure:

```json
{
  "profile_version": 1,
  "source": "default" ,
  "age_bands": [
    {
      "id": "8_to_10_weeks",
      "label": "8-10 weeks",
      "min_weeks": 8,
      "max_weeks": 10,
      "potty_interval_min": 45,
      "food_interval_min": 180,
      "water_interval_min": 120,
      "awake_window_min": 60,
      "nap_duration_min": 120,
      "potty_due_soon_min": 10,
      "food_due_soon_min": 20,
      "sleep_due_soon_min": 10,
      "notes": "Short awake windows and frequent potty trips are expected here."
    }
  ]
}
```

## Recommended UI direction

Add a lightweight `Expected Schedule` panel or screen with:

- current age and active age band
- a plain-language summary like `At 11 weeks, expect potty about every 60-90 min and awake windows around 60 min`
- the currently active thresholds that drive banner and tile states
- an `Adjust schedule` action for future customization

This does not need to be the primary home-screen surface at first. A settings panel, info drawer, or details sheet would be enough for the first release.

## Recommended release path

### Phase 1

Read-only visibility only.

- show the current age band
- show the derived schedule values being used
- explain that recommendations are based on this profile

### Phase 2

Add customization.

- allow per-puppy overrides
- allow reset back to default guidance
- record whether the active profile is default or customized

### Phase 3

Use schedule profiles more deeply.

- make banner explanations reference the active threshold directly
- show upcoming expected transitions
- support profile tuning over time

## Suggested persistence approach

When this is implemented for real, prefer one of these:

1. Store default schedule bands in code and store only per-puppy overrides in SQLite.
2. Store both defaults and overrides in SQLite if we want schedule definitions editable without redeploy.

Recommendation:

Start with defaults in code plus overrides in SQLite. That is simpler, safer, and enough for the first visible release.

## Minimum fields needed before building the UI

- puppy birth date or explicit age
- active age band resolution logic
- thresholds used by banner and status tiles
- a place to store optional human overrides

## Open questions for implementation

- Should age bands be week-based, month-based, or mixed?
- Do we want one generic default profile or breed-size variants later?
- Should water guidance be informational only or drive urgency states?
- Do we want nap duration targets, awake window targets, or both?
- Should edits be global for the household or tied to one puppy profile?

## Definition of done for the future feature

- Human can see the active expected schedule in the app
- Human can understand why the app thinks something is due
- Schedule thresholds are no longer hidden-only logic
- Defaults remain fast and low-friction for first-time use
