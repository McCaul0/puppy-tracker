# Puppy Coordinator Manual Test Script

Run this against `test_app` before promoting code to live.

## Setup

- Start the test app.
- Open it on one phone and one second device or browser tab.
- Use the test database, not the live database.

## Critical Path Tests

### 1. App loads

- Open the home page.
- Confirm the dashboard renders.
- Confirm the live indicator connects.
- Confirm recent events load.

### 2. Quick logging

- Tap the `pee` tile.
- Tap the `pee` tile with the accident checkbox on.
- Tap the `poop` tile.
- Tap the `poop` tile with the accident checkbox on.
- Tap the `food` tile.
- Tap the `water` tile.
- Tap the `awake` tile while the puppy is awake and confirm it logs `sleep`.
- Tap the `awake` tile while the puppy is asleep and confirm it logs `wake`.

Expected:

- supported tile actions are one tap
- `awake` clearly shows whether the puppy is awake or asleep and what tapping it will log next
- each event appears immediately in recent activity
- accident-tagged `pee` and `poop` show an obvious accident marker
- banner and status tiles update immediately
- second device updates without refresh

### 3. Sleep behavior

- Log `sleep`.
- Confirm the UI shows sleeping state.
- Confirm a wake target is shown.
- Log `wake`.
- Confirm sleep ends.
- Log `sleep` again.
- Before the projected wake time, log `pee`.
- Confirm sleep closes early because of later activity.

### 4. Edit behavior

- Edit a recent `sleep` event.
- Change the start date.
- Change the start time.
- Change the wake-by date.
- Change the wake-by time.
- Save and confirm duration changes.
- Edit a recent non-sleep event.
- Change activity, actor, time, and note.
- Toggle the accident checkbox on for `pee` or `poop`.
- Change the activity away from `pee` or `poop` and confirm the accident checkbox no longer applies.
- Save and confirm the dashboard recalculates.

### 5. Delete behavior

- Delete a non-critical recent event.
- Confirm it disappears immediately on both devices.
- Confirm dependent banner/tile values recalculate.

### 6. Settings behavior

- Change puppy name.
- Change household name.
- Change birth date.
- Change household members.
- Save settings.

Expected:

- title and subtitle update
- schedule recalculates from birth date
- second device sees updated settings

### 6a. Expected routine overview

- Open the `Expected routine` section.
- Confirm the first view explains the day in `Now`, `Next`, and `Later today` language.
- Confirm the routine source badge explains whether the app is auto-following the current age band or using a custom routine.
- Confirm the routine does not look like a rigid work calendar.

### 6b. Routine customization and age-upgrade review

- Save a simple custom routine.
- Confirm the source badge changes to a custom routine state.
- Change the puppy birth date so the recommended age band advances.
- Confirm an age-upgrade proposal appears with both accept and reject choices.
- Reject the proposal and confirm the custom routine remains active.
- Recreate the pending proposal and accept it.
- Confirm the routine returns to the current age recommendation.

### 7. Data hygiene checks

- Save household members with extra spaces.
- Save duplicate household members.
- Confirm duplicates and blanks do not persist.
- Confirm activities still include the default supported actions.
- Confirm the dashboard no longer shows a quick-action strip, actor chooser, or accident toggle.

### 8. Banner sanity checks

- After recent potty, confirm banner is not incorrectly urgent.
- After long awake period, confirm banner can suggest sleep.
- After food, confirm post-food potty guidance appears when expected.
- During sleep, confirm banner shows sleeping guidance instead of another action.

### 9. Refresh resilience

- Refresh one device.
- Confirm it reloads current state correctly.
- Disconnect and reconnect network if practical.
- Confirm websocket reconnects and live updates resume.

### 10. UI and navigation polish

- Confirm the app now presents in dark mode across the main dashboard, settings, and event cards.
- Confirm the tappable status tiles still read primarily as status and urgency, not as oversized buttons.
- Confirm advanced controls only appear under the `Settings` drawer.
- Confirm split date and time inputs fit cleanly within their containers on phone-width and desktop-width layouts.
- Open older history with the left double-arrow button.
- Navigate back toward today with the right double-arrow button.
- Confirm the right arrow is obviously inactive on `Today`.
- Confirm the left arrow is obviously inactive on the earliest available day.

## Release Gate

Do not promote to live if any of these fail:

- supported status tiles do not save
- dashboard does not load
- websocket sync fails
- sleep logic is inconsistent
- editing corrupts event times or durations
- settings save invalid or surprising values
- live state tiles do not recalculate after changes
- the expected routine silently rewrites a custom routine after an age change without user acceptance
