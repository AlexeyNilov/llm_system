# TASK-024: Project stateless self-action event feedback

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-014, TASK-021, TASK-022

## Objective

Provide the first pure canonical-event feedback operation: project a caller-selected batch of canonical events into the exact self-action `EventObserved` values available to one character at current canonical time.

This task handles action ownership only. It does not decide what other characters witnessed, compose a complete perception snapshot, or track which events were already delivered.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Event”, “Feedback”, “Observation”, “Perception engine”, “Perceptual filtering”, “Perception snapshot”, “Simulation time”, and “Validated world state”
* `doc/requirements.md`: `EVENT-001` through `EVENT-013`, `PERCEPTION-001` through `PERCEPTION-035`, and `LOOP-001`, `LOOP-005`, `LOOP-006`
* `doc/decisions.md`: “Separate truth, perception, memory, and belief”, “Use an explicit cognition and action loop”, “Retain typed canonical events without full event sourcing”, “Begin canonical events with eight actor-operation facts”, “Begin perception with typed deterministic observation values”, “Project current state before filtering event feedback”, and “Begin event feedback with stateless self-action projection”
* `doc/high_level_design.md`: “Perception engine”, “Principal records”, “Actor loop”, “Simulation-step flow”, and “Testing strategy”
* `src/llm_system/simulation/events.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/perception_engine.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/__init__.py`, `tests/test_current_state_perception.py`, `tests/test_events.py`, `tests/test_perception_contracts.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, resolver or dispatch implementation, or other task briefs.

## Fixed assumptions

* The public operation is `project_self_event_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]`.
* The public `FutureEventFeedbackError` subclasses `ValueError`. Its constructor accepts the offending event's UUID, occurrence seconds, and the world's current simulation seconds; it stores public typed attributes `event_id`, `occurred_at_seconds`, and `perceived_at_seconds` and supplies stable non-blank text identifying that the event is later than perception time.
* Resolve `observer_id` first in the same `world.state.characters` namespace as `project_current_perception`. Reuse the exact existing `PerceptionObserverNotFoundError` for an unknown or object observer, before reading candidate-event timing.
* After observer validation, validate every supplied event in tuple order against `world.state.simulation_time_seconds` before ownership filtering. Raise `FutureEventFeedbackError` for the first event whose `occurred_at_seconds` is greater, including a non-owned event. Do not return a partial tuple.
* Determine ownership exhaustively across the closed initial union: `ActorSpokeEvent.speaker_id`; and `actor_id` for `ActorObservedEvent`, `ActorMovedEvent`, `ObjectTakenEvent`, `ObjectUsedEvent`, `ActorHelpedEvent`, `ActorWaitedEvent`, and `ActorActionFailedEvent`.
* Recipient, assisted character, observation or use target, object identity or placement, spatial proximity, and current possession do not make an observer the event owner.
* Preserve supplied event order and duplicate matching inputs. Do not sort, deduplicate, group, or query canonical history.
* For each owned event, construct `EventObserved(observation_type="event", source_type="canonical_event", observer_id=observer_id, observed_at_seconds=world.state.simulation_time_seconds, event=event)` and retain the exact supplied event object.
* Empty input or no owned event returns exact immutable `()`.
* Past and current-time events are eligible; this boundary does not apply a lookback window.
* Candidate batch selection and already-delivered tracking belong to the caller or later coordinator/persistence work. This function is a stateless projection and may return the same feedback again when called with the same events.
* Repeated calls for equal inputs return equal tuples and do not mutate, copy, replace, or commit the validated world or supplied events.
* Do not return `PerceptionSnapshot`, call `project_current_perception`, compose current-state observations, determine witness visibility or audibility, enrich definitions, record observations, persist delivery state, create memory or beliefs, generate IDs, invoke an LLM, or perform narration or presentation.
* No new dependency is required.
* This public perception milestone advances the project version from `0.22.0` to `0.23.0`; the lockfile's editable root-package version must match.

## In scope

* Add `FutureEventFeedbackError` and `project_self_event_feedback` to the existing perception-engine boundary and expose both from `llm_system.simulation`.
* Add high-signal behavioral tests for exhaustive ownership, actor versus participant distinctions, mixed ordered filtering, duplicate preservation, empty/no-match behavior, past/current time, future-event rejection, observer-first validation, exact object retention, determinism, and input immutability.
* Update README and the accepted high-level-design perception descriptions with the self-feedback API, ownership and timing rules, caller-owned window, and explicit witness/composition exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Changing canonical-event, observation, snapshot, current-state projection, action, outcome, resolver, dispatch, authorization, or commitment contracts.
* Witness feedback, speech hearing, recipient awareness, assisted-character awareness, target awareness, pre- or post-action location reconstruction, co-location, line of sight, environment, concealment, attention, sensory capabilities, or event-specific rule packs.
* Combining state and event observations, returning a complete perception snapshot, ordering state relative to event observations, or narrator/NPC context assembly.
* Querying canonical event history, persistence, delivery cursors, deduplication, observation identity or recording, SQLite, episodic memory, beliefs, retrieval, scheduler behavior, UI, API, narration, or LLM calls.
* Generic filter protocols, registries, visibility policies, service classes, caches, ID providers, logging, configuration, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-024 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/perception_engine.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_self_event_feedback.py`.

