# Main-Page Expected Behavior Reference

## Purpose

This document defines the intended behavior of the default dashboard surface so it can be used as a source of truth for manual QA and future automated tests.

This first pass covers only:

- Needs banner
- Status tiles: `Pee`, `Poop`, `Food`, `Water`, `Awake/Asleep`
- Recent activity, including its inline edit cards, only where it affects live dashboard state

This document does not cover:

- Anything inside `Settings`
- Activity edit-page UI details
- Schedule editor behavior

Main-page elements intentionally included in this reference:

- Header title and subtitle
- Live connection indicator
- Needs banner
- Main status tiles
- Recent activity list
- Inline edit cards for Recent activity
- Version footer

Main-page elements intentionally excluded from this reference:

- Expanded Settings drawer content
- Schedule and routine panels inside Settings
- Standalone edit-page flows outside the dashboard
- Back-office or API-only behavior that has no visible main-page effect

## Standard Output Shape

Each main-page component should be describable in terms of visible output. For dashboard tiles, the expected visible fields are:

- `Label`: the tile title shown to the user
- `Elapsed time display`: relative time such as `just now`, `45m ago`, `2h ago`
- `Secondary detail text`: optional clarifier such as `Since 11:30 AM`
- `Visual state/color`: green, yellow, red, or neutral gray
- `Urgency wording`: `On track`, `Due soon`, `Overdue`, or `No data`
- `Tap result`: what gets logged when the tile is tapped, if tappable

General timing rules:

- `On track` means elapsed time is less than the `due` threshold.
- `Due soon` means elapsed time is greater than or equal to the `due` threshold and less than the `overdue` threshold.
- `Overdue` means elapsed time is greater than or equal to the `overdue` threshold.
- `No data` means the app does not have enough information to compute the timer.

General text rules:

- No elapsed-time value should display as `No entries yet`.
- A timer under one minute should display as `just now`.
- Otherwise the display should use relative time such as `45m ago`, `1h ago`, or `2h 15m ago`.
- Local clock labels such as `Since 11:30 AM` should use the household timezone shown by the app.

### Formatting Rules

Main-page copy and formatting should stay consistent across the dashboard.

| Element | Expected format |
| --- | --- |
| Tile labels | Title case, for example `Pee`, `Food`, `Awake`, `Asleep` |
| Activity pills in the log | Match the stored activity name consistently; if humanized in the future, all pills should switch together |
| Relative times | `just now`, `45m ago`, `1h ago`, `2h 15m ago`, `1d ago` |
| Banner titles | Short action-oriented title case phrases |
| Banner reasons | Plain-language sentence fragments or short sentences |
| Footer version | `Version <value>` |
| Local date/time in the log | Local month/day plus local time, for example `4/14, 11:30 AM` |

Formatting expectations:

- Relative durations should use compact units rather than long prose.
- Clock times should reflect the local household timezone.
- The app should avoid mixing multiple time vocabularies for the same concept on the same component.
- If a value is unknown, the page should prefer a readable fallback such as `No entries yet` or `Unknown time`.

## Header And Footer

### Header Title And Subtitle

The header should identify the current household context clearly.

| Element | Expected behavior |
| --- | --- |
| Title | `<Puppy name> Coordinator` when settings are available |
| Subtitle | `Shared puppy log for <household name>` when settings are available |
| Initial fallback title | `Puppy Coordinator` before settings load |
| Initial fallback subtitle | `Shared puppy log` before settings load |

Header rules:

- The title should update when the puppy name changes.
- The subtitle should update when the household name changes.
- If names are missing or blank, the page should fall back to a safe default rather than showing an empty header.

### Live Indicator

The live indicator is part of the header and should communicate connection state at a glance.

| State | Expected text | Expected dot behavior |
| --- | --- | --- |
| Initial load | `Connecting` | neutral dot |
| Connected | `Live` | green dot |
| Connection lost | `Reconnecting` | non-green dot |

### Version Footer

The footer should display the current app version when available.

Expected behavior:

- Show `Version <app version>` when the server provides a version.
- Fall back to `Version unknown` if the version is unavailable.
- Keep the footer visually secondary to the main dashboard content.

## Current Schedule Values

The dashboard is age-band driven. Thresholds should always follow the active schedule band.

If the puppy birth date is missing, the current app defaults to an assumed age of `12.0 weeks`, which lands in the `12-16 weeks` band. That means the immediately testable default values today are:

| Measure | Due soon | Overdue |
| --- | ---: | ---: |
| Pee | 120m | 180m |
| Poop | 300m | 420m |
| Food | 360m | 480m |
| Water | 180m | 240m |
| Awake window | 90m | 120m |
| Post-food potty trigger | 15m | 30m |

Default sleep targets in the same band:

- Daytime nap target: `120m`
- Overnight sleep target: `240m`
- Overnight potty limit: `240m`

Full current age-band values:

