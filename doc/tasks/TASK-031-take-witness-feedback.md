# TASK-031: Project immediate Take witness feedback

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-024, TASK-030

## Objective

Provide a pure event-feedback projection that gives a non-acting character an exact committed `ObjectTakenEvent` when that character was co-located with the object's previous location during the current simulation instant.

This task establishes immediate Take witnessing only. It does not reconstruct historical observer locations, implement richer visibility, trigger reactions, or compose perception fragments.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Event”, “Observation”, “Object placement”, “Perception engine”, “Simulation time”, “Take-witness feedback”, and “Validated world state”
* `doc/requirements.md`: `PERCEPTION-001` through `PERCEPTION-012`, `PERCEPTION-026` through `PERCEPTION-054`, `TAKE-001` through `TAKE-012`, and `LOOP-001`, `LOOP-005`, `LOOP-006`
* `doc/decisions.md`: “Separate truth, perception, memory, and belief”, “Begin perception with typed deterministic observation values”, “Begin event feedback with stateless self-action projection”, “Resolve Take v0 as direct co-located acquisition”, and “Project immediate co-located Take witnesses”
* `doc/high_level_design.md`: “Perception engine”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/events.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/perception_engine.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/resolvers/take.py`, `src/llm_system/simulation/__init__.py`, `tests/test_addressed_speech_feedback.py`, `tests/test_self_event_feedback.py`, `tests/test_take_resolver.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, persistence, scheduling, randomness, actor policies, prompts, or other task briefs.

## Fixed assumptions

* Add public `project_take_witness_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` to the existing perception-engine module.
* Validate `observer_id` first through the existing character-state namespace and reuse `PerceptionObserverNotFoundError` unchanged. An object or any absent identifier follows the same error path.
* Add public `WitnessEventTimeMismatchError`, a `ValueError` carrying exact public `event_id: UUID`, `occurred_at_seconds: int`, and `perceived_at_seconds: int` attributes. Its exact message is `canonical event {event_id} occurred at {occurred_at_seconds}, which does not match witness perception time {perceived_at_seconds}`.
* After observer validation, validate the entire supplied event tuple in input order before event-type or witness filtering. Every event must have `occurred_at_seconds == world.state.simulation_time_seconds`; raise `WitnessEventTimeMismatchError` for the first past or future mismatch, including a non-Take event or an event that would not match the observer.
* Emit feedback only when an event is `ObjectTakenEvent`, its `actor_id` differs from `observer_id`, its `previous_placement` is `ObjectAtLocation`, and that placement's `location_id` equals the observer's exact current canonical location.
* The taking actor never matches this projection even if co-located. Existing self-action feedback remains the actor's feedback path.
* A previous `ObjectPossessedByCharacter` placement never establishes a witness location and does not match. Do not treat the possessor, object owner, object target, or other participant role as witness evidence.
* The committed event's exact previous placement establishes the event location. Do not inspect the object's current placement, require the object still to exist at that location, consult authored initial placement, or call `project_current_perception`.
* For every match, create one `EventObserved` with `observation_type="event"`, `source_type="canonical_event"`, exact requested observer, current canonical observation time, and the exact input event object.
* Preserve matching input order and duplicates. Empty input and no matches return the immutable empty tuple. Do not deduplicate against self-action, addressed-speech, or any other feedback source.
* Candidate-event window selection, already-delivered tracking, composition, and cross-source ordering belong to a later caller or coordinator. This projection's exact-current-time validation makes a stale or future candidate-window defect explicit.
* The operation is stateless and deterministic and must not mutate or replace the world or event tuple, generate identities, record observations, create memory or belief, persist data, narrate, invoke an actor policy or LLM, or trigger a reaction.
* Keep current-state, self-action, and addressed-speech projection behavior, validation precedence, error contracts, ownership or recipient semantics, order, duplicates, and exact event-object retention unchanged.
* Internal helper refactoring is allowed only when it preserves all existing public behavior and error precedence. `FutureEventFeedbackError` remains unchanged and is not used for the new exact-time mismatch contract.
* Do not add a generic witness engine, visibility service, perception-fragment model, composition API, cursor, delivery record, reaction hook, protocol, registry, or new dependency.
* This public perception milestone advances the project version from `0.29.0` to `0.30.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact immediate Take-witness projection and mismatch error and expose both from `llm_system.simulation`.
* Add high-signal behavioral tests for co-located non-actor matches; actor, remote observer, non-Take event, and possessed-previous-placement exclusion; post-commit current-object independence; observer-first validation; first whole-batch past/future mismatch; exact object retention; order and duplicate preservation; empty/no-match behavior; determinism; input immutability; and unchanged existing feedback behavior.
* Update README with the implemented API, exact-current-time contract, previous-placement location rule, and exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Take resolution or dispatch changes, outcome or canonical-event contract changes, current-state perception changes, self-action ownership changes, addressed-speech recipient changes, or new observation variants.
* Historical witness reconstruction, past-event acceptance, line-of-sight, concealment, attention, sensory traits, within-location geometry, ownership visibility, current object placement filtering, or other event-specific witness rules.
* Perception-snapshot or feedback-fragment composition, cross-source ordering, deduplication, event-window queries, cursors, delivery tracking, observation recording, persistence, SQLite, memory, belief, sensemaking, reaction generation, policies, prompts, LLM calls, narration, UI, or API behavior.
* Logging, metrics, services, protocols, registries, repositories, ID providers, generic filtering frameworks, or new dependencies.
* Changes to requirements, decisions, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-031 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/perception_engine.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_take_witness_feedback.py`; existing self-action and addressed-speech tests may change only when necessary to verify preserved shared behavior.

