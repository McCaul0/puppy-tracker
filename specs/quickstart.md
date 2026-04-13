# Quickstart: Simplify Expected Routine Editing

## 1. Run the app

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open the app at `http://localhost:8000`.

## 2. Prepare a realistic schedule context

1. Save a puppy birth date that lands in the `10-12 weeks` band.
2. Log a few recent events such as `sleep`, `wake`, `pee`, and `food`.
3. Confirm the banner and quick tiles still behave normally before touching the routine area.

## 3. Verify the default first-open routine view

1. Open the routine section.
2. Confirm the first surface emphasizes understanding rather than raw editing controls.
3. Confirm the view shows:
   - active age band
   - routine source badge
   - current block
   - next expected block
   - a short agenda for later today
4. Confirm the language feels like household guidance, not a business calendar.
5. If the user is still on defaults, confirm the routine simply reflects the current age band
   without any review prompt.

## 4. Verify simple adjustments

1. Choose `Adjust routine`.
2. Change one or more of the common fields:
   - potty rhythm
   - meal rhythm
   - awake window
   - nap length
3. Save.
4. Confirm the overview, banner explanation, and relevant timing guidance update immediately.
5. Re-open the routine area and confirm the customized source state is visible.
6. Confirm later age-band changes do not silently rewrite the saved custom routine.

## 5. Verify age-upgrade proposal review

1. Put the app into a customized routine state.
2. Change the puppy age so the recommended age band advances.
3. Confirm the routine stays on the saved custom schedule.
4. Confirm the app shows a proposal describing what would usually change.
5. Reject the proposal once and confirm:
   - the custom routine stays unchanged
   - the proposal is marked handled
   - the same prompt does not immediately reappear
6. Recreate or revisit a pending proposal and accept it.
7. Confirm the saved routine updates to the accepted recommendation outcome.

## 6. Verify advanced editing

1. Open the same routine area.
2. Enter advanced editing deliberately from the simple view.
3. Confirm the app reveals exact threshold controls for the active age band.
4. Cancel out once and confirm no accidental draft state persists.
5. Save an advanced change and confirm the saved mode/source metadata reflects the new state.

## 7. Verify reset behavior

1. Use the reset action for the active age band.
2. Confirm the routine returns to defaults.
3. Confirm the source state changes back from customized to default.
4. Confirm live guidance still reflects recent real events after reset.

## 8. Regression expectations

The feature is not complete unless all of the following still hold:

- one-tap quick logging remains unchanged
- the banner still shows exactly one primary recommendation
- sleep auto-close logic still works
- live state recalculates after event edits and deletes
- the routine UI does not create conflicting schedule concepts
- custom routines do not auto-change on age transition without user acceptance

## 9. Required implementation follow-through

When this feature is implemented for real:

1. Update `app.py` and `test_app/app.py`.
2. Add or refresh tests for the new routine state and save/reset API.
3. Update `test_app/docs/DATA_CONTRACT.md`.
4. Update `test_app/docs/MANUAL_TEST_SCRIPT.md`.
5. Add a changelog or decisions entry if release-candidate behavior changes.