| Age band | Pee | Poop | Food | Water | Awake | Nap default | Post-food potty |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8-10 weeks | 45/60m | 180/240m | 240/300m | 90/120m | 45/60m | 120m | 10/20m |
| 10-12 weeks | 60/90m | 240/300m | 300/360m | 120/180m | 60/75m | 120m | 10/25m |
| 12-16 weeks | 120/180m | 300/420m | 360/480m | 180/240m | 90/120m | 120m | 15/30m |
| 4-6 months | 180/240m | 420/540m | 480/720m | 240/300m | 180/240m | 120m | 15/30m |
| 6+ months | 240/360m | 540/720m | 600/720m | 300/360m | 240/300m | 120m | 15/35m |

In each pair, the first number is the `Due soon` threshold and the second is the `Overdue` threshold.

## Needs Banner

### Purpose

Show exactly one recommendation: the single most important thing the user should know or do right now.

### Inputs It Depends On

- Current resolved sleep state
- Elapsed time since pee, food, water, wake, play, and awake anchor
- Behavior triggers such as post-wake or post-food potty windows
- Active schedule band thresholds

### Display Rules

- The banner must always show exactly one title and one reason.
- The banner must never be blank.
- If nothing is urgent or active, the banner should read:
  - Title: `All good for now`
  - Reason: `Nothing looks urgent right now.`

### Priority Rules

Highest applicable rule wins. Intended priority order:

1. `Sleeping now`
2. `Potty likely due` after a recent wake, before a potty is logged
3. `Potty likely overdue` or `Likely needs potty soon` after food if no pee or poop has been logged after that meal
4. `Potty likely due` after a recent drink if still inside the drink-trigger watch window and no potty has followed
5. `Potty likely due` after recent play if still inside the play-trigger watch window and no potty has followed
6. `Pee break overdue`
7. `Needs sleep`
8. `Food likely due`
9. `Water likely due`
10. `Potty soon`
11. `Sleep soon`
12. `All good for now`

### Tie-Break And Conflict Rules

When more than one banner rule is true at the same time, the banner should use deterministic priority rather than trying to merge messages.

Tie-break rules:

- `Sleeping now` beats every other banner state.
- Behavior triggers beat general timer warnings when their priority is higher.
- More urgent potty states beat sleep, food, and water timer states.
- Post-wake potty beats the general pee timer when both are true at the same moment.
- Post-food potty beats the general pee timer when its priority is higher than the pee timer state.
- `Pee break overdue` beats `Needs sleep`.
- `Needs sleep` beats `Food likely due`.
- `Food likely due` beats `Water likely due`.
- `Potty soon` beats `Sleep soon`.
- If two different rules of the same broad category could both apply, the lower priority number wins and only that banner should be shown.

Expected conflict examples:

| Simultaneous conditions | Expected banner |
| --- | --- |
| Puppy is currently sleeping and pee timer is overdue | `Sleeping now` |
| Wake was 5m ago and pee timer is also due soon | `Potty likely due` after wake |
| Post-food potty overdue and awake window is due soon | `Potty likely overdue` |
| Pee overdue and sleep overdue | `Pee break overdue` |
| Food overdue and water overdue | `Food likely due` |
| Pee due soon and sleep due soon | `Potty soon` |

### Recalculation Rules

The banner should recalculate immediately after any event add, edit, or delete that changes:

- whether the puppy is currently asleep
- the current awake anchor
- any elapsed timer
- whether a trigger such as post-food potty has been cleared

### No-Data Behavior

- If there are no relevant events, the banner should still show `All good for now` rather than blank.
- As richer no-data handling is added later, it should still collapse to a single readable recommendation.

## Status Tiles

### Shared Tile Rules

All five main tiles should follow the same core contract:

- A tile shows one dashboard concept only.
- A tile's timer is always anchored to one specific event or derived state.
- The tile color and urgency wording must agree with the current timer state.
- Tapping a tappable tile logs exactly one activity and then refreshes the dashboard immediately.
- Editing or deleting the anchor event must refresh the tile immediately.

### Pee Tile

| Field | Expected behavior |
| --- | --- |
| Purpose | Show how long it has been since the most recent `pee` event. |
| Anchor event | The latest logged `pee`. |
| Starts/resets timer | Any new `pee` event, including one logged from the tile. |
| Stops timer | Never stops; it only resets on a newer `pee`. |
| Label | `Pee` |
| Elapsed time display | Relative time since the last `pee`; `No entries yet` if none exists. |
| Detail text | Optional; not required for the first pass. |
| Color/state | Green `On track` before `pee_due`; yellow `Due soon` from `pee_due`; red `Overdue` from `pee_overdue`; gray `No data` if no pee exists. |
| Tap behavior | Tap logs a `pee` event. |
| Recalculation | Add/edit/delete of a `pee` event immediately updates the timer and may change the banner. |

### Poop Tile

| Field | Expected behavior |
| --- | --- |
| Purpose | Show how long it has been since the most recent `poop` event. |
| Anchor event | The latest logged `poop`. |
| Starts/resets timer | Any new `poop` event. |
| Stops timer | Never stops; it only resets on a newer `poop`. |
| Label | `Poop` |
| Elapsed time display | Relative time since the last `poop`; `No entries yet` if none exists. |
| Detail text | Optional; not required for the first pass. |
| Color/state | Green before `poop_due`; yellow from `poop_due`; red from `poop_overdue`; gray if no poop exists. |
| Tap behavior | Tap logs a `poop` event. |
| Recalculation | Add/edit/delete of a `poop` event immediately updates the timer. |

