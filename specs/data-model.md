# Data Model: Simplify Expected Routine Editing

## Entity: ScheduleAgeBand

Represents the default schedule profile currently defined in code for a puppy age range.

### Fields

- `id`: string
  Example: `10_to_12_weeks`
- `label`: string
  Example: `10-12 weeks`
- `min_weeks`: number or null
- `max_weeks`: number or null
- `pee_due`: integer minutes
- `pee_overdue`: integer minutes
- `poop_due`: integer minutes
- `poop_overdue`: integer minutes
- `food_due`: integer minutes
- `food_overdue`: integer minutes
- `water_due`: integer minutes
- `water_overdue`: integer minutes
- `awake_due`: integer minutes
- `awake_overdue`: integer minutes
- `sleep_default`: integer minutes
- `post_food_potty_due`: integer minutes
- `post_food_potty_overdue`: integer minutes
- `summary_note`: string
  Friendly explanation used by the overview surface.

### Validation

- All minute values must be positive integers.
- Every `*_due` value must be strictly less than its paired `*_overdue` value.
- `sleep_default` must be greater than `0` and at most `1440`.

## Entity: CustomRoutineProfile

Persisted customization data for the currently active manual routine.

### Fields

- `base_age_band_id`: string
- `updated_at_utc`: ISO-8601 datetime string
- `last_saved_mode`: enum
  Allowed: `simple`, `advanced`
- `custom_values`: full threshold object
  Keys mirror the editable fields from `ScheduleAgeBand`

### Validation

- `base_age_band_id` must match a known schedule band.
- `custom_values` must contain only supported routine fields.
- Each custom value must satisfy the same numeric bounds as the default schedule.
- Every `*_due` value must remain less than its paired `*_overdue` value.

## Entity: RoutineModeState

Top-level persisted state describing whether the user is auto-following recommendations or using
a saved custom routine.

### Fields

- `routine_mode`: enum
  Allowed: `default_auto`, `custom_manual`
- `custom_profile`: `CustomRoutineProfile` or null
- `last_reviewed_recommendation_band_id`: string or null

### Validation

- `custom_profile` must be null when `routine_mode` is `default_auto`.
- `custom_profile` must be present when `routine_mode` is `custom_manual`.

## Entity: EffectiveRoutineProfile

The resolved schedule used by live guidance after selecting either the current recommended age
band or the saved custom routine.

### Fields

- `effective_age_band_id`: string
- `age_label`: string
- `age_weeks`: number
- `routine_mode`: enum
  Allowed: `default_auto`, `custom_manual`
- `profile_source`: enum
  Allowed: `default_current_age`, `custom_saved`
- `recommended_age_band_id`: string
- `recommended_age_label`: string
- `last_saved_mode`: enum or null
  Allowed: `simple`, `advanced`, `null`
- `defaults`: full `ScheduleAgeBand` value object
- `effective_values`: resolved threshold object currently driving guidance

### Relationships

- Always references the current recommended `ScheduleAgeBand`
- Optionally references one `CustomRoutineProfile`

## Entity: AgeBasedAdjustmentProposal

A pending proposal shown when the puppy has aged into a new recommendation band while the app is
still using a saved custom routine.

### Fields

- `proposal_id`: string
- `status`: enum
  Allowed: `pending`, `accepted`, `rejected`
- `current_custom_age_band_id`: string
- `recommended_age_band_id`: string
- `headline`: string
  Example: `Your puppy is now 4 months old`
- `summary_text`: string
  Example: `We'd usually lengthen potty windows and awake time at this stage.`
- `diff_items`: array of objects
  Each item includes `field_id`, `label`, `current_value`, `recommended_value`, and `change_note`
- `reviewed_at_utc`: ISO-8601 datetime string or null

### Validation

- A proposal exists only when `routine_mode` is `custom_manual` and the recommended age band is
  newer than the last reviewed one.
- `pending` proposals must expose at least one diff item.

