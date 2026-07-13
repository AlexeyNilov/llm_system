# TASK-026: Select and order eligible scheduled activities

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-025, TASK-013

## Objective

Provide a pure deterministic scheduler operation that partitions one validated activity queue at canonical world time into ordered eligible work and the remaining future queue.

This task selects and orders only. It does not claim, persist, execute, retry, or recursively process any activity.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Scheduled activity”, “Scheduled activity queue”, “Scheduled activity selection”, “Scheduler”, “Simulation time”, and “Validated world state”
* `doc/requirements.md`: `TIME-001` through `TIME-006` and `SCHEDULE-001` through `SCHEDULE-023`
* `doc/decisions.md`: “Use discrete, action-driven simulation time”, “Serialize eligible activities deterministically”, “Represent scheduled work as one-shot typed eligibility records”, and “Partition due scheduled activities without executing them”
* `doc/high_level_design.md`: “Clock and scheduler”, “Principal records”, “Simulation-step flow”, and “Testing strategy”
* `src/llm_system/simulation/scheduling.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/__init__.py`, `tests/test_scheduled_activity_contracts.py`, `tests/test_world_state_validation.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, activity execution, resolvers, perception, persistence, package implementation, or other task briefs.

## Fixed assumptions

* Add public `select_eligible_activities(world: ValidatedWorldState, queue: ScheduledActivityQueue) -> ScheduledActivitySelection` to the existing scheduling module.
* `ScheduledActivitySelection` is a public strict frozen Pydantic model with exactly `selected_at_seconds: NonNegativeSeconds`, `eligible_activities: tuple[ScheduledActivity, ...]`, and `remaining_queue: ScheduledActivityQueue`.
* `eligible_activities` accepts Python tuples and serialized JSON/YAML-style lists, normalizes lists to tuples, and rejects every other collection shape.
* Selection time is exactly `world.state.simulation_time_seconds`; the function takes no caller time and does not inspect wall-clock time.
* An activity is eligible when its eligibility time is less than or equal to selection time. Do not discard or specially classify overdue activity.
* Derive phase rank exhaustively from the closed activity union: environmental zero, NPC one, System director two. Do not add a public phase enum, stored phase field, or configurable priority.
* Sort eligible activities by exact key `(eligible_at_seconds, phase_rank, insertion_sequence)`. Do not use activity UUID or original tuple position as an additional key.
* Preserve pending activities in exact input queue storage order, regardless of their time, phase, or insertion metadata.
* Retain the exact input scheduled-activity objects in eligible and pending results; do not reconstruct or copy them.
* The selection result's model validation requires: every eligible activity is due; eligible activities equal their exact sorted order; every remaining activity is strictly future; combined activity IDs are unique; and combined insertion sequences are unique. Use this validation order. Separate tests should target each invariant rather than relying on aggregated errors.
* The result cannot prove completeness relative to an unavailable original queue and need not retain the original queue as a field.
* When no activity is eligible, return the exact input queue object as `remaining_queue`. When at least one is eligible, construct a new queue from pending activities; if all are eligible, that new queue is empty.
* Empty queues and results with an empty eligible tuple are valid when temporally consistent.
* Repeated calls for equal inputs return equal results and do not mutate, copy, replace, commit, or revalidate the world or input queue.
* Do not add queue mutation methods, eligibility classes, activity claiming, locks, transactions, persistence, execution dispatch, callbacks, policy or LLM invocation, proposals, outcomes, retries, cancellation, recurrence, newly scheduled activity handling, cascading loops, tracing, randomness, reference validation, generic scheduler services, or configuration.
* No new dependency is required.
* This public scheduler milestone advances the project version from `0.24.0` to `0.25.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact self-validating selection result and pure selection operation, and expose both from `llm_system.simulation`.
* Add high-signal behavioral tests for inclusive due/overdue eligibility, future partitioning, exact ordering across time/phase/sequence, pending storage order, empty/none/some/all eligible cases, exact object retention and queue reuse, serialized normalization, model invariants, determinism, and input immutability.
* Update README and accepted high-level-design scheduler descriptions with the API, ordering and partition rules, identity guarantees, self-validation, and execution/persistence exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Activity execution, environmental mechanics, NPC policy or System-director invocation, action submission, outcome resolution or commitment, canonical events, world mutation, simulation-time advancement, retries, errors during execution, recurrence, cancellation, rescheduling, activity insertion, cascading eligibility, tracing, persistence, transactions, queue claims, locks, SQLite, UI, API, or LLM calls.
* Authored schedule or hook definitions, Greybridge flood content, package reference validation, runtime-world queue integration, or changes to scheduled-activity variants and queue contracts.
* Changes to world state, actions, outcomes, events, authorization, dispatch, resolvers, perception, commitment, or package contracts.
* Public phase models, generic sorter protocols, registries, service classes, repositories, configuration layers, logging, ID providers, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-026 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/scheduling.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_scheduled_activity_selection.py`.

The two new public names are exactly `ScheduledActivitySelection` and `select_eligible_activities`. Existing scheduled-activity variants, union, queue, world, and time contracts remain unchanged.

## Acceptance criteria

1. Selection uses exact canonical world time and treats overdue and exactly due activities as eligible while retaining strictly future activities (`SCHEDULE-016`, `SCHEDULE-018`).
2. Eligible activities are ordered exactly by time, derived environmental/NPC/System-director phase, and insertion sequence, independent of queue storage and UUID order (`SCHEDULE-019`).
3. Pending activities preserve exact input storage order and all output groups retain exact scheduled-activity objects (`SCHEDULE-020`).
4. The strict immutable result normalizes serialized eligible lists and rejects future eligible activity, due pending activity, incorrect eligible order, duplicate activity identity, or duplicate insertion sequence across the partition (`SCHEDULE-017`, `SCHEDULE-021`).
5. Empty, none-eligible, some-eligible, and all-eligible inputs produce exact valid partitions; none-eligible reuses the input queue and every nonempty selection creates a new remaining queue (`SCHEDULE-022`).
6. Selection is deterministic and preserves the exact immutable world and queue without execution, reference resolution, identity generation, randomness, persistence, or LLM behavior (`SCHEDULE-023`).
7. Public exports, README, and high-level design accurately describe the API, inclusive threshold, exact ordering, pending order, identity rules, result self-validation, and deferred execution and persistence boundaries.
8. Existing package, world, activity-contract, action, outcome, event, arbiter, resolver, perception, and installed-package behavior remains unchanged.
9. Project and installed metadata plus editable root `uv.lock` report `0.25.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production logic; record the import or missing-contract failure.
* Run focused selection tests after partition/order, result-validation, and identity/determinism groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.24.0` to `0.25.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires executing or persisting activities, claiming a queue, changing time, processing newly scheduled work, recurrence, retries, package definitions or reference validation, public phase configuration, an existing contract change, a dependency, or generic scheduler infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
