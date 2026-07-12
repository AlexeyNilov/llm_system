# TASK-014: Define state-change and canonical-event contracts

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-013

## Objective

Provide strict immutable public leaf contracts for self-verifying changes to canonical runtime snapshots and for the eight initial actor-operation facts retained as canonical events.

This task defines typed deltas and factual records only. It does not aggregate them into outcomes, apply them to state, validate them against a world, or make visibility and narration decisions.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Action”, “Canonical world state”, “Event”, “Outcome”, and “Simulation arbiter”
* `doc/requirements.md`: `STATE-038` through `STATE-042` and `EVENT-001` through `EVENT-013`
* `doc/decisions.md`: “Represent state changes as self-verifying before-and-after deltas”, “Retain typed canonical events without full event sourcing”, “Timestamp outcomes and events at atomic completion”, “Begin canonical events with eight actor-operation facts”, and “Define state changes and events before outcome aggregates”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/_types.py`, `src/llm_system/simulation/__init__.py`, `tests/test_actions.py`, `tests/test_runtime_state.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* All contracts are strict frozen Pydantic 2 models that forbid unknown fields, use immutable nested values, and contain no generated IDs or mutable collections.
* `CharacterLocationChanged` uses discriminator `character_location`, identifies `character_id`, and contains distinct `from_location_id` and `to_location_id`.
* `ObjectPlacementChanged` uses discriminator `object_placement`, identifies `object_id`, and contains distinct `from_placement` and `to_placement` values using the existing runtime `ObjectPlacement` union.
* `ConnectionAvailabilityChanged` uses discriminator `connection_availability`, identifies `connection_id`, and contains distinct strict booleans `from_available` and `to_available`.
* `SimulationTimeChanged` uses discriminator `simulation_time`, contains non-negative strict integer `from_seconds` and `to_seconds`, and requires `to_seconds > from_seconds`.
* `StateChange` is a closed union of exactly those four variants, discriminated by `change_type`.
* The seven supported operation strings shall be exposed once as public `ActorActionOperation` and reused by action-failed events without changing existing proposal behavior.
* Every event contains required application-supplied `uuid.UUID` `event_id` and `outcome_id`, non-negative strict integer `occurred_at_seconds`, and its exact `event_type`; no field has an ID or time default.
* Event discriminator values are `actor_observed`, `actor_moved`, `actor_spoke`, `object_taken`, `object_used`, `actor_helped`, `actor_waited`, and `actor_action_failed`.
* `ActorObservedEvent` contains `actor_id` and an existing `ObservationTarget`.
* `ActorMovedEvent` contains `actor_id`, `connection_id`, distinct `from_location_id` and `to_location_id`.
* `ActorSpokeEvent` contains `speaker_id`, `recipient_id`, and non-blank `utterance`. Do not impose an unaccepted speaker/recipient inequality.
* `ObjectTakenEvent` contains `actor_id`, `object_id`, and `previous_placement: ObjectPlacement`.
* `ObjectUsedEvent` contains `actor_id`, `object_id`, and an existing `UseTarget`.
* `ActorHelpedEvent` contains `actor_id` and `assisted_character_id`. Do not impose an unaccepted actor/assisted-character inequality.
* `ActorWaitedEvent` contains `actor_id` and strictly positive integer `duration_seconds`.
* `ActorActionFailedEvent` contains `actor_id` and `attempted_operation: ActorActionOperation`.
* `CanonicalEvent` is a closed union of exactly those eight variants, discriminated by `event_type`.
* Events contain no visibility, observer, perception result, narration, state-change collection, proposal, outcome status, reason code, source authority, or persistence behavior.
* This task validates only context-free leaf invariants such as unequal before/after values. Event/outcome causation agreement, duplicate changes or events, state matching, and operation semantics belong to TASK-015 or the arbiter.
* Shared private identifier, non-blank-text, positive-seconds, or non-negative-seconds aliases may be centralized within `llm_system.simulation` if existing public behavior remains unchanged; private helpers must not be exported.
* No new dependency is required.
* This public contract milestone advances the project version from `0.12.0` to `0.13.0`; the lockfile's editable root-package version must match.

