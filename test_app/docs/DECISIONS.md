# Decisions Log

## 2026-03-28

### Timezone handling

Decision:

- Use the timezone of the device/browser for logging and editing times.

Why:

- The app is intended for one household in one place.
- There is no need to geolocate or enforce a stricter timezone model.

### Promotion strategy

Decision:

- Keep refining `test_app` locally and promote by copying the tested [`app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py) into the live app before rebuilding the live container.

Why:

- Live data is in active use.
- This keeps the production DB isolated while iterating.

### Accident model

Decision:

- Do not keep `accident` as a standalone quick action in the next version direction.

Why:

- The behavioral spec is moving toward elimination events carrying accident meaning rather than using a separate activity.

Follow-up:

- Update the behavioral spec version when that model is formally adopted in code.

### Spec versioning

Decision:

- The behavioral spec is now `v14`.

Why:

- The source-of-truth document should reflect the current direction, including removal of the standalone accident action and clearer sleep/banner behavior.

## 2026-03-29

### Production release labeling

Decision:

- The live app should default its visible version label to `v14`, while test-specific labeling stays opt-in through `PUPPY_TRACKER_VERSION`.

Why:

- Production should not present itself as a test build after promotion.
- The environment variable still leaves room for explicit test or preview labels when needed.

### Post-promotion cleanup rule

Decision:

- Any production-only fix discovered during promotion or smoke testing should be written back into the release-candidate docs/code path immediately after the cutover.

Why:

- The release source of truth still lives under `test_app`.
- This avoids drift where live behavior and the documented candidate stop matching after last-mile fixes.

### Accident logging model

Decision:

- `accident` should be stored as a boolean flag on `pee` and `poop` events instead of being a standalone activity.

Why:

- The logging flow still needs a fast way to mark accidents.
- Keeping accident status on the elimination event preserves potty history while removing the deprecated separate activity.

## 2026-04-11

### Routine profile aging model

Decision:

- Default-following routines should move automatically with the puppy's current age band.
- Saved custom routines should stay fixed until the user explicitly accepts a newer recommendation.
- Age-upgrade prompts must support both accept and reject outcomes.

Why:

- Auto-advancing defaults keep the common case effortless.
- Custom edits are a deliberate choice and should not be silently overwritten.
- Rejecting a proposal needs to be a first-class outcome so the app does not keep nagging with the same recommendation.

## 2026-04-13

### Tap-to-log status tile scope

Decision:

- Make `pee`, `poop`, `food`, and `water` status tiles the primary one-tap logging surface.
- Let the `awake` tile represent the current awake/asleep state and use it to log `sleep` or `wake`.
- Remove the separate quick-action strip, actor chooser, and accident toggle from the main dashboard.

Why:

- These four tiles have an obvious, safe event mapping.
- The awake/sleep state is important enough to deserve the same direct interaction, as long as the tile copy explains the current state and the next action clearly.
- Removing duplicate controls keeps the default dashboard simpler and pushes advanced controls into settings or event editing.
