# Puppy Coordinator Release Checklist

This checklist is for promoting `test_app` into the live app with the smallest possible blast radius.

## Release Assumption

Current release method:

- `test_app/app.py` is the candidate
- live and test use different database paths
- promoting to live means copying the tested `app.py` into the live folder
- then stopping and rebuilding the live Docker container

If that assumption changes, update this checklist first.

## Before Release

- Confirm the current candidate is [`test_app/app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py).
- Confirm the live app is not being actively edited.
- Confirm the live database path is correct and separate from the test database path.
- Back up the live database file before any swap.
- Review the most recent entry in [`CHANGELOG.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\CHANGELOG.md).
- Review the most recent entry in [`DECISIONS.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DECISIONS.md).
- Run the manual release test script in [`MANUAL_TEST_SCRIPT.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\MANUAL_TEST_SCRIPT.md).
- Confirm no known blocker remains unresolved.

## Promotion Steps

- Stop the live container.
- Copy [`test_app/app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py) over the live [`app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\app.py).
- Rebuild the live Docker image.
- Start the live container.
- Confirm the live container is using the live DB path, not the test DB path.
- Open the live app from a phone and confirm it loads.

## Post-Release Smoke Test

- Confirm the dashboard loads without errors.
- Log `pee`.
- Log `food`.
- Log `sleep`.
- Confirm the banner and tiles update immediately.
- Edit the most recent event.
- Delete a non-critical recent event if safe to do so.
- Open the app on a second device and confirm websocket sync is working.
- Confirm existing live history is still visible.
- Confirm settings still load and save.

## Rollback

- Stop the live container.
- Restore the previous live [`app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\app.py).
- If needed, restore the backed-up live database.
- Rebuild and restart the live container.
- Re-run the post-release smoke test.

## Release Notes Minimum

For each release, record:

- date
- summary of what changed
- whether any data model behavior changed
- whether manual test script passed
- whether rollback would require DB restoration or code only
