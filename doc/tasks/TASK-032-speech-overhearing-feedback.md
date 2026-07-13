# TASK-032: Project immediate third-party speech overhearing

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-024, TASK-028, TASK-029, TASK-031

## Objective

Provide a pure event-feedback projection that gives a co-located third party an exact committed `ActorSpokeEvent` during the current simulation instant.

This task establishes immediate speech overhearing only. It keeps speaker self-feedback and addressed-recipient delivery separate and does not reconstruct historical locations, model comprehension, trigger reactions, or compose perception fragments.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Event”, “Observation”, “Perception engine”, “Simulation time”, “Speech audibility”, “Speech-overhearing feedback”, and “Validated world state”
* `doc/requirements.md`: `PERCEPTION-001` through `PERCEPTION-012`, `PERCEPTION-026` through `PERCEPTION-064`, `SPEAK-001` through `SPEAK-011`, and `LOOP-001`, `LOOP-005`, `LOOP-006`
* `doc/decisions.md`: “Separate truth, perception, memory, and belief”, “Begin perception with typed deterministic observation values”, “Begin event feedback with stateless self-action projection”, “Resolve Speak v0 as co-located zero-time speech”, “Project addressed speech from committed recipient identity”, “Project immediate co-located Take witnesses”, and “Project immediate third-party speech overhearing”
* `doc/high_level_design.md`: “Perception engine”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/events.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/perception_engine.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/resolvers/speak.py`, `src/llm_system/simulation/__init__.py`, `tests/test_addressed_speech_feedback.py`, `tests/test_self_event_feedback.py`, `tests/test_speak_resolver.py`, `tests/test_take_witness_feedback.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, persistence, scheduling, randomness, actor policies, prompts, or other task briefs.

## Fixed assumptions

* Add public `project_speech_overhearing_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` to the existing perception-engine module.
* Validate `observer_id` first through the existing character-state namespace and reuse `PerceptionObserverNotFoundError` unchanged. An object or any absent identifier follows the same observer error path.
* After observer validation, validate the entire supplied event tuple in input order before event-type or overhearing filtering. Every event must have `occurred_at_seconds == world.state.simulation_time_seconds`; reuse `WitnessEventTimeMismatchError` unchanged for the first past or future mismatch, including a non-speech event or an event that would not match the observer.
* Add public `SpeechSpeakerNotFoundError`, a `ValueError` carrying exact public `event_id: UUID` and `speaker_id: AuthoredId` attributes. Its exact message is `actor-spoke event {event_id} references missing speaker: {speaker_id}`.
* After observer and time validation, resolve the speaker of every supplied `ActorSpokeEvent` in input order before observer-specific filtering. Raise `SpeechSpeakerNotFoundError` for the first absent speaker even when that event names the observer as speaker or recipient, is remote from the observer, or otherwise would not match.
* Do not validate speakers for non-speech events. Do not revalidate an `ActorSpokeEvent` recipient's existence or location; its explicit recipient identity remains committed delivery evidence, and recipient state is not needed for third-party co-location.
* Emit feedback only when an event is `ActorSpokeEvent`, the observer differs from both `speaker_id` and `recipient_id`, and the resolved speaker's exact current canonical location equals the observer's exact current canonical location.
* The speaker and addressed recipient never match this projection even if co-located. Existing self-action and addressed-speech feedback remain their distinct paths.
* Exact-current-time speaker and observer state establishes immediate co-location. Do not reconstruct historical locations, add an event-location field, inspect visual perception, or call `project_current_perception`.
* For every match, create one `EventObserved` with `observation_type="event"`, `source_type="canonical_event"`, exact requested observer, current canonical observation time, and the exact input event object.
* Preserve matching input order and duplicates. Empty input and no matches return the immutable empty tuple. Do not deduplicate against self-action, addressed-speech, Take-witness, or any other feedback source.
* Candidate-event window selection, already-delivered tracking, composition, and cross-source ordering belong to a later caller or coordinator. This projection's exact-current-time validation makes a stale or future candidate-window defect explicit.
* The operation is stateless and deterministic and must not mutate or replace the world or event tuple, generate identities, record observations, create memory or belief, persist data, narrate, invoke an actor policy or LLM, establish comprehension, or trigger a reaction.
* Keep current-state, self-action, addressed-speech, and Take-witness projection behavior, validation precedence, error contracts, ownership or participant semantics, order, duplicates, and exact event-object retention unchanged.
* Internal helper refactoring is allowed only when it preserves all existing public behavior and error precedence. `FutureEventFeedbackError`, `WitnessEventTimeMismatchError`, and `PerceptionObserverNotFoundError` remain unchanged.
* Do not add a generic witness or audibility engine, visibility service, perception-fragment model, composition API, cursor, delivery record, reaction hook, protocol, registry, event schema field, or new dependency.
* This public perception milestone advances the project version from `0.30.0` to `0.31.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact immediate speech-overhearing projection and missing-speaker error and expose both from `llm_system.simulation`.
* Add high-signal behavioral tests for co-located third-party matches; speaker, recipient, remote observer, and non-speech exclusion; observer-first validation; first whole-batch past/future mismatch; first whole-batch missing-speaker failure; validation before observer-specific filtering; exact event retention; order and duplicate preservation; empty/no-match behavior; determinism; input immutability; and unchanged existing feedback behavior.
* Update README with the implemented API, exact-current-time contract, speaker integrity rule, third-party co-location rule, and exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Speak resolution or dispatch changes, outcome or canonical-event contract changes, event-location fields, current-state perception changes, self-action ownership changes, addressed-speech recipient changes, Take-witness changes, or new observation variants.
* Historical overhearing reconstruction, past-event acceptance, hearing range, barriers, volume, language comprehension, sensory traits, within-location geometry, concealment, attention, recipient revalidation, or richer audibility rules.
* Perception-snapshot or feedback-fragment composition, cross-source ordering, deduplication, event-window queries, cursors, delivery tracking, observation recording, persistence, SQLite, memory, belief, sensemaking, reaction generation, policies, prompts, LLM calls, narration, UI, or API behavior.
* Logging, metrics, services, protocols, registries, repositories, ID providers, generic filtering frameworks, or new dependencies.
* Changes to requirements, decisions, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-032 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/perception_engine.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_speech_overhearing_feedback.py`; existing feedback tests may change only when necessary to verify preserved shared behavior.

