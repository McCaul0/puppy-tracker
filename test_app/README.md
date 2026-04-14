# Puppy Coordinator Functional Spec (v14.4 test)

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
- Awake doubles as the sleep/wake toggle tile: tap it to log `sleep` when awake or `wake` when asleep
- Tile copy should read state first, then elapsed time, then `Since ...`, with a simple `Tap to log` hint

---

## 1.3 Sleep System

- Sleep sets start plus target wake
- Wake ends sleep
- Any later non-sleep activity can end sleep early

---

## 1.4 Awake State

Shows whether the puppy is currently awake or asleep, when that state started, and lets the user log the opposite state in one tap.

---

## 1.6 Activity Log

History with edit and delete.

---

## 1.7 Edit

Modify events after the fact without slowing down the default quick-log flow.

---

## 1.7 Schedule Logic

Shows the expected routine as a friendly day overview, with simple and advanced editing paths.

---

## 1.8 Settings

Basic configuration plus the advanced `Schedule and logic` and `Expected routine` sections behind a compact settings drawer.

---

## 1.9 Expected Routine Review

- Default routines should auto-follow the puppy's current age recommendation
- Custom routines should stay stable until the user accepts a newer recommendation
- Age-based recommendation changes should be reviewable with explicit accept or reject actions

---

## 1.10 Version Indicator

Displayed near Live status when present.

---

## 1.11 Elimination Events

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
