# Quickstart: Tap-To-Log Status Tiles

## Goal

Validate that supported dashboard tiles become the primary one-tap log surface without making
the dashboard harder to interpret.

## Implementation Outline

1. Extend the derived `live_state.tiles` objects in `app.py` and `test_app/app.py` to include
   explicit action metadata and a server-defined `secondary_quick_actions` list.
2. Update tile rendering so supported tiles use accessible button behavior while preserving the
   existing urgency colors, elapsed-time display, and lightweight status-first layout.
3. Replace the full quick-action strip with the smaller unsupported-action set from
   `secondary_quick_actions`.
4. Route tile taps through the existing `POST /api/events` call path, with client-side pending
   protection and success or error toast feedback.
5. Keep recent-activity edit/delete unchanged and verify that mistaken tile logs can be corrected
   there.
6. Update `test_app/docs` so the release-candidate docs match the new dashboard behavior.

## Verification Flow

1. Open the dashboard on two devices or tabs.
2. Confirm `pee`, `poop`, `food`, and `water` tiles show a subtle tap affordance and still read
   clearly as status tiles.
3. Confirm `awake` does not look tappable.
4. Tap each supported tile once and verify:
   - the matching event is created
   - the banner and tile urgency update immediately
   - the event appears in recent activity
   - the second device updates without refresh
5. Attempt rapid repeated taps on the same tile and confirm the pending state prevents accidental
   duplicate submissions while the request is in flight.
6. Simulate an error and confirm the dashboard stays truthful and shows clear failure feedback.
7. Correct a mistaken tile log through recent-activity edit or delete.
8. Confirm the remaining quick-log section only shows unsupported actions such as `play`,
   `sleep`, and `wake`.

## Out of Scope for This Cut

- adding a new database field or migration
- adding confirmation dialogs before tile logs
- making derived-state tiles tappable
- introducing a tile-specific write endpoint
- redesigning edit/delete recovery flows beyond ensuring they still work
