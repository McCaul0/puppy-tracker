# Puppy Coordinator Docs Index

This folder supports the `test_app` release candidate and the process around promoting it to live.

Latest promotion:

- The current live app was promoted from `test_app` on `2026-03-29`.
- Any follow-up fixes made directly in live should be synced back here so the candidate and docs stay aligned.

## Source Of Truth

- Behavioral source of truth: [`puppy_coordinator_behavioral_spec_v14.md`](C:\Users\mccau\Codex Projects\puppy_tracker\puppy_coordinator_behavioral_spec_v14.md)
- Test candidate app: [`test_app/app.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\app.py)

## Docs In This Folder

- [`RELEASE_CHECKLIST.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\RELEASE_CHECKLIST.md)
  Use before promoting `test_app` to live.
- [`MANUAL_TEST_SCRIPT.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\MANUAL_TEST_SCRIPT.md)
  Run the core manual regression checks before release.
- [`DATA_CONTRACT.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DATA_CONTRACT.md)
  Technical reference for stored data, API shapes, and migration-sensitive changes.
- [`CHANGELOG.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\CHANGELOG.md)
  High-level record of what changed.
- [`DECISIONS.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DECISIONS.md)
  Record of durable product and engineering decisions.
- [`PROCESS_NOTES.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\PROCESS_NOTES.md)
  Lightweight workflow notes for keeping the docs current.
- [`scripts/update_docs.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\scripts\update_docs.py)
  Tiny helper for appending changelog and decision-log entries.

## Recommended Reading Order

1. Read the behavioral spec.
2. Read the data contract if a change touches persistence or API behavior.
3. Review the changelog and decisions log.
4. Run the manual test script.
5. Use the release checklist when promoting to live.
6. After promotion, record the shipped result and sync any last-mile production fixes back into `test_app`.
