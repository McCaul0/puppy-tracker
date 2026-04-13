# Changelog

## Unreleased

### 2026-04-13

- Added tap-to-log status tiles for `pee`, `poop`, `food`, and `water` while keeping `awake` read-only.
- Reduced secondary quick actions to `play`, `sleep`, and `wake` so the dashboard feels simpler.
- Preserved edit/delete recovery paths for accidental logs and kept unsupported actions on other entry paths.
- Recovered and merged the routine-editing and tap-to-log work onto the current `master` base before release validation.

### 2026-04-11

- Replaced the dense schedule threshold card with an `Expected routine` overview that explains `Now`, `Next`, and `Later today`.
- Added routine profile state so default-following schedules auto-advance by age while custom routines remain stable.
- Added explicit age-upgrade proposals with `Accept recommendation` and `Keep my routine` decisions.
- Added routine profile endpoints and release-doc coverage for the new routine editing flow.

### 2026-03-29

- Promoted the current `v14.2 test` candidate into the live/root app.
- Rebuilt the production Docker stack and kept the production DB target on `/data/puppy_tracker.db`.
- Changed recent-activity day labels to fixed-width abbreviated month/day formatting so the nav buttons stay anchored while paging between days.
- Removed the timezone offset field from in-app settings while keeping the existing stored/server-side timezone behavior.
- Reworked sleep editing to use a simple `Sleep for` hours duration with a 2-hour nap default instead of a `Wake by` datetime input.
- Bumped the live app version label to `v14.1`.
- Advanced the test candidate label to `v14.2 test`.
- Fixed mobile edit-form date/time inputs so their borders stay inside the card container on narrow screens.

### 2026-03-29

- Started the `v14.1 test` candidate in `test_app`.
- Switched the test UI to a dark-mode visual treatment.
- Reworked event editing time entry to use separate date and time inputs with mobile-friendly widths.
- Added an `is_accident` event flag for `pee` and `poop`, with a quick-log accident checkbox and edit support.
- Replaced day-navigation text buttons with left/right double-arrow icon buttons and clearer disabled states at the ends of the history range.

### 2026-03-29

- Promoted the `test_app` candidate into the live app and rebuilt the production Docker container.
- Verified the live deployment against the production DB with API, websocket, create, edit, delete, and settings smoke checks.
- Set the production default app version label to `v14` instead of a test-tagged value.
- Normalized age-range schedule labels in the live app to ASCII (`8-10`, `10-12`, `12-16`, `4-6`) so they render cleanly across environments.
- Synced `test_app/app.py` back to the same `v14` version label and schedule-label formatting so test and prod are in parity again.

### 2026-03-28

- Fixed awake-time fallback so it uses the most recent event when no sleep block is available.
- Removed the deprecated `accident` quick action from the test candidate.
- Added server-side settings normalization for activities and household members.
- Added release, data contract, and manual test documentation.
- Bumped the behavioral spec to `v14` and aligned companion docs with the current direction.