The two new public names are exactly `project_speech_overhearing_feedback` and `SpeechSpeakerNotFoundError`. Existing `project_current_perception`, `project_self_event_feedback`, `project_addressed_speech_feedback`, `project_take_witness_feedback`, `PerceptionObserverNotFoundError`, `FutureEventFeedbackError`, `WitnessEventTimeMismatchError`, `ActorSpokeEvent`, `EventObserved`, and Speak resolver behavior remain unchanged.

## Acceptance criteria

1. A current-time `ActorSpokeEvent` produces exact feedback for an observer who is neither speaker nor recipient and shares the speaker's current canonical location (`PERCEPTION-055`, `PERCEPTION-059`, `PERCEPTION-060`).
2. The speaker, addressed recipient, remote observer, and non-speech events produce no speech-overhearing feedback (`PERCEPTION-059`).
3. An absent observer raises `PerceptionObserverNotFoundError` before any candidate-time or speaker error (`PERCEPTION-056`).
4. The first past or future candidate event raises unchanged `WitnessEventTimeMismatchError` before event-type, speaker, or observer-specific filtering (`PERCEPTION-057`).
5. After time validation, the first `ActorSpokeEvent` with an absent speaker raises exact `SpeechSpeakerNotFoundError` before any observer-specific filtering, while non-speech events require no speaker validation (`PERCEPTION-058`).
6. Recipient existence and location are not revalidated; exact-current-time speaker and observer locations alone determine third-party co-location (`PERCEPTION-062`).
7. Matching order, duplicates, exact event identity, immutable empty results, deterministic repetition, and input immutability are preserved (`PERCEPTION-060`, `PERCEPTION-061`, `PERCEPTION-064`).
8. Existing current-state, self-action, addressed-speech, Take-witness, and Speak resolver contracts remain unchanged.
9. README documents the implemented boundary without claiming comprehension, reaction, historical reconstruction, richer audibility, composition, or persistence.
10. The package and lockfile report version `0.31.0`.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv sync --locked`
* `uv run pytest tests/test_speech_overhearing_feedback.py tests/test_addressed_speech_feedback.py tests/test_self_event_feedback.py tests/test_take_witness_feedback.py tests/test_speak_resolver.py tests/test_package.py -q`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Verify installed metadata reports `0.31.0`.
* Verify `uv.lock` changes only the editable root-package version unless a concrete existing inconsistency is documented.
* `git diff --check`

Record every command and exact result in the handoff report. If a command cannot run, record the concrete reason rather than substituting silently.

## Stop conditions

Stop and report a design gap if implementation requires historical location reconstruction, a canonical event-location field, recipient revalidation, a general witness or audibility abstraction, composition or delivery state, richer hearing semantics, a new dependency, or any public behavior not fixed above.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented the exact-current-time third-party speech-overhearing
projection, missing-speaker integrity error, public exports, focused behavioral
coverage, documentation, and `0.31.0` package metadata.

**Changed files:** `src/llm_system/simulation/perception_engine.py`,
`src/llm_system/simulation/__init__.py`,
`tests/test_speech_overhearing_feedback.py`, `tests/test_package.py`, `README.md`,
`pyproject.toml`, `uv.lock`, and
`doc/tasks/TASK-032-speech-overhearing-feedback.md`.

**Verification:**

* TDD red: `uv run pytest tests/test_speech_overhearing_feedback.py -q` exited
  2 during collection with the expected missing public
  `SpeechSpeakerNotFoundError` import.
* TDD green: `uv run pytest tests/test_speech_overhearing_feedback.py -q`
  passed: `9 passed in 0.10s`.
* `uv sync --locked` passed; rebuilt and replaced editable `llm-system==0.30.0`
  with `llm-system==0.31.0`.
* `uv run pytest tests/test_speech_overhearing_feedback.py tests/test_addressed_speech_feedback.py tests/test_self_event_feedback.py tests/test_take_witness_feedback.py tests/test_speak_resolver.py tests/test_package.py -q`
  passed: `33 passed in 0.13s`.
* `make format` passed: `64 files left unchanged`.
* `make lint` passed: `All checks passed!`.
* `make mypy` passed: `Success: no issues found in 64 source files`.
* `make test` passed: `286 passed in 0.30s`.
* `make check` passed: 64 files formatted, Ruff clean, mypy clean, and
  `286 passed in 0.29s`.
* `uv lock --check` passed: `Resolved 19 packages in 0.50ms`.
* `uv run python -c 'import importlib.metadata; print(importlib.metadata.version("llm-system"))'`
  passed and printed `0.31.0`.
* `git diff -- uv.lock` passed inspection: only the editable root-package
  version changed from `0.30.0` to `0.31.0`.
* `git diff --check` passed with no output.
* Independent integration review repeated `uv sync --locked`, the required
  focused suite (`33 passed`), `make format`, `make lint`, `make mypy`,
  `make test` (`286 passed`), `make check` (`286 passed` plus all quality
  gates), `uv lock --check`, installed-version inspection (`0.31.0`), lockfile
  diff inspection, and `git diff --check`; all passed.

**Deviations:** None.

**Design gaps or follow-ups:** None found within the accepted task boundary.
