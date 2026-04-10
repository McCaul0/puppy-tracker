# Process Notes

## Documentation Workflow

Treat these files as part of the release process:

- [`CHANGELOG.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\CHANGELOG.md)
- [`DECISIONS.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DECISIONS.md)
- [`DATA_CONTRACT.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DATA_CONTRACT.md)

## Minimum Update Rule

Whenever behavior changes in a meaningful way:

- update the changelog
- record any lasting design decision
- update the data contract if persisted data or API shape changed
- update the behavioral spec version if product behavior changed materially

## Default Team Convention

Documentation updates are part of the task by default.

Unless explicitly skipped, any meaningful change should also update the relevant docs in the same round of work.

At minimum, check:

- [`CHANGELOG.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\CHANGELOG.md)
- [`DECISIONS.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DECISIONS.md) when a durable choice was made
- [`DATA_CONTRACT.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\DATA_CONTRACT.md) when storage or API behavior changed
- [`puppy_coordinator_behavioral_spec_v14.md`](C:\Users\mccau\Codex Projects\puppy_tracker\puppy_coordinator_behavioral_spec_v14.md) when product behavior changed materially

## Automation Direction

Use the local helper script to keep docs current without adding much process.

Script:

- [`scripts/update_docs.py`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\scripts\update_docs.py)

Example:

```powershell
python .\scripts\update_docs.py `
  --changelog "Refined sleep banner behavior" `
  --changelog "Adjusted edit flow copy" `
  --decision-title "Sleep banner wording" `
  --decision "Use plain-language banner copy instead of terse status text." `
  --why "The banner is the primary decision aid and should read clearly at a glance."
```

Recommended use:

- run it whenever you finish a meaningful behavior change
- add one or more changelog bullets
- add a decision entry only when the change reflects a durable choice

Until then, keep the docs current as part of each release candidate.