## In scope

* Add the four state-change models and closed `StateChange` union.
* Add `ActorActionOperation`, eight canonical-event models, and closed `CanonicalEvent` union.
* Expose all intended public contracts from `llm_system.simulation`.
* Add behavioral tests for each discriminator, valid payload and JSON round-trip, unequal-value rules, strict time/boolean/duration handling, UUID injection, immutability, forbidden fields, typed target/placement reuse, and absence of presentation concerns.
* Preserve all existing action, runtime-state, and world-state-validation behavior if private aliases are refactored.
* Update README with the delta-versus-event distinction, public variants, and explicit limitations.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Outcome models or reason codes, nested outcome consistency, state-change application, conflict detection across multiple changes, or event-ID uniqueness.
* State-dependent validation, source authorization, operation resolution, random draws, world initialization, scheduler behavior, perception, persistence, APIs, or UI.
* Visibility, observations produced by perception, narration, System notifications, event storage, or event replay.
* World-action, scheduled-activity, objective, progression, Fieldcraft, flood, bridge-condition, or other Greybridge-specific changes and events.
* Additional state-change or event variants, generic payload dictionaries, public registries, plugin mechanisms, or executable callbacks.
* Changes to game-package schemas or existing public behavior.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production files are `src/llm_system/simulation/changes.py` and `src/llm_system/simulation/events.py`, with public exports from `src/llm_system/simulation/__init__.py`. Focused tests likely belong in `tests/test_state_changes.py` and `tests/test_events.py`.

Public names are `ActorActionOperation`, `CharacterLocationChanged`, `ObjectPlacementChanged`, `ConnectionAvailabilityChanged`, `SimulationTimeChanged`, `StateChange`, all eight event model names fixed above, and `CanonicalEvent`.

## Acceptance criteria

1. `StateChange` discriminates exactly the four accepted typed delta variants and rejects equal before/after values, invalid identifiers, unknown fields, invalid discriminators, and non-strict scalar types (`STATE-038` through `STATE-041`).
2. Object-placement deltas reuse exact runtime placement variants and simulation time only moves forward (`STATE-039` through `STATE-041`).
3. `CanonicalEvent` discriminates exactly the eight accepted factual variants with required injected UUID identities, strict non-negative occurrence time, and operation-specific payloads (`EVENT-007` through `EVENT-012`).
4. Observation and use events reuse their accepted target unions; taken events reuse runtime placement; failed-action events accept exactly the seven `ActorActionOperation` values (`EVENT-009`, `EVENT-011`, `EVENT-012`).
5. Move events reject equal previous/new locations, speech rejects blank utterance, and wait rejects boolean, zero, or negative duration (`EVENT-010` through `EVENT-012`).
6. Event contracts expose no visibility, narration, observer list, generated identity, or persistence behavior and do not require an outcome aggregate (`EVENT-003`, `EVENT-004`, `EVENT-008`, `EVENT-013`).
7. Models and unions serialize deterministically and validate strict JSON representations suitable for later trace and persistence boundaries.
8. Public exports and README accurately distinguish snapshot deltas from canonical factual history and state all deferred consistency and application behavior (`STATE-042`, `EVENT-006`).
9. Existing simulation and package behavior remains unchanged.
10. Project and installed metadata plus the editable root in `uv.lock` report `0.13.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production contract logic; record the import or missing-contract failure.
* Run focused state-change and event tests after each contract group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is the editable root package version from `0.12.0` to `0.13.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires outcome semantics, another variant, state or authority lookup, changing accepted field meaning, generic payloads, persistence behavior, public action behavior changes, a dependency, or richer mechanics.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