### Food Tile

| Field | Expected behavior |
| --- | --- |
| Purpose | Show how long it has been since the most recent `food` event. |
| Anchor event | The latest logged `food`. |
| Starts/resets timer | Any new `food` event. |
| Stops timer | Never stops; it only resets on a newer `food`. |
| Label | `Food` |
| Elapsed time display | Relative time since the last `food`; `No entries yet` if none exists. |
| Detail text | Optional; not required for the first pass. |
| Color/state | Green before `food_due`; yellow from `food_due`; red from `food_overdue`; gray if no food exists. |
| Tap behavior | Tap logs a `food` event. |
| Recalculation | Add/edit/delete of a `food` event immediately updates the tile and may start or clear post-food potty banner logic. |

### Water Tile

| Field | Expected behavior |
| --- | --- |
| Purpose | Show how long it has been since the most recent `water` event. |
| Anchor event | The latest logged `water`. |
| Starts/resets timer | Any new `water` event. |
| Stops timer | Never stops; it only resets on a newer `water`. |
| Label | `Water` |
| Elapsed time display | Relative time since the last `water`; `No entries yet` if none exists. |
| Detail text | Optional; not required for the first pass. |
| Color/state | Green before `water_due`; yellow from `water_due`; red from `water_overdue`; gray if no water exists. |
| Tap behavior | Tap logs a `water` event. |
| Recalculation | Add/edit/delete of a `water` event immediately updates the tile and may affect drink-triggered potty guidance. |

### Tile Pending And Error States

Tile taps need explicit transient-state rules so the fast logging path stays understandable.

#### Pending State

When a tile tap has been sent but not yet completed:

- only the tapped activity should enter a pending state
- the tile should become temporarily disabled
- the tile should show a hint such as `Logging...`
- the tile should keep its current label, elapsed time, and urgency styling until the request resolves
- repeated taps on the same activity should be ignored while pending

Pending examples:

| User action | Expected tile state |
| --- | --- |
| Tap `Pee` once | Pee tile disables and shows `Logging...` |
| Tap `Pee` repeatedly while pending | No duplicate requests; tile remains pending |
| Tap `Awake` while it is logging `sleep` or `wake` | Awake tile disables until the request resolves |

#### Success State

After a successful tile log:

- the pending state clears
- the dashboard refreshes from the returned snapshot
- the relevant tile resets to the new anchor
- the log list refreshes
- the banner recalculates
- a success toast appears

Expected success messages:

| Action | Expected feedback |
| --- | --- |
| Tile logs `pee`, `poop`, `food`, or `water` | `<Activity> logged from tile` |
| Awake tile logs `sleep` | `Sleep logged. <sleep projection reason>` |
| Non-tile quick log | `<Activity> logged` |

#### Error State

If a tile log fails:

- the pending state clears
- the tile becomes tappable again
- the visible timer should remain truthful to the last confirmed state
- no optimistic timer reset should remain on screen
- the user should see an error message such as `Could not log pee`

Error rules:

- A failed request must not partially update the banner or any tile.
- The page should fall back to the last confirmed snapshot until a later success or live update arrives.
- If the server returns an error message, that message should be preferred over a generic fallback.

## Toasts And Error Messaging

The page uses lightweight transient feedback for most successful actions and plain error messaging for several failure paths.

### Success Toast Matrix

| Action | Expected message |
| --- | --- |
| Tile logs `pee` | `Pee logged from tile` |
| Tile logs `poop` | `Poop logged from tile` |
| Tile logs `food` | `Food logged from tile` |
| Tile logs `water` | `Water logged from tile` |
| Awake tile logs `sleep` | `Sleep logged. <sleep projection reason>` |
| Quick action logs a non-tile activity | `<Activity> logged` |
| Event edit succeeds | `Event updated` |
| Event delete succeeds | `Event deleted` |
| Settings save succeeds | `Settings saved` |

Toast behavior:

- Success toasts should appear briefly and then dismiss automatically.
- Success toasts should not block further interaction.
- The visible page state should already reflect the successful action when the toast appears.

### Error Messaging Matrix

| Failure case | Expected feedback |
| --- | --- |
| Tile log request fails without server detail | `Could not log <activity>` |
| Tile log request fails with server detail | prefer the server-provided error |
| Invalid edit date/time on the client | clear error such as `Could not read the date and time.` |
| Server rejects event update | prefer the server-provided update error |
| Server rejects settings save | prefer the server-provided settings error |

Error behavior:

- Error feedback must not imply success.
- Error feedback must leave the visible dashboard in the last confirmed state.
- The page should prefer human-readable wording over raw technical errors when possible.
- If the current implementation uses blocking alerts for some failures, the intended behavior can still be documented as inline or toast-style messaging for future UX cleanup, but the outcome must remain the same: no silent failure.

## Awake / Asleep Tile

This tile needs tighter documentation than the others because it is derived state rather than a direct activity timer.

