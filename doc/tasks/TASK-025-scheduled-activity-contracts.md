# TASK-025: Define scheduled-activity and queue contracts

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** M3 domain models

## Objective

Define strict immutable runtime contracts for one-shot environmental, NPC, and System-director eligibility records and for the queue that contains them.

This task establishes identity, time, provenance, storage, and uniqueness only. It does not select eligible activities, derive an execution result, or run scheduled work.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Scheduled activity”, “Scheduled activity queue”, “Scheduler”, “Simulation time”, “NPC”, and “System director”
* `doc/requirements.md`: `TIME-001` through `TIME-006`, `ACTION-020` through `ACTION-023`, and `SCHEDULE-001` through `SCHEDULE-015`
* `doc/decisions.md`: “Use discrete, action-driven simulation time”, “Give NPCs bounded proactive autonomy”, “Serialize eligible activities deterministically”, “Invoke the System director through rate-limited event hooks”, “Inject UUID runtime identities and type submission sources”, and “Represent scheduled work as one-shot typed eligibility records”
* `doc/high_level_design.md`: “Clock and scheduler”, “Principal records”, “Simulation-step flow”, and “Testing strategy”
* `src/llm_system/simulation/_types.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/__init__.py`, `tests/test_runtime_state.py`, `tests/test_actions.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, resolver, perception, persistence or package implementation, or other task briefs.

## Fixed assumptions

* Add strict frozen `EnvironmentalScheduledActivity`, `NpcScheduledActivity`, and `SystemDirectorScheduledActivity` Pydantic models in a new scheduling module.
* The discriminators are exact `activity_type` literals `environmental`, `npc`, and `system_director` respectively.
* Every variant requires caller-supplied `activity_id: UUID`, `eligible_at_seconds: NonNegativeSeconds`, and a strict non-negative integer `insertion_sequence`. No field has a generated default.
* `EnvironmentalScheduledActivity` additionally requires `schedule_id: AuthoredId`; `NpcScheduledActivity` requires `npc_id: AuthoredId`; and `SystemDirectorScheduledActivity` requires `hook_id: AuthoredId`.
* `ScheduledActivity` is the public closed discriminated union of those exact three variants.
* Do not add `phase_priority` to any record. Phase order is derived later from the variant as environmental, NPC, then System director.
* Do not add NPC policy identity, owner/source unions, mechanic arguments, action proposals, outcomes, callbacks, recurrence, cancellation, retry, completion, lock, claim, execution, or trace fields.
* `ScheduledActivityQueue` is a strict frozen model with exactly `activities: tuple[ScheduledActivity, ...]`.
* The queue accepts Python tuples and JSON/YAML-style lists, normalizes lists to tuples, permits an empty tuple, and preserves supplied activity order.
* Reject every other collection shape. Reject duplicate `activity_id` values and duplicate `insertion_sequence` values; check identity duplication before sequence duplication when both occur. Separate inputs test each rule rather than depending on combined-error aggregation.
* Equal `eligible_at_seconds` values and storage order unrelated to time, phase, or insertion sequence are valid.
* Contract construction does not resolve whether `schedule_id`, `npc_id`, or `hook_id` exists. Package schemas and relational validation for schedules and hooks do not yet exist.
* Do not add queue methods or functions for sorting, eligibility, partitioning, insertion, removal, execution, recurrence, persistence, or mutation.
* No new dependency is required.
* This public contract milestone advances the project version from `0.23.0` to `0.24.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact three scheduled-activity models, discriminated union, and queue model, and expose all five public names from `llm_system.simulation`.
* Add high-signal behavioral tests for union parsing and variant fields, strictness and immutability, required caller identity, non-negative time and sequence, list normalization, empty and unsorted order preservation, equal-time acceptance, and duplicate identity and sequence rejection.
* Update README and the accepted high-level-design principal-record description with exact contracts, derived-phase boundary, one-shot meaning, queue invariants, and execution/reference-validation exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Eligibility selection, ordering functions, phase enums or stored priorities, queue partitioning, removal, claiming, rescheduling, cancellation, retry, recurrence generation, activity execution, proposal creation, policy invocation, outcome resolution, state mutation, time advancement, tracing, persistence, SQLite, UI, API, or LLM calls.
* Authored environmental-schedule or System-director-hook definitions, scenario-package changes, reference resolution, game-package validation, runtime world-state integration, or Greybridge flood content.
* Changes to actions, submission sources, outcomes, events, state changes, world state, authorization, dispatch, resolvers, perception, commitment, or existing package contracts.
* Generic payload dictionaries, callbacks, protocols, registries, service classes, repositories, configuration layers, logging, ID providers, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-025 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/scheduling.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_scheduled_activity_contracts.py`.

The five new public names are exactly `EnvironmentalScheduledActivity`, `NpcScheduledActivity`, `SystemDirectorScheduledActivity`, `ScheduledActivity`, and `ScheduledActivityQueue`.

## Acceptance criteria

1. The public strict discriminated union accepts and round-trips exactly the three scheduled-activity variants with required application-supplied UUID, time, insertion sequence, and variant-specific reference (`SCHEDULE-007` through `SCHEDULE-009`).
2. Activity contracts reject extra fields, mutation, generated or missing identity, negative time, negative or non-integer sequence, and arbitrary executable payload while containing no stored phase priority (`SCHEDULE-008` through `SCHEDULE-010`, `SCHEDULE-015`).
3. Queue construction accepts tuples and JSON/YAML-style lists, normalizes to an immutable tuple, permits empty input, and preserves deliberately unsorted supplied storage order (`SCHEDULE-011`).
4. The queue rejects duplicate activity identities and duplicate insertion sequences while accepting equal eligibility times (`SCHEDULE-012`).
5. Records remain one-shot structural eligibility evidence without recurrence, cancellation, execution, policy, proposal, outcome, persistence, reference-resolution, or LLM behavior (`SCHEDULE-013` through `SCHEDULE-015`).
6. Public exports, README, and high-level design accurately describe the variants, derived phase, one-shot meaning, queue invariants, and deferred scheduler and package-validation boundaries.
7. Existing package, runtime-state, action, outcome, event, arbiter, resolver, perception, and installed-package behavior remains unchanged.
8. Project and installed metadata plus editable root `uv.lock` report `0.24.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production logic; record the import or missing-contract failure.
* Run focused contract tests after variant, queue, and strictness/immutability groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.23.0` to `0.24.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires scheduler selection or ordering behavior, a stored phase field, execution payload, recurrence or cancellation state, package schedule or hook definitions, reference validation, world-state integration, persistence, an existing contract change, a dependency, or generic infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