The two new public names are exactly `FutureEventFeedbackError` and `project_self_event_feedback`. Existing `CanonicalEvent`, `EventObserved`, `PerceptionObserverNotFoundError`, `project_current_perception`, and `PerceptionSnapshot` contracts remain unchanged.

## Acceptance criteria

1. Each of the eight initial canonical-event variants produces one self-action `EventObserved` for its actor or speaker and retains the exact event object (`PERCEPTION-028`, `PERCEPTION-029`, `PERCEPTION-031`).
2. Mixed event batches exclude other actors' events, preserve matching input order, and do not treat recipients, assisted characters, targets, objects, possession, or proximity as ownership (`PERCEPTION-028`, `PERCEPTION-029`, `PERCEPTION-032`).
3. Past and current-time matching events are accepted; empty and no-match batches return `()`; duplicate matching inputs remain duplicated (`PERCEPTION-032`).
4. The entire candidate batch is validated before filtering, and the first future event raises `FutureEventFeedbackError` with exact typed attributes even when another actor owns it; no partial result is returned (`PERCEPTION-030`).
5. Unknown or object observers raise the existing exact observer error before future-event validation (`PERCEPTION-027`, `PERCEPTION-030`).
6. Every output uses the requested observer and current canonical observation time with `source_type="canonical_event"`, without generated identity, copied payload, enrichment, prose, or mutation (`PERCEPTION-031`, `PERCEPTION-034`).
7. The operation is stateless and deterministic, preserves the exact immutable world and supplied event tuple, and does not query history, deduplicate, record delivery, or compose a snapshot (`PERCEPTION-033` through `PERCEPTION-035`).
8. Public exports, README, and high-level design accurately describe self-action ownership, whole-batch temporal validation, caller-owned delivery window, and witness/composition boundaries.
9. Existing package, world-validation, event, observation, current-state perception, action, resolver, dispatch, authorization, outcome, and commitment behavior remains unchanged.
10. Project and installed metadata plus editable root `uv.lock` report `0.23.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production logic; record the import or missing-contract failure.
* Run focused feedback tests after exhaustive ownership, filtering/window, and validation/determinism groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.22.0` to `0.23.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires witness semantics, target or recipient awareness, pre- or post-action location state, a delivery cursor, history access, deduplication, current-state composition, an observation or event contract change, persistence, enrichment, recording, a dependency, or generic filter infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented stateless self-action event feedback with exhaustive initial-event ownership, observer-first and whole-batch temporal validation, exact event retention, public exports, documentation, and the `0.23.0` version milestone.

**Changed files:** `src/llm_system/simulation/perception_engine.py`; `src/llm_system/simulation/__init__.py`; `tests/test_self_event_feedback.py`; `tests/test_package.py`; `README.md`; `doc/high_level_design.md`; `pyproject.toml`; `uv.lock`; `doc/tasks/TASK-024-self-event-feedback.md`.

**Verification:** Initial red: `.venv/bin/pytest -q tests/test_self_event_feedback.py` failed during collection with `ImportError: cannot import name 'FutureEventFeedbackError' from 'llm_system.simulation'`. Focused green: `.venv/bin/pytest -q tests/test_self_event_feedback.py` -> `4 passed`; focused regression set -> `23 passed`. Final green: `uv sync --locked`; `make format`; `make lint`; `make mypy` -> no issues in 52 source files; `make test` -> `203 passed`; `make check` -> formatting, lint, mypy, and `203 passed`; `uv lock --check`; `git diff --check`. `uv.lock` diff contains only editable root `llm-system` version `0.22.0` to `0.23.0`.

**Deviations:** None.

**Design gaps or follow-ups:** None.