### Purpose

Show whether the puppy is currently awake or asleep, how long the current state has lasted, and whether the awake stretch is still on track.

### Derived-State Rules

The tile has two modes:

- `Asleep`: the puppy is currently inside an unresolved sleep block
- `Awake`: the puppy is not currently inside an unresolved sleep block

### Sleep Block Resolution

A sleep block starts at the logged `sleep` time and resolves at the earliest applicable end:

1. A later explicit `wake` event
2. A later non-sleep activity that proves the puppy was awake

Important intended rules:

- The projected nap target is recommendation-only. It must not become the actual sleep end by itself.
- Any later recorded `wake` or later recorded non-sleep activity ends the sleep block at that recorded time.
- Once a sleep block ends, the awake timer must anchor to that resolved recorded end time.

### Awake Anchor

The awake anchor is the timestamp that the tile should use as `Since ...` when the puppy is awake:

- use the resolved sleep end if the latest sleep block has ended
- otherwise, if no sleep block exists, fall back to the most recent valid event timestamp

### Asleep State

| Field | Expected behavior |
| --- | --- |
| Label | `Asleep` |
| Anchor | The current sleep block start time |
| Elapsed time display | Time since sleep started |
| Detail text | `Since <sleep start local time>` |
| Visual state/color | Green `On track` while currently asleep |
| Tap behavior | Tap logs `wake` |
| Recalculation | Any `wake`, any later non-sleep event, or any edit/delete affecting the active sleep block must recompute the tile immediately |

Asleep state rules:

- While asleep, the tile is describing the current sleep stretch, not the awake window.
- The elapsed value should increase from sleep start.
- The tile should switch out of `Asleep` as soon as the sleep block is resolved.

### Awake State

| Field | Expected behavior |
| --- | --- |
| Label | `Awake` |
| Anchor | The resolved end of the latest sleep block, or the most recent valid event if no sleep block exists |
| Elapsed time display | Time since the awake anchor |
| Detail text | `Since <awake anchor local time>` |
| Visual state/color | Green before `awake_due`; yellow from `awake_due`; red from `awake_overdue`; gray if no valid anchor exists |
| Urgency wording | `On track`, `Due soon`, `Overdue`, or `No data` |
| Tap behavior | Tap logs `sleep` |
| Recalculation | Any add/edit/delete affecting sleep start, wake, or the first later activity after sleep must recompute the awake anchor immediately |

Awake state rules:

- `Awake for X` always means time since the resolved end of sleep, not time since the last manually logged `wake` unless that `wake` is the resolved end.
- If a later non-sleep activity closed the last sleep block, that later activity time becomes the awake anchor.
- The awake timer is derived and must never be manually entered.

### No-Data Behavior

- If no sleep block exists and there is no usable recent event, the tile should show:
  - Label: `Awake`
  - Elapsed time: `No entries yet`
  - Visual state: gray
  - Urgency wording: `No data`
- Once any valid event exists, the tile should use the best available anchor instead of staying blank.

## Recent Activity

### Purpose

Show the latest event history while serving as the correction path for mistakes that affect the dashboard.

### Expected Behavior

- Events should display newest first.
- The list should reflect newly logged tile actions immediately.
- Sleep rows represent sleep starts; they do not require a pre-entered end time for dashboard logic to work.
- If a later `wake` or later non-sleep activity resolves a sleep block, dashboard state should update immediately even though the original sleep row still represents the start event.

### Sleep-Related Rows And Helper Copy

Sleep rows need clearer behavior than ordinary rows because they represent a derived block rather than a fully self-contained event.

| Row element | Expected behavior |
| --- | --- |
| Activity pill | Shows `sleep` because the row represents a sleep start event. |
| Timestamp line | Shows the sleep start time, not the resolved wake time. |
| Note | Shows the saved note if one exists. |
| Helper copy | Explains that the row is a start-only sleep event and that wake or a later activity closes the block. |

Sleep helper text rules:

- For a standard sleep-start event with no stored duration, helper copy should read like: `Sleep start logged. Wake or the next activity will close the block.`
- If older legacy sleep data includes a stored duration, helper copy may mention the planned duration, for example: `Legacy sleep block planned for 2h.`
- Helper text should help the user understand how dashboard state is derived from the row.
- Helper text should never imply that awake duration is manually stored.

Sleep row behavior rules:

- Editing the row changes the sleep start.
- Deleting the row removes that sleep start from sleep-block resolution.
- A later wake row or later non-sleep row may resolve the sleep block, but those later rows do not rewrite the original sleep row timestamp.
- The activity list should continue to show the actual events in order, while the dashboard derives sleep and awake state from those events.

### Visual State And Row Feedback

The activity log should provide lightweight visual feedback after relevant updates.

Expected behavior:

- A newly saved or newly logged event may briefly flash or highlight so the user can find it.
- That highlight should be temporary and should not change the underlying meaning of the row.
- Accident rows should show an additional accident pill that is visually distinct from the main activity pill.
- Disabled or unavailable controls should look intentionally inactive, not broken.

### Dashboard-Coupled Recalculation Rules

Any add, edit, or delete in Recent activity must immediately recalculate:

