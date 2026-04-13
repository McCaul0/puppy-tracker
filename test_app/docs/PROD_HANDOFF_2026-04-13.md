# Prod Handoff: 2026-04-13

## Candidate

- Branch: `rebuild-final-candidate-merge`
- Base: `master` at `2be2fd7 feat: ship schedule guidance and production bug fixes`
- Included recoveries:
  - `f6f6214 feat: recover simplify routine editing on master base`
  - `1e463a9 feat: rebuild tap-to-log status tiles on master base`
- Integration follow-up:
  - preserve legacy schedule-profile overrides in default-auto routine mode
  - preserve schedule-profile summary source while keeping routine-profile source semantics

## Scope Shipping Together

- Expected schedule guidance from the current `master` base
- Simplified routine editing (`002-simplify-routine-editing`)
- Tap-to-log status tiles (`003-tap-to-log-status-tiles`)

## Validation

- `python -m py_compile app.py test_app/app.py`
- `python -m pytest tests/contract/test_schedule_profile_api.py tests/integration/test_schedule_profile_flow.py -q --basetemp .pytest_tmp_final_merge_targeted2 -o cache_dir=.pytest_cache_final_merge_targeted2`
- `python -m pytest tests -q --basetemp .pytest_tmp_final_merge_full2 -o cache_dir=.pytest_cache_final_merge_full2`
- Result: `29 passed`

## Known Non-Blocking Warnings

- Pydantic deprecation warnings for `min_items` and `max_items`
- FastAPI deprecation warnings for `@app.on_event("startup")`

## Promotion Steps

1. Back up the live database file.
2. Back up the current live `app.py` with a timestamped filename in `backups/`.
3. Copy the approved candidate from `test_app/app.py` into the live `app.py`.
4. Restart the live app the normal way for this environment.
5. Smoke test the live dashboard:
   - dashboard loads
   - `pee`, `poop`, `food`, and `water` tiles tap-to-log
   - `awake` stays read-only
   - quick actions show `play`, `sleep`, and `wake`
   - expected routine editor still saves and loads
   - schedule-profile trigger rules still drive the advisory banner
6. If live-only hotfixes are made during promotion, copy them back into `test_app/app.py` immediately so test and prod do not drift again.

## Rollback

1. Stop the live app.
2. Restore the backed-up live `app.py`.
3. Restore the backed-up live database if the rollback requires data reversal.
4. Restart the live app.
5. Confirm the dashboard and `/api/state` load normally.
