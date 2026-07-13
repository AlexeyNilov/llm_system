# TASK-029: Project addressed-speech recipient feedback

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-024, TASK-028

## Objective

Provide a pure event-feedback projection that gives a character exact committed speech events explicitly addressed to that character.

This task establishes addressed recipient delivery only. It does not implement overhearing, response generation, memory, persistence, or composition with other perception fragments.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Addressed-speech feedback”, “Event”, “Observation”, “Perception engine”, “Simulation arbiter”, “Simulation time”, and “Speech audibility”
* `doc/requirements.md`: `PERCEPTION-001` through `PERCEPTION-012`, `PERCEPTION-026` through `PERCEPTION-044`, `SPEAK-001` through `SPEAK-011`, and `LOOP-001`, `LOOP-005`, `LOOP-006`
* `doc/decisions.md`: “Separate truth, perception, memory, and belief”, “Begin perception with typed deterministic observation values”, “Begin event feedback with stateless self-action projection”, “Resolve Speak v0 as co-located zero-time speech”, and “Project addressed speech from committed recipient identity”
* `doc/high_level_design.md`: “Perception engine”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/events.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/perception_engine.py`, `src/llm_system/simulation/resolvers/speak.py`, `src/llm_system/simulation/__init__.py`, `tests/test_perception_contracts.py`, `tests/test_self_event_feedback.py`, `tests/test_speak_resolver.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, persistence, scheduling, randomness, actor policies, prompts, or other task briefs.

## Fixed assumptions