- needs banner
- all status tiles
- sleep block resolution
- awake anchor
- current awake duration
- any trigger rules cleared or activated by the changed event order

### Day Navigation

The Recent activity list is grouped by calendar day and only one day group is shown at a time.

Navigation rules:

- The default visible day should be the newest day with activity.
- The day label should show the active group, such as `Apr 14`.
- If there are no events at all, the day label should show `No activity yet`.
- `Newer` should move toward the most recent day.
- `Older` should move toward earlier days.
- `Newer` should be disabled when the user is already on the newest visible day.
- `Older` should be disabled when the user is already on the oldest visible day.

Refresh rules:

- After a successful quick log, edit, delete, or settings save, the current implementation resets the log view to the newest day.
- If the currently selected day no longer exists after a refresh, the view should fall back to the newest available day rather than staying on an invalid index.
- An empty active day should render `No activity yet.` in the list body.

Day-navigation scenarios:

| Situation | Expected behavior |
| --- | --- |
| User opens the page with events on three days | Newest day is shown first |
| User taps `Older` once | Next older day becomes active |
| User reaches the oldest day | `Older` becomes disabled |
| User edits an event while viewing an older day | After save, view resets to the newest day |
| User deletes the only event on the active day | View resets safely to the newest valid day |

### Empty And Degraded States

The Recent activity area should remain usable even when data is incomplete or the list is empty.

Expected behavior:

- If there are no events at all, the list body should show `No activity yet.`
- If a timestamp cannot be parsed for a row, the row should use a readable fallback like `Unknown time`.
- If the day key cannot be derived, that row should still remain visible under a readable fallback day grouping rather than disappearing.

## Activity Log Edit Cards

These are the inline edit panels that open underneath a Recent activity row when the user taps `Edit`.

### Purpose

Allow the user to correct an existing event without leaving the main page.

### Open / Close Behavior

| Action | Expected behavior |
| --- | --- |
| Tap `Edit` on an event row | Opens that event's inline edit card directly under the row. |
| Tap `Edit` again | Toggles the same inline edit card closed. |
| Tap `Cancel` | Closes the card without saving changes. |
| Tap `Save` | Attempts to update the event, then refreshes the dashboard state if successful. |
| Tap `Delete` on the row | Removes the event and refreshes the dashboard state immediately. |

### Fields

Each edit card should expose these fields:

| Field | Expected behavior |
| --- | --- |
| Activity | Dropdown of allowed activities from Settings. |
| Actor | Dropdown of household members from Settings. |
| When | Date and time inputs populated from the event's current timestamp in local time. |
| Accident | Checkbox shown only for `pee` and `poop`. |
| Note | Multiline note field populated from the current event note. |

Fields not exposed in the inline edit card:

- No separate wake/end-time field for sleep
- No manual awake duration entry
- No schedule logic editing

### Activity-Specific Rules

| Case | Expected behavior |
| --- | --- |
| Change activity to `pee` or `poop` | Show the `Accident` checkbox. |
| Change activity away from `pee` or `poop` | Hide the `Accident` checkbox and clear the accident value. |
| Edit a `sleep` event | Treat the event as a sleep start only; later wake or activity still resolves the block. |
| Edit a `play` event | The inline card does not expose a duration field; play should keep using the quick-log default duration unless a future design adds duration editing. |

### Sleep-Specific Rules

Sleep edit cards need special expectations because they influence derived dashboard state:

- Editing a sleep start time changes the start of the sleep block.
- Editing a later wake event changes the resolved end of the sleep block.
- Editing a later non-sleep activity that falls after a sleep start can change whether that activity ends the sleep block.
- Changing an event from a non-sleep activity to `sleep` can create a new sleep block and shift the awake anchor.
- Changing an event from `sleep` to a non-sleep activity can remove a sleep block and force the dashboard to fall back to another awake anchor.

### Save Behavior

On save, the system should:

1. Read the edited activity, actor, date, time, accident flag, and note.
2. Validate that the date and time can be combined into a valid timestamp.
3. Save the corrected event.
4. Refresh the full dashboard state.
5. Re-render the needs banner, tiles, and activity list using the corrected event history.
6. Show a clear success message such as `Event updated`.

If the edited time cannot be parsed:

- the save should fail
- the user should see a clear error
- no event should be changed

### Delete Behavior

Deleting an event should:

- remove the event from the log
- refresh the full dashboard state immediately
- recalculate any derived sleep or awake state
- show a clear success message such as `Event deleted`

Delete-failure expectation:

- If delete fails, the row should remain in place and the dashboard should keep the last confirmed state.
- The user should receive a clear failure message.
- A failed delete must not remove the row optimistically and then leave the page inconsistent.

Delete safety UX:

- The current main-page flow uses immediate delete from the row action.
- If confirmation is added later, the behavior should still preserve the same post-delete recalculation rules.
- Whether confirmation exists or not, delete must never silently fail.

Detailed delete expectations:

