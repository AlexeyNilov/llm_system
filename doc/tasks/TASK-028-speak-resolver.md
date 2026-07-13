# TASK-028: Resolve co-located speech

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-017, TASK-020

## Objective

Make the accepted Speak v0 action executable through a pure deterministic resolver and the actor-action dispatcher. Speech succeeds only when it addresses another character at the speaker's exact canonical location and records the exact utterance without claiming a response or comprehension.

This task resolves and records canonical speech only. Recipient event feedback is an immediate separate follow-up.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Event”, “Operation dispatch”, “Outcome”, “Simulation arbiter”, “Simulation time”, “Speech audibility”, and “Validated world state”
* `doc/requirements.md`: `TIME-001` through `TIME-006`, `ACTION-006` through `ACTION-010`, `ACTION-024` through `ACTION-042`, `SPEAK-001` through `SPEAK-011`, `DISPATCH-001` through `DISPATCH-010`, and `EVENT-001` through `EVENT-009`
* `doc/decisions.md`: “Use discrete, action-driven simulation time”, “Use namespace-aware operation references and connection-based movement”, “Distinguish rejected, failed, and succeeded outcomes”, “Retain typed canonical events without full event sourcing”, “Separate arbiter commitment from operation resolution”, “Introduce partial type-based actor-action dispatch”, and “Resolve Speak v0 as co-located zero-time speech”
* `doc/high_level_design.md`: “Simulation arbiter”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/dispatch.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/resolvers/observe.py`, `src/llm_system/simulation/resolvers/__init__.py`, `src/llm_system/simulation/__init__.py`, `tests/test_actor_action_dispatch.py`, `tests/test_observe_resolver.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, perception-engine implementation, persistence, scheduling, randomness, or other task briefs.

## Fixed assumptions

* Add public `resolve_speak(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` in a focused resolver module.
* Passing an authorized action whose proposal is not `SpeakActionProposal` raises `TypeError` with stable non-blank text and produces no outcome.
* Authorization plus validated-world completeness guarantees one runtime character state for the authorized speaker. A missing speaker state is an upstream invariant defect; do not convert it into an in-world rejection.
* Determine audibility from canonical runtime character locations, not authored definitions or `project_current_perception`. The recipient is audible only when its identifier resolves in runtime character state, differs from the speaker identifier, and its location equals the speaker's location.
* Unknown, remote, self, object-namespace, connection-namespace, location-namespace, and otherwise absent recipient identifiers all return the same `RejectedOutcome` reason `recipient-not-audible`. Do not query other namespaces or reveal which condition applied.
* Rejection uses exact current simulation time, originating proposal identity, and supplied outcome identity. It has no effect fields, consumes no time, produces no event, and leaves `event_id` unused.
* Success uses reason `speech-completed`, resolves at exact current simulation time, has `state_changes=()`, and contains exactly one `ActorSpokeEvent` using supplied event and outcome identities, current time, authorized actor ID as speaker, proposal `character_id` as recipient, and proposal's exact `utterance`.
* Speak v0 never returns `FailedOutcome`, changes canonical state, or advances simulation time. Do not add or infer a duration from utterance text.
* Success establishes audible addressed speech only. Do not establish comprehension, memory, belief, agreement, obedience, response, recipient state change, or any generated fact.
* `dispatch_actor_action` routes `SpeakActionProposal` directly to `resolve_speak` with the exact action and supplied identities. Take, Use, and Help remain unavailable through `OperationResolverUnavailableError`.
* Do not add recipient or witness `EventObserved` production, alter `project_self_event_feedback`, invoke an actor policy or LLM, or generate a reply. Addressed-speech recipient feedback is a separate planned task.
* Repeated resolution for equal inputs and caller identities returns equal outcomes and preserves the exact immutable authorized action, world, submission, proposal, and utterance.
* Do not add audibility services, hearing protocols, sensory traits, language models, text normalization, moderation, duration estimation, logging, registries, or configuration.
* No new dependency is required.
* This public resolver milestone advances the project version from `0.26.0` to `0.27.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact Speak v0 resolver and expose it from `llm_system.simulation`.
* Route Speak through the existing actor-action dispatcher and retain capability errors for Take, Use, and Help.
* Add high-signal behavioral tests for audible success; exact event and utterance evidence; unknown, remote, self, and wrong-namespace uniform rejection; zero-time and no-state-change behavior; wrong-operation failure; dispatch pass-through; determinism; and input immutability.
* Update README and accepted high-level-design dispatch and resolver descriptions with implemented behavior and explicit perception, response, time, and comprehension exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Recipient or witness perception, event-feedback filtering, `EventObserved` values, observation composition, event delivery tracking, audibility outside exact co-location, pre- or post-event location reconstruction, or changes to self-action feedback.
* Responses, NPC policy execution, turn coordination, conversation history, memory, belief, understanding, agreement, goals, plans, intent, sentiment, language translation, narration, prompts, LLM calls, or UI behavior.
* Speech duration, time advancement, action failure, interruption, volume, hearing range, deafness, barriers, concealment, stealth, channels, broadcasts, groups, overhearing, randomness, checks, rules, costs, or package configuration.
* Changes to proposal, authorization, state, outcome, event, perception, commitment, scheduling, randomness, or package contracts.
* Persistence, SQLite, API, logging, metrics, generic resolver protocols, registries, service classes, ID providers, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-028 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/resolvers/speak.py`, with routing in `src/llm_system/simulation/dispatch.py` and public re-exports from `src/llm_system/simulation/resolvers/__init__.py` and `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_speak_resolver.py`, with dispatch coverage updated in `tests/test_actor_action_dispatch.py`.