## Entity: RoutineSourceState

Explains why the routine currently looks the way it does.

### Fields

- `profile_source`: enum
  Allowed: `default_current_age`, `custom_saved`
- `routine_mode`: enum
  Allowed: `default_auto`, `custom_manual`
- `guidance_shifted_by_recent_events`: boolean
- `source_badge`: string
  Example: `Default 10-12 week routine`
- `source_detail`: string
  Example: `Recent sleep and potty logs move the next window without changing your saved routine.`
- `proposal_status`: enum
  Allowed: `none`, `pending`, `accepted`, `rejected`

### Notes

- `routine_mode` is about whether defaults auto-advance or a custom routine is locked in.
- `profile_source` is about the concrete schedule currently driving guidance.
- `guidance_shifted_by_recent_events` is about live schedule interpretation.
- Both can be true at the same time without conflict.

## Entity: RoutineAgendaItem

One user-facing block in the overview agenda.

### Fields

- `id`: string
- `kind`: enum
  Allowed: `sleep`, `awake`, `potty`, `food`, `water`, `play`, `custom`
- `phase`: enum
  Allowed: `now`, `next`, `later`
- `title`: string
  Example: `Potty window`
- `window_start_utc`: ISO-8601 datetime string or null
- `window_end_utc`: ISO-8601 datetime string or null
- `time_label`: string
  Example: `Around 2:15 PM to 2:30 PM`
- `explanation`: string
  Plain-language reason for the block
- `emphasis`: enum
  Allowed: `active`, `upcoming`, `informational`

### Validation

- `now` items may omit `window_start_utc` when they describe the currently active block.
- `next` and `later` items should include at least one meaningful time boundary.
- `time_label` must be renderable without exposing raw JSON or technical jargon.

## Entity: RoutineOverview

The default first-open surface for the routine area.

### Fields

- `headline`: string
  Example: `Today's rhythm`
- `summary_text`: string
  Example: `At 11 weeks, expect potty about every 60 to 90 minutes and naps after about an hour awake.`
- `source_state`: `RoutineSourceState`
- `current_block`: `RoutineAgendaItem` or null
- `next_block`: `RoutineAgendaItem` or null
- `agenda`: array of `RoutineAgendaItem`
- `plain_language_defaults`: array of strings
  Optional supportive bullets such as `Meals usually land every 5 to 6 hours`

## Entity: RoutineEditorState

The data the frontend needs to power the simple and advanced edit surfaces without opening a
second fetch path.

### Fields

- `active_age_band_id`: string
- `active_age_label`: string
- `routine_mode`: enum
  Allowed: `default_auto`, `custom_manual`
- `default_values`: threshold object
- `effective_values`: threshold object
- `last_saved_mode`: enum or null
- `simple_fields`: array of field descriptors
  Intended fields for first-pass editing: potty rhythm, meal rhythm, awake window, nap length
- `advanced_fields`: array of full field descriptors

## State Transitions

### Default auto to customized manual

1. User opens the default overview.
2. User chooses `Adjust routine`.
3. User edits simple or advanced controls.
4. Save validates values and persists `CustomRoutineProfile`.
5. Live state rebuilds immediately from the new `EffectiveRoutineProfile`.

### Customized manual age transition proposal

1. Puppy ages into a newer recommended band.
2. The app keeps the current `CustomRoutineProfile`.
3. The app creates a pending `AgeBasedAdjustmentProposal`.
4. User accepts or rejects the proposal.
5. The app records the outcome and rebuilds live state.

### Customized manual to reset

1. User opens the editor while a custom routine exists.
2. User chooses `Reset to default`.
3. `custom_profile` is removed and `routine_mode` returns to `default_auto`.
4. Live state rebuilds from the current recommended age band.

### Advanced cancel path

1. User opens advanced controls.
2. User changes values locally.
3. User closes or cancels without save.
4. No persisted change occurs and the overview remains on the last saved effective profile.