- Delete is a row-level action, not part of the inline edit card body.
- In the current main-page flow, delete happens immediately from the row action.
- Once deleted, the event should disappear from Recent activity after the refresh.
- If the deleted event was the newest anchor for a tile, that tile should fall back to the next newest qualifying event.
- If the deleted event resolved a sleep block, the app should recompute the sleep block using the remaining events.
- If the deleted event was the winning banner trigger, the banner should immediately recalculate and may change to a different recommendation.

Delete edge cases:

- Deleting the latest `pee`, `poop`, `food`, or `water` event should move that tile back to the previous matching event or to `No data` if none remains.
- Deleting the only `sleep` event may remove the current sleep block entirely and force the awake tile to fall back to another recent event or to `No data`.
- Deleting a later `wake` event may re-open a sleep block if no other later event resolves it.
- Deleting the later non-sleep event that ended a sleep block may re-open the sleep block until another recorded ending event exists.

### Banner Behavior Triggered By Edits And Deletes

Editing or deleting events can change which rule wins the banner, even when the visible change looks small.

Core rule:

- After every successful edit or delete, the banner should be recomputed from the corrected event history, not patched incrementally from the previous banner.

Expected banner shifts:

| Change to event history | Expected banner effect |
| --- | --- |
| Move latest `pee` later | Can clear `Potty soon` or `Pee break overdue`. |
| Move latest `pee` earlier | Can escalate the banner to `Potty soon` or `Pee break overdue`. |
| Delete latest `pee` | Falls back to the prior pee anchor and may escalate potty urgency. |
| Add or move `wake` later | Can shorten awake time and clear `Sleep soon` or `Needs sleep`. |
| Move `wake` earlier | Can lengthen awake time and trigger `Sleep soon` or `Needs sleep`. |
| Edit a later non-sleep event to fall before projected sleep end | That event can become the sleep-block end and set a new awake anchor, which may clear or trigger sleep-related banner states. |
| Delete the event that ended the sleep block | The app must recompute the end source and may switch the banner back to `Sleeping now` if no other recorded ending event remains. |
| Move `food` later | Can clear meal-related overdue states and delay the post-food potty trigger. |
| Move `food` earlier | Can activate `Likely needs potty soon`, `Potty likely overdue`, or `Food likely due`. |
| Change a post-food potty event to a non-potty activity | Can reactivate the post-food potty banner because the meal is no longer considered cleared by `pee` or `poop`. |

Banner edit examples:

- Editing the only recent `pee` from `11:30 AM` to `9:30 AM` at `12:15 PM` should allow the banner to escalate from calm to `Potty soon` or `Pee break overdue`, depending on the active thresholds.
- Editing a `wake` from `11:50 AM` to `10:50 AM` should lengthen the awake window by one hour and may turn `All good for now` into `Sleep soon` or `Needs sleep`.
- Deleting the `pee` that followed a meal should allow the post-food potty banner to return if the meal still falls inside its trigger window.

### Live-Update Behavior

The dashboard supports live updates from other devices or browser sessions through the websocket connection.

Connection-state rules:

- Before the websocket is connected, the header status may show `Connecting`.
- When connected, the status should show `Live`.
- If the socket closes, the status should show `Reconnecting`.
- The app should keep retrying the connection after a short delay.

Snapshot rules:

- A live websocket message should replace the current dashboard state with the server-provided snapshot.
- Banner, tiles, Recent activity, and other main-page state should be re-rendered from that incoming snapshot.
- Live updates should keep the dashboard truthful even if another device created, edited, or deleted an event.

Expected cross-device behavior:

| Change on another device | Expected local result |
| --- | --- |
| Another device logs `pee` | Pee tile resets locally without a manual refresh |
| Another device edits a sleep-related event | Awake tile and banner recompute locally |
| Another device deletes the latest anchor event | Local tiles fall back to the next valid anchor |

Open-panel behavior:

- In the current implementation, a live update triggers a full event-list re-render.
- Because of that, an open inline edit card should be treated as non-persistent across live refreshes unless future UX explicitly preserves it.
- The expected behavior for now is correctness first: live data wins, even if the currently open edit card closes.

Local pending vs remote update rules:

- A local pending tile action should still resolve from the authoritative server snapshot once it returns.
- If another device changes the same timer while the local page is open, the local page should adopt the most recent server snapshot rather than trying to merge views client-side.

### Unsaved Edit Conflicts

An inline edit card can become stale if another device changes the same event or refreshes the list while the card is open.

Expected behavior:

- Live truth beats stale local form state.
- If a websocket refresh re-renders the activity list, any open edit card may close.
- The page should avoid pretending an unsaved draft is still attached to the old event row after that row has changed.
- If the event was deleted elsewhere, the local page should remove it and not allow a stale save against a missing row.
- If conflict handling becomes more advanced later, it should still prioritize correctness and explicit feedback over silent merging.

### Recalculation Rules

Editing or deleting an event must immediately recalculate anything derived from event ordering, including:

- latest pee, poop, food, and water anchors
- whether a post-wake, post-food, post-drink, or post-play trigger is active
- whether the puppy is currently asleep
- the resolved end of the latest sleep block
- the current awake anchor
- the banner winner

### Expected User Feedback

