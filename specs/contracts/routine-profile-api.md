# Contract: Routine Profile API

## Goal

Keep the existing dashboard snapshot contract intact while adding enough routine-specific data to
render the new overview surface, save/reset routine customizations, and handle explicit accept or
reject decisions on age-based proposals.

## Endpoint: `GET /api/state`

### Additive response fields

Existing top-level keys remain unchanged. The following additions are expected inside
`live_state`.

```json
{
  "live_state": {
    "schedule": {
      "effective_age_band_id": "10_to_12_weeks",
      "age_label": "10-12 weeks",
      "age_weeks": 11.4,
      "routine_mode": "custom_manual",
      "profile_source": "custom_saved",
      "recommended_age_band_id": "4_to_6_months",
      "recommended_age_label": "4-6 months",
      "guidance_shifted_by_recent_events": true,
      "last_saved_mode": "simple",
      "defaults": {
        "pee_due": 60,
        "pee_overdue": 90,
        "poop_due": 240,
        "poop_overdue": 300,
        "food_due": 300,
        "food_overdue": 360,
        "water_due": 120,
        "water_overdue": 180,
        "awake_due": 60,
        "awake_overdue": 75,
        "sleep_default": 120,
        "post_food_potty_due": 10,
        "post_food_potty_overdue": 25
      },
      "pee_due": 60,
      "pee_overdue": 90,
      "poop_due": 240,
      "poop_overdue": 300,
      "food_due": 300,
      "food_overdue": 360,
      "water_due": 120,
      "water_overdue": 180,
      "awake_due": 60,
      "awake_overdue": 75,
      "sleep_default": 120,
      "post_food_potty_due": 10,
      "post_food_potty_overdue": 25
    },
    "routine_overview": {
      "headline": "Today's rhythm",
      "summary_text": "At 11 weeks, expect short awake windows, regular potty breaks, and naps after about an hour awake.",
      "source_state": {
        "profile_source": "custom_saved",
        "routine_mode": "custom_manual",
        "guidance_shifted_by_recent_events": true,
        "source_badge": "Custom routine from 10-12 weeks",
        "source_detail": "Recent logs shift the next window without changing your saved routine.",
        "proposal_status": "pending"
      },
      "current_block": {
        "id": "awake-now",
        "kind": "awake",
        "phase": "now",
        "title": "Awake stretch",
        "window_start_utc": "2026-04-11T15:00:00Z",
        "window_end_utc": "2026-04-11T16:00:00Z",
        "time_label": "Now until around 12:00 PM",
        "explanation": "Puppies in this band usually nap after about an hour awake.",
        "emphasis": "active"
      },
      "next_block": {
        "id": "potty-next",
        "kind": "potty",
        "phase": "next",
        "title": "Potty window",
        "window_start_utc": "2026-04-11T15:15:00Z",
        "window_end_utc": "2026-04-11T15:30:00Z",
        "time_label": "Around 11:15 AM to 11:30 AM",
        "explanation": "Last pee was 50 minutes ago.",
        "emphasis": "upcoming"
      },
      "agenda": []
    },
    "routine_proposal": {
      "proposal_id": "10_to_12_weeks-to-4_to_6_months",
      "status": "pending",
      "current_custom_age_band_id": "10_to_12_weeks",
      "recommended_age_band_id": "4_to_6_months",
      "headline": "Your puppy is now 4 months old",
      "summary_text": "We'd usually lengthen potty windows and awake time at this stage.",
      "diff_items": [
        {
          "field_id": "pee_due",
          "label": "Potty rhythm",
          "current_value": 60,
          "recommended_value": 180,
          "change_note": "Expect longer stretches between potty breaks."
        }
      ],
      "reviewed_at_utc": null
    },
    "routine_editor": {
      "active_age_band_id": "10_to_12_weeks",
      "active_age_label": "10-12 weeks",
      "routine_mode": "custom_manual",
      "last_saved_mode": "simple",
      "default_values": {},
      "effective_values": {},
      "simple_fields": [
        {
          "id": "potty_rhythm",
          "label": "Potty rhythm",
          "fields": ["pee_due", "pee_overdue"]
        }
      ],
      "advanced_fields": [
        {
          "id": "pee_due",
          "label": "Pee due",
          "unit": "minutes"
        }
      ]
    }
  }
}
```

### Notes

- Existing clients that only read the flat `live_state.schedule.*` fields remain compatible.
- `schedule.defaults` exposes the age-band defaults so the client can render comparisons and
  reset affordances without extra fetches.
- `routine_editor` is read-only state for UI rendering. No draft state is stored server-side.
- `routine_proposal` is present only when a customized routine has a new age-based recommendation
  awaiting review.

## Endpoint: `PUT /api/routine-profile`

### Purpose

Persist routine customizations for the active age band.

### Request body

```json
{
  "base_age_band_id": "10_to_12_weeks",
  "save_mode": "simple",
  "custom_values": {
    "pee_due": 70,
    "pee_overdue": 100,
    "food_due": 330,
    "food_overdue": 390,
    "awake_due": 55,
    "awake_overdue": 70,
    "sleep_default": 110
  }
}
```

### Validation

- `base_age_band_id` must match a known schedule band.
- `save_mode` must be `simple` or `advanced`.
- `custom_values` must contain only supported routine fields.
- Numeric values must be integers within the existing schedule bounds policy.
- Any supplied due/overdue pair must preserve `due < overdue`.

### Success response

- Returns the same snapshot shape as `GET /api/state` after recalculating live state.

## Endpoint: `DELETE /api/routine-profile`

### Purpose

Remove the saved custom routine and restore `default_auto` behavior.

### Success response

- Returns the same snapshot shape as `GET /api/state` after recalculating live state.

## Endpoint: `POST /api/routine-proposal/{proposal_id}/decision`

### Purpose

Record an explicit accept or reject decision for a pending age-based proposal.

### Request body

```json
{
  "action": "accept"
}
```

### Validation

- `proposal_id` must match the currently pending proposal.
- `action` must be `accept` or `reject`.

### Accept behavior

- Applies the proposed routine changes to the saved custom routine.
- Updates the custom routine base age band to the current recommended band.
- If the accepted values exactly match the age recommendation, the implementation may collapse
  back to `default_auto`.

### Reject behavior

- Preserves the current custom routine unchanged.
- Marks the current recommendation band as reviewed so the same proposal is not shown again until
  a later age-based recommendation change occurs.

## Persistence Contract

Routine profile state is stored in the `settings` table under the `routine_profile_state` key.

### Stored JSON shape

```json
{
  "version": 1,
  "routine_mode": "custom_manual",
  "last_reviewed_recommendation_band_id": "10_to_12_weeks",
  "custom_profile": {
    "base_age_band_id": "10_to_12_weeks",
    "updated_at_utc": "2026-04-11T15:05:00Z",
    "last_saved_mode": "simple",
    "custom_values": {
      "pee_due": 70,
      "pee_overdue": 100,
      "awake_due": 55,
      "awake_overdue": 70,
      "sleep_default": 110
    }
  }
}
```

## Decision Notes

- Accepting a proposal is a user-approved routine update, not an automatic age migration.
- Rejecting a proposal is a first-class, persisted outcome and should suppress repeat prompting
  until the next recommendation change.
- Recent-event-based guidance continues to operate independently of proposal state.

## Non-Goals For This Contract

- No route-per-screen routine editor.
- No multi-day planning API.
- No draft autosave or partially persisted editor state.
- No push notification delivery system in this first contract; the feature only requires an
  in-app proposal surface when the user encounters the routine area or related guidance UI.