The one new public name is exactly `resolve_speak`. Existing `SpeakActionProposal`, `ActorSpokeEvent`, outcome contracts, dispatch API, unavailable error, runtime state, and self-event-feedback behavior remain unchanged.

## Acceptance criteria

1. Addressing another character at the exact speaker location succeeds at current canonical time without state change or time advancement (`SPEAK-001`, `SPEAK-003`, `SPEAK-006`, `SPEAK-007`).
2. Unknown, remote, self, and wrong-namespace recipients reject uniformly as `recipient-not-audible`, without canonical existence disclosure or event production (`SPEAK-004`, `SPEAK-005`).
3. Success contains exactly one `ActorSpokeEvent` with supplied identities, authorized speaker, proposal recipient, current time, and exact unnormalized utterance; rejection leaves the event identity unused (`SPEAK-005`, `SPEAK-006`, `EVENT-009`).
4. The resolver uses canonical runtime co-location directly and neither calls nor reimplements visual perception as hearing (`SPEAK-001`, `SPEAK-003`).
5. Speak has no failed branch, duration, state change, randomness, response, comprehension, memory, belief, recipient feedback, persistence, or presentation behavior (`SPEAK-007`, `SPEAK-008`, `SPEAK-010`).
6. A non-Speak authorized action raises `TypeError` and produces no in-world outcome (`SPEAK-009`).
7. Dispatcher output for Speak equals direct resolution with exact input and identity pass-through; Take, Use, and Help retain their typed unavailable-capability error (`DISPATCH-003` through `DISPATCH-009`).
8. Repeated resolution is deterministic and preserves the immutable authorized action and validated world (`SPEAK-011`).
9. Public exports, README, and high-level design accurately describe Speak v0, co-located audibility, zero-time semantics, uniform rejection, event evidence, dispatch availability, and recipient-feedback exclusions.
10. Existing package, world-validation, action, authorization, outcome, commitment, Move, Wait, Observe, perception, randomness, scheduler, and remaining dispatch behavior remains unchanged.
11. Project and installed metadata plus editable root `uv.lock` report `0.27.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing resolver and dispatch tests before production logic; record genuine red evidence.
* `uv run pytest tests/test_speak_resolver.py tests/test_actor_action_dispatch.py tests/test_self_event_feedback.py tests/test_package.py -q`
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.26.0` to `0.27.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires recipient perception, witness hearing, event delivery, response generation, speech duration, failed-attempt semantics, audibility beyond canonical co-location, visual-perception reuse, an existing contract change, a dependency, or generic resolver infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented pure deterministic co-located Speak v0 resolution, public exports, and concrete actor-action dispatch while preserving uniform private rejection and zero-time exact-event evidence.

**Changed files:** `src/llm_system/simulation/resolvers/speak.py`, `src/llm_system/simulation/resolvers/__init__.py`, `src/llm_system/simulation/dispatch.py`, `src/llm_system/simulation/__init__.py`, `tests/test_speak_resolver.py`, `tests/test_actor_action_dispatch.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, `uv.lock`, and `doc/tasks/TASK-028-speak-resolver.md`.

**Verification:** Initial red: `uv run pytest tests/test_speak_resolver.py tests/test_actor_action_dispatch.py -q` failed during collection because `resolve_speak` was not publicly implemented or exported. Final green: required focused suite passed (22 tests); `uv sync --locked`, `make format`, `make lint`, `make mypy`, `make test` (256 tests), `make check` (256 tests), `uv lock --check`, and `git diff --check` all passed. Installed metadata reports `0.27.0`; `uv.lock` changes only the editable root version from `0.26.0` to `0.27.0`.

**Deviations:** None. The accepted high-level design already described Speak v0, its dispatch availability, and its exclusions accurately, so no additional edit was necessary there.

**Design gaps or follow-ups:** No design gap. Recipient addressed-speech event feedback remains the explicitly separate planned follow-up.