| Outcome | Expected behavior |
| --- | --- |
| Successful save | Show a success toast and refresh visible dashboard state. |
| Successful delete | Show a success toast and refresh visible dashboard state. |
| Invalid date/time | Show an error and keep the existing event unchanged. |

## Accessibility And Keyboard Behavior

The main page should stay understandable and operable without relying only on color or pointer interaction.

### Tile Accessibility

Expected behavior:

- Tappable tiles should use real button semantics.
- Read-only tiles should not pretend to be interactive.
- Tile accessible names should include:
  - label
  - elapsed value
  - detail text when present
  - urgency wording
  - tap hint or readonly reason when relevant

Accessibility rules:

- Color should reinforce urgency, not be the only signal.
- `On track`, `Due soon`, `Overdue`, and `No data` should remain visible in text where the tile design shows urgency text.
- Focus styling should be visible on keyboard focusable controls.

### Activity Log Accessibility

Expected behavior:

- `Edit`, `Delete`, `Save`, and `Cancel` should be reachable by keyboard.
- Day navigation buttons should have clear accessible labels like `Earlier days` and `Newer days`.
- Form labels should be present for edit-card fields.
- Error feedback should be perceivable even if the user is not watching the exact edited row.

## Fallback And Degraded States

The page should remain truthful and readable even when data or connectivity is incomplete.

Expected degraded-state rules:

- Missing events should show `No entries yet` rather than blank values.
- Missing or invalid timestamps should fall back to `Unknown time` in the log and `No data` or `No entries yet` in derived surfaces.
- If the websocket disconnects, the last confirmed dashboard snapshot may remain on screen while the header shows `Reconnecting`.
- If settings are partially missing, header and footer fields should use safe defaults rather than blank strings.
- If a live update arrives while local UI state is open, the visible data should favor the authoritative snapshot.

### Edit-Card Scenarios

#### Scenario A: Change pee time and update the pee tile

Current time checked:

- `12:15 PM`

Original events:

- `11:00 AM` pee

User correction:

- edit `pee` from `11:00 AM` to `10:30 AM`

Expected result:

- Pee tile changes from `1h 15m ago` to `1h 45m ago`
- Banner recalculates from the corrected pee time
- The updated event remains visible in Recent activity with the corrected timestamp

#### Scenario B: Change activity away from pee and clear accident

Original event:

- `pee`, marked as accident

User correction:

- change activity from `pee` to `water`

Expected result:

- Accident checkbox disappears
- Accident state is cleared and not retained on save
- Water tile now uses the corrected event as its latest anchor
- Pee tile no longer treats that event as a pee reset

#### Scenario C: Editing a later activity changes the awake anchor

Current time checked:

- `12:15 PM`

Original events:

- `9:15 AM` sleep
- `11:30 AM` pee

User correction:

- edit the `pee` event to `10:45 AM`

Expected result:

- The sleep block now ends at `10:45 AM` because that corrected recorded event is the first wake evidence after sleep started
- Awake tile recalculates to `1h 30m ago`
- Awake detail recalculates to `Since 10:45 AM`

#### Scenario D: Delete the event that currently anchors a timer

Current time checked:

- `12:15 PM`

Original events:

- `9:00 AM` pee
- `11:30 AM` pee

User action:

- delete the `11:30 AM` pee

Expected result:

- Pee tile falls back to the next most recent pee at `9:00 AM`
- Pee tile immediately recalculates to `3h 15m ago`
- Banner recalculates from the older remaining event history

#### Scenario E: Delete the wake that ended sleep

Current time checked:

- `12:15 PM`

Original events:

- `9:15 AM` sleep
- `11:30 AM` wake

User action:

- delete the `11:30 AM` wake

Expected result:

- The app recomputes the latest sleep block using the remaining events
- If no other later event ends that sleep block, the sleep block becomes open again and the awake tile should switch back to `Asleep`
- Banner and awake tile both recalculate immediately from the remaining history

#### Scenario F: Delete the event that cleared post-food potty

Current time checked:

- `12:15 PM`

Original events:

- `11:45 AM` food
- `12:00 PM` pee

User action:

- delete the `12:00 PM` pee

Expected result:

- The meal is no longer considered cleared by a potty event
- If the current time is still inside the post-food potty watch window, the banner may become `Likely needs potty soon`
- If the current time has passed the post-food potty overdue threshold, the banner may become `Potty likely overdue`

## Timeline Scenarios

These examples are intended for QA and future tests.

### Scenario 1: No data yet

Current time checked:

- `12:15 PM`

Event sequence:

- none

Expected banner:

- `All good for now`
- `Nothing looks urgent right now.`

Expected tiles:

| Tile | Expected output |
| --- | --- |
| Pee | `Pee` / `No entries yet` / gray / `No data` |
| Poop | `Poop` / `No entries yet` / gray / `No data` |
| Food | `Food` / `No entries yet` / gray / `No data` |
| Water | `Water` / `No entries yet` / gray / `No data` |
| Awake | `Awake` / `No entries yet` / gray / `No data` |

### Scenario 2: Pee just logged

Assumption for this scenario:

- no birth date is saved, so the active age band is the fallback `12-16 weeks` band