* Add public `project_addressed_speech_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` to the existing perception-engine module.
* Validate `observer_id` first through the existing character-state namespace and reuse `PerceptionObserverNotFoundError` unchanged. An object or any absent identifier follows the same error path.
* After observer validation, validate the entire supplied event tuple in input order against `world.state.simulation_time_seconds` before event-type or recipient filtering. Reuse `FutureEventFeedbackError` unchanged for the first future event, including a future non-speech or speech event addressed to someone else.
* Emit feedback only when an event is `ActorSpokeEvent` and its `recipient_id` equals `observer_id`. Other event variants, speeches to other recipients, speaker ownership, participant roles, object possession, and spatial proximity do not match.
* Recipient identity on the committed event is sufficient evidence that Speak resolution established audibility at occurrence time. Do not inspect or compare current speaker or recipient locations and do not call `project_current_perception`.
* Later movement cannot revoke delivery of a past addressed event. A current world in which the speaker and recipient are remote from each other must still project a matching past or current-time addressed event.
* For every match, create one `EventObserved` with `observation_type="event"`, `source_type="canonical_event"`, exact requested observer, current canonical observation time, and the exact input event object.
* Preserve matching input order and duplicates. Empty input and no matches return the immutable empty tuple. Do not deduplicate against self-action feedback or any other source.
* Candidate-event window selection, already-delivered tracking, composition with self feedback or current-state perception, and cross-source ordering belong to a later caller or coordinator.
* The operation is stateless and deterministic and must not mutate or replace the world or event tuple, generate identities, record observations, create memory or belief, persist data, narrate, invoke an actor policy or LLM, or generate a response.
* Keep `project_self_event_feedback` behavior and ownership unchanged; a recipient does not become an event owner.
* Internal helper refactoring is allowed only when it preserves current public behavior, validation precedence, exact errors, and object identity for self-action feedback.
* Do not add a generic witness engine, audibility service, perception-fragment model, composition API, cursor, delivery record, protocol, registry, or new error type.
* No new dependency is required.
* This public perception milestone advances the project version from `0.27.0` to `0.28.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact addressed-speech feedback projection and expose it from `llm_system.simulation`.
* Add high-signal behavioral tests for exact recipient matches; exclusion of other recipients and non-speech events; past/current acceptance despite later movement; observer-first and whole-batch temporal validation; exact object retention; order and duplicate preservation; empty/no-match behavior; determinism; input immutability; and unchanged self-feedback ownership.
* Update README and accepted high-level-design perception descriptions with the implemented API, temporal semantics, event identity rule, and exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Speak resolution or dispatch changes, outcome or event contract changes, self-action ownership changes, current-state perception changes, or new observation variants.
* General witness visibility, overhearing, co-location reconstruction, hearing range, barriers, volume, language comprehension, sensory traits, attention, concealment, speaker perception, or present-location filtering.
* Perception-snapshot or feedback-fragment composition, cross-source ordering, deduplication, event-window queries, cursors, delivery tracking, observation recording, persistence, SQLite, memory, belief, sensemaking, response generation, policies, prompts, LLM calls, narration, UI, or API behavior.
* Logging, metrics, services, protocols, registries, repositories, ID providers, generic filtering frameworks, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-029 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/perception_engine.py`, with public re-export from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_addressed_speech_feedback.py`; existing self-feedback tests may change only when necessary to verify preserved shared behavior.

The one new public name is exactly `project_addressed_speech_feedback`. Existing `project_self_event_feedback`, `PerceptionObserverNotFoundError`, `FutureEventFeedbackError`, `ActorSpokeEvent`, `EventObserved`, and Speak resolver behavior remain unchanged.

## Acceptance criteria

1. Past and current-time `ActorSpokeEvent` values addressed to the observer produce exact event observations at current canonical time, including after speaker or recipient movement (`PERCEPTION-036`, `PERCEPTION-039` through `PERCEPTION-041`).
2. Other event variants and speech addressed to another character produce no recipient feedback; speaker ownership alone does not match (`PERCEPTION-039`).
3. Observer validation precedes event inspection, and whole-batch future validation precedes type and recipient filtering while reusing exact existing error contracts (`PERCEPTION-037`, `PERCEPTION-038`).
4. Matching order and duplicates are preserved with exact event-object identity; empty and no-match input returns `()` (`PERCEPTION-041`, `PERCEPTION-042`).
5. Projection does not inspect current co-location or visual perception, and later movement cannot revoke historical addressed delivery (`PERCEPTION-039`, `PERCEPTION-040`).
6. Candidate windows, delivery tracking, self/current-state composition, cross-source ordering, and deduplication remain caller responsibilities (`PERCEPTION-043`).
7. Repeated projection is deterministic, preserves exact immutable inputs, and has no persistence, memory, belief, policy, LLM, response, narration, or general witness behavior (`PERCEPTION-044`).
8. Existing self-action feedback retains speaker-only ownership for `ActorSpokeEvent`, exact validation precedence, order, duplicates, and object identity (`PERCEPTION-026` through `PERCEPTION-035`).
9. Public exports, README, and high-level design accurately describe addressed-speech feedback, committed-recipient temporal semantics, and all deferred composition and witness boundaries.
10. Existing package, world-validation, action, authorization, outcome, event, resolver, dispatch, current-perception, randomness, scheduler, and commitment behavior remains unchanged.
11. Project and installed metadata plus editable root `uv.lock` report `0.28.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing addressed-speech tests before production logic; record genuine red evidence.
* `uv run pytest tests/test_addressed_speech_feedback.py tests/test_self_event_feedback.py tests/test_speak_resolver.py tests/test_package.py -q`
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.27.0` to `0.28.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires event-time location reconstruction, present-location filtering, visual-perception reuse, general witness audibility, feedback composition, delivery persistence, response generation, self-ownership changes, a new error or data contract, a dependency, or generic perception infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented pure addressed-speech recipient feedback with public
export, exact committed-event retention, observer-first and whole-batch temporal
validation, and committed-recipient delivery semantics independent of current
location or visual perception.

**Changed files:** `src/llm_system/simulation/perception_engine.py`,
`src/llm_system/simulation/__init__.py`,
`tests/test_addressed_speech_feedback.py`, `tests/test_package.py`, `README.md`,
`doc/high_level_design.md`, `pyproject.toml`, `uv.lock`, and this task brief.

**Verification:** Genuine red: `uv run pytest
tests/test_addressed_speech_feedback.py -q` failed during collection because
`project_addressed_speech_feedback` was not yet exported. Final green: focused
required pytest command, 18 passed; `uv sync --locked`; `make format`; `make
lint`; `make mypy`; `make test`, 260 passed; `make check`, 260 passed; `uv lock
--check`; lock diff inspection confirmed only editable root `0.27.0` to `0.28.0`;
and `git diff --check`.

**Deviations:** None.

**Design gaps or follow-ups:** None within TASK-029 scope. Candidate-window
selection, delivery tracking, composition, ordering, deduplication, overhearing,
memory, and response generation remain explicitly deferred.
