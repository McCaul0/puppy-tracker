# Puppy Coordinator Functional Spec (v14.2 test)

## Core Principle

The app minimizes user effort and maximizes clarity of what the puppy needs now.

- Default interaction: one tap
- Correction model: edit after
- System behavior: assume, infer, adjust
- Output: actionable guidance, not raw data

---

# 1. Primary Components

## 1.1 Needs Banner

Displays a single recommendation for what the puppy likely needs right now.

---

## 1.2 Status Tiles

Pee, Poop, Food, Water, Awake

Format:

- "Pee, 36m ago, On track"

States:

- On track
- Due soon
- Overdue

Primary interaction:

- Pee, Poop, Food, and Water tiles are the main one-tap logging targets
- Awake remains read-only because it is derived state
- Tile copy should still read as status first, action second

---

## 1.3 Quick Actions

Play, Sleep, Wake

One-tap logging for activities that do not map safely to a status tile.

---

## 1.4 Sleep System

- Sleep sets start plus target wake
- Wake ends sleep
- Any later non-sleep activity can end sleep early

---

## 1.5 Awake State

Time since last sleep ended.

---

## 1.6 Activity Log

History with edit and delete.

---

## 1.7 Edit

Modify events after the fact without slowing down the default quick-log flow.

---

## 1.8 Schedule Logic

Shows the expected routine as a friendly day overview, with simple and advanced editing paths.

---

## 1.9 Settings

Basic configuration.

---

## 1.10 Expected Routine Review

- Default routines should auto-follow the puppy's current age recommendation
- Custom routines should stay stable until the user accepts a newer recommendation
- Age-based recommendation changes should be reviewable with explicit accept or reject actions

---

## 1.11 Version Indicator

Displayed near Live status when present.

---

## 1.12 Elimination Events

Accident meaning belongs on pee or poop events, not as a standalone quick action.

---

# 2. System Logic

- Derived timers
- Urgency states
- Recommendation engine

---

# 3. UX Rules

- one tap default
- edit later
- no duplicate meaning

---

# 4. Non-Goals

- no notifications yet

---

# 5. Future

- accident flag on elimination events
- notifications
- adaptive timing

---

## Summary

Decision assistant, not just a tracker.