Current time checked:

- `12:15 PM`

Event sequence:

- `12:15 PM` pee

Expected banner:

- `All good for now`

Expected tile highlights:

- Pee: `just now`, green, `On track`
- Awake: if there is still no sleep history, it may anchor to the most recent valid event and show `Awake`, `just now`, `Since 12:15 PM`

### Scenario 3: Pee reaches due soon

Assumption for this scenario:

- no birth date is saved, so the active age band is the fallback `12-16 weeks` band

Current time checked:

- `2:15 PM`

Event sequence:

- `12:15 PM` pee

Expected tile highlights:

- Pee: `2h ago`, yellow, `Due soon`
- Banner: `Potty soon`

### Scenario 4: Pee becomes overdue

Assumption for this scenario:

- no birth date is saved, so the active age band is the fallback `12-16 weeks` band

Current time checked:

- `3:15 PM`

Event sequence:

- `12:15 PM` pee

Expected tile highlights:

- Pee: `3h ago`, red, `Overdue`
- Banner: `Pee break overdue`

### Scenario 5: Sleep started and still active

Current time checked:

- `10:15 AM`

Event sequence:

- `9:15 AM` sleep

Expected outputs:

- Awake tile label: `Asleep`
- Awake tile elapsed display: `1h ago`
- Awake tile detail: `Since 9:15 AM`
- Awake tile color/state: green / `On track`
- Awake tile tap result: tapping logs `wake`
- Banner: `Sleeping now`

### Scenario 6: Sleep ended by explicit wake

Assumption for this scenario:

- the current nap target checkpoint has not been reached yet, so the later recorded event still happens before the recommendation window would normally change color

Current time checked:

- `12:15 PM`

Event sequence:

- `9:15 AM` sleep
- `11:30 AM` wake

Expected outputs:

- Sleep block end: `11:30 AM`
- Awake tile label: `Awake`
- Awake tile elapsed display: `45m ago`
- Awake tile detail: `Since 11:30 AM`
- Awake tile color/state: green / `On track`
- Awake tile tap result: tapping logs `sleep`

### Scenario 7: Sleep ended by a later non-sleep activity

Assumption for this scenario:

- the current nap target checkpoint has not been reached yet, so the later recorded event still happens before the recommendation window would normally change color

Current time checked:

- `12:15 PM`

Event sequence:

- `9:15 AM` sleep
- `11:30 AM` pee

Expected outputs:

- Sleep block end: `11:30 AM`
- Awake anchor: `11:30 AM`
- Awake tile label: `Awake`
- Awake tile elapsed display: `45m ago`
- Awake tile detail: `Since 11:30 AM`
- Awake tile color/state: green / `On track`
- Pee tile elapsed display: `45m ago`
- Banner: `All good for now`

This scenario is the key regression guard:

- The app must not continue showing `1h awake` at `12:15 PM` if a later non-sleep activity at `11:30 AM` already proved the puppy was awake.
- A stale assumed nap target must not override the earlier wake evidence.

### Scenario 8: Later activity happens after the nap target has already passed

Current time checked:

- `12:15 PM`

Event sequence:

- `9:15 AM` sleep
- `11:30 AM` pee

Expected outputs:

- Sleep block end should be `11:30 AM`, because only a recorded later event ends the sleep block
- Awake tile should show `45m ago`
- Awake tile detail should show `Since 11:30 AM`
- Pee tile should still show `45m ago`

### Scenario 9: Editing the later activity should move the awake anchor

Current time checked:

- `12:15 PM`

Original events:

- `9:15 AM` sleep
- `11:30 AM` pee

User correction:

- edit `pee` from `11:30 AM` to `10:45 AM`

Expected outputs after edit:

- Sleep block end becomes `10:45 AM` because the corrected later activity is now the first recorded event after sleep started
- Awake tile becomes `1h 30m ago`
- Awake tile detail becomes `Since 10:45 AM`
- Pee tile becomes `1h 30m ago`
- Banner recalculates immediately using the corrected timers

### Scenario 10: Repeated tile taps should only reset the relevant timer

Current time checked:

- `12:15 PM`

Event sequence:

- `9:00 AM` food
- `10:00 AM` water
- `11:00 AM` pee
- `12:15 PM` tap `Pee` tile

Expected outputs:

- Pee resets to `just now`
- Food remains `3h 15m ago`
- Water remains `2h 15m ago`
- Awake/Asleep logic is unaffected unless the new event changes sleep resolution order

## Test Layers To Derive From This Document

This reference should drive three kinds of tests:

- Rule checks: each tile correctly transitions through `On track`, `Due soon`, `Overdue`, and `No data`
- Timeline checks: realistic event sequences produce exact expected UI outputs
- Mutation checks: add, edit, and delete operations immediately recompute the affected anchor and visible state

Minimum regression coverage to derive from this document:

- No-data state for every tile
- Due and overdue threshold crossings for each timer tile
- Sleep still active
- Sleep ended by `wake`
- Sleep ended by later non-sleep activity
- Later activity after nap target has passed
- Edit shifting the awake anchor
- Repeated logs resetting only the related timer
