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

---

## 1.3 Quick Actions

Pee, Poop, Food, Water, Play, Sleep, Wake

One-tap logging.

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

Shows timing rules and thresholds.

---

## 1.9 Settings

Basic configuration.

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
