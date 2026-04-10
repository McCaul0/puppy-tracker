<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
  - Template Principle 1 -> I. One-Tap Logging First
  - Template Principle 2 -> II. Decision-First Guidance
  - Template Principle 3 -> III. Derived State Integrity
  - Template Principle 4 -> IV. No Duplicate Concepts
  - Template Principle 5 -> V. Release Candidate Discipline
- Added sections:
  - Product Constraints
  - Development Workflow
- Removed sections:
  - None
- Templates requiring updates:
  - updated: .specify/templates/plan-template.md
  - updated: .specify/templates/spec-template.md
  - updated: .specify/templates/tasks-template.md
- Follow-up TODOs:
  - None
-->

# Puppy Coordinator Constitution

## Core Principles

### I. One-Tap Logging First
Core puppy activities MUST remain loggable in one tap or less on the default path.
Core flows MUST NOT require typing, confirmation, or multi-step forms before logging.
Edits MAY add detail later, but quick logging remains the primary interaction model because
the product succeeds only when tired humans can log events with almost no friction.

### II. Decision-First Guidance
The product MUST guide action rather than merely display raw data. The needs banner MUST
show exactly one primary recommendation, MUST be explainable in plain language, and MUST
never be blank. Status surfaces MUST support fast situational awareness without competing
recommendations or ambiguous urgency states.

### III. Derived State Integrity
Derived state MUST stay consistent after every create, edit, and delete. Sleep MUST be
auto-closed by the next wake or later non-sleep activity. Awake time MUST be derived and
MUST NEVER be manually entered. The system MUST function with partial or missing data and
MUST recalculate live state immediately after event changes.

### IV. No Duplicate Concepts
The UI, event model, and wording MUST preserve a single mental model for each concept.
Changes MUST NOT introduce overlapping concepts that describe the same outcome in multiple
ways. If a behavior can be represented as event detail, it MUST NOT also appear as a
separate first-class activity unless the specification explicitly replaces the old model.

### V. Release Candidate Discipline
`test_app` is the release candidate and MUST stay aligned with the live app and supporting
docs. Any change that affects persistence, API shape, release behavior, or manual
regression expectations MUST update the relevant docs under `test_app/docs` before release.
Production-only fixes MUST be synced back into `test_app` so the candidate remains the
trustworthy source for the next promotion.

## Product Constraints

The product is a self-hosted, LAN-first puppy tracker for a single household. Core
operation MUST continue without internet dependency and MUST remain usable from phones.
SQLite-backed local storage remains the default persistence model unless a future spec
explicitly changes it.

Current non-goals remain out of scope unless a future specification deliberately expands the
constitution or feature scope:

- notifications
- machine learning or adaptive automation
- multi-puppy support
- public-internet exposure without added auth and transport security

## Development Workflow

Feature work MUST start from the current behavioral source of truth in
`puppy_coordinator_behavioral_spec_v14.md` and this constitution. New work SHOULD follow
the Spec Kit flow of specification, plan, tasks, and implementation so product intent stays
traceable.

When a change touches user-facing behavior, reviewers MUST explicitly verify:

- one-tap logging is preserved for core actions
- the banner still presents exactly one recommendation
- derived state remains consistent after edits and deletes
- no duplicate concepts were introduced in UI copy or data modeling

When a change touches persistence, API behavior, or release procedure, the implementation
MUST update the appropriate reference docs in `test_app/docs`, including the data contract,
manual test coverage, checklist, changelog, or decisions log as applicable.

## Governance

This constitution supersedes ad hoc process notes when there is a conflict. Behavioral
specifications, implementation plans, and task lists MUST be reviewed against it before work
is considered ready.

Amendments require:

- an intentional update to this constitution
- a clear rationale in the related spec, plan, or commit history
- corresponding template or process updates when the amendment changes workflow expectations

Versioning policy:

- MAJOR for incompatible governance or principle changes
- MINOR for new principles or materially expanded obligations
- PATCH for clarifications that do not change expected behavior

Compliance review expectations:

- plans MUST pass the constitution check before implementation begins
- code review MUST call out violations to one-tap logging, decision-first guidance, derived
  state integrity, duplicate-concept avoidance, and release-doc synchronization
- releases MUST treat `test_app` and its docs as the candidate package, not an optional copy

**Version**: 1.0.0 | **Ratified**: 2026-04-10 | **Last Amended**: 2026-04-10