The two new public names are exactly `project_take_witness_feedback` and `WitnessEventTimeMismatchError`. Existing `project_current_perception`, `project_self_event_feedback`, `project_addressed_speech_feedback`, `PerceptionObserverNotFoundError`, `FutureEventFeedbackError`, `ObjectTakenEvent`, `EventObserved`, and Take resolver behavior remain unchanged.

## Acceptance criteria

1. A current-time `ObjectTakenEvent` produces exact feedback for a non-actor observer whose current location equals the event's previous `ObjectAtLocation` (`PERCEPTION-045`, `PERCEPTION-048`, `PERCEPTION-049`).
2. The taking actor, a remote observer, non-Take events, and events with previous character possession produce no Take-witness feedback (`PERCEPTION-048`).
3. Observer validation precedes event inspection and reuses `PerceptionObserverNotFoundError` unchanged (`PERCEPTION-046`).
4. Whole-batch exact-current-time validation precedes filtering and raises the exact new error for the first past or future event, including otherwise irrelevant events (`PERCEPTION-047`).
5. Matching eligibility uses the exact committed previous location and remains unchanged after successful Take commitment moves the object's current placement to actor possession (`PERCEPTION-051`).
6. Matching order and duplicates are preserved with exact event-object identity; empty and no-match input returns `()` (`PERCEPTION-049`, `PERCEPTION-050`).
7. Candidate windows, delivery tracking, composition, cross-source ordering, and deduplication remain caller responsibilities (`PERCEPTION-052`).
8. Repeated projection is deterministic, preserves exact immutable inputs, and has no richer visibility, persistence, memory, belief, policy, LLM, reaction, narration, or presentation behavior (`PERCEPTION-053`).
9. Existing current-state, self-action, and addressed-speech feedback retains exact public behavior and error precedence (`PERCEPTION-054`).
10. Public exports, README, and accepted high-level design accurately describe immediate Take-witness feedback and its temporal, spatial, identity, and scope boundaries.
11. Existing package, world-validation, action, authorization, outcome, event, resolver, dispatch, randomness, scheduler, and commitment behavior remains unchanged.
12. Project and installed metadata plus editable root `uv.lock` report `0.30.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing Take-witness tests before production logic; record genuine red evidence.
* `uv run pytest tests/test_take_witness_feedback.py tests/test_self_event_feedback.py tests/test_addressed_speech_feedback.py tests/test_take_resolver.py tests/test_package.py -q`
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.29.0` to `0.30.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires past-event witness reconstruction, a different event-location source, current object placement filtering, visual-perception reuse, richer visibility, feedback composition, delivery persistence, reaction generation, existing feedback changes, another new contract, a dependency, or generic perception infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
