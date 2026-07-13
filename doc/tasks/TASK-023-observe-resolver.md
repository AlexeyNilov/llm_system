# TASK-023: Resolve focused current-state observation

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-017, TASK-020, TASK-022

## Objective

Make the accepted thin Observe v0 action executable through a pure deterministic resolver and the existing actor-action dispatcher. A specific observation succeeds only when the target is already present in the authorized actor's current-state perception; all non-perceptible targets reject without leaking canonical existence.

This task establishes action and event plumbing only. It does not reveal richer facts, filter event feedback, perform a skill check, or create a durable observation record.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Actor-action operation dispatch”, “Event”, “Observation”, “Outcome”, “Perception engine”, “Perceptual filtering”, “Perception snapshot”, “Simulation arbiter”, and “Simulation time”
* `doc/requirements.md`: `TIME-001` through `TIME-006`, `ACTION-006` through `ACTION-010`, `ACTION-024` through `ACTION-042`, `OBSERVE-001` through `OBSERVE-010`, `DISPATCH-001` through `DISPATCH-010`, `EVENT-001` through `EVENT-009`, `PERCEPTION-001` through `PERCEPTION-025`, and `LOOP-001`, `LOOP-005`, `LOOP-006`
* `doc/decisions.md`: “Use discrete, action-driven simulation time”, “Separate truth, perception, memory, and belief”, “Use namespace-aware operation references and connection-based movement”, “Distinguish rejected, failed, and succeeded outcomes”, “Retain typed canonical events without full event sourcing”, “Separate arbiter commitment from operation resolution”, “Introduce partial type-based actor-action dispatch”, “Begin perception with typed deterministic observation values”, “Project current state before filtering event feedback”, and “Begin Observe as a focused current-perception action”
* `doc/high_level_design.md`: “Simulation arbiter”, “Perception engine”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/dispatch.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/perception_engine.py`, `src/llm_system/simulation/resolvers/move.py`, `src/llm_system/simulation/resolvers/wait.py`, `src/llm_system/simulation/__init__.py`, `tests/test_actor_action_dispatch.py`, `tests/test_current_state_perception.py`, `tests/test_move_resolver.py`, `tests/test_wait_resolver.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, experiments, or other task briefs.

## Fixed assumptions

* The public operation is `resolve_observe(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome`.
* Passing an authorized action whose proposal is not `ObserveActionProposal` raises `TypeError` with stable non-blank text and produces no outcome.
* Use `action.submission.actor_id` as the observer and call `project_current_perception(action.world, actor_id)`. Do not duplicate current location, connection direction, character co-location, object placement, possession, visibility, or ordering logic in the resolver.
* Authorization plus validated-world completeness guarantees that the actor has runtime character state. Do not catch or translate `PerceptionObserverNotFoundError`; its occurrence is an upstream invariant defect.
* A `SurroundingsTarget` is always perceptible after successful current-state projection.
* A `LocationTarget`, `ConnectionTarget`, `CharacterTarget`, or `ObjectTarget` is perceptible only when the snapshot contains the corresponding `LocationObserved`, `ConnectionObserved`, `CharacterObserved`, or `ObjectObserved` with the same typed identifier.
* Target matching ignores other observation payload fields. In particular, an unavailable outgoing connection remains perceptible because `ConnectionObserved` exists for it.
* Unknown, remote, incoming-only, self-character, wrong-namespace, and otherwise absent specific targets all return the same `RejectedOutcome` reason `target-not-perceptible`. Do not query canonical definitions to distinguish those cases.
* A rejection uses the world's exact current simulation time, originating proposal identity, and supplied outcome identity. It has no effect fields, consumes no time, produces no event, and leaves `event_id` unused.
* Success uses reason `observation-completed`, resolves at the exact current simulation time, has `state_changes=()`, and contains exactly one `ActorObservedEvent` using the supplied event and outcome identities, current time, actor ID, and proposal's exact typed target.
* Observe v0 never returns `FailedOutcome`, changes state, or advances simulation time.
* `dispatch_actor_action` routes `ObserveActionProposal` directly to `resolve_observe` with the exact action and supplied identities. Speak, Take, Use, and Help remain unavailable through `OperationResolverUnavailableError`.
* Repeated resolution for equal inputs and caller identities returns equal outcomes and preserves the exact immutable authorized action and world.
* Do not add rich perceptible facts, target descriptions, inspection results, event feedback, definition enrichment, capability or Fieldcraft checks, search mechanics, uncertainty, durations, randomness, recording, memory, beliefs, persistence, narration, configuration, protocols, registries, or service classes.
* No new dependency is required.
* This public resolver milestone advances the project version from `0.21.0` to `0.22.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact Observe v0 resolver and expose it from `llm_system.simulation`.
* Route Observe through the existing actor-action dispatcher and retain capability errors for Speak, Take, Use, and Help.
* Add high-signal behavioral tests covering successful surroundings and every specific target kind, the conservative current-perception boundary, uniform non-leaking rejection, exact success event evidence, zero-time and no-state-change behavior, wrong-operation failure, determinism, and input immutability.
* Update README and the accepted high-level-design dispatch and resolver descriptions to reflect the implemented Observe boundary and explicit rich-inspection exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Adding or changing action, authorization, outcome, state-change, event, observation, perception-snapshot, current-state projection, commitment, or unavailable-error contracts.
* Canonical-event feedback filtering, `EventObserved` production, pre-outcome state, event visibility, or outcome-to-observation processing.
* New package definitions for perceptible features, environmental facts, bridge damage, object affordances, rules, checks, skills, Fieldcraft, progression, or scenario content.
* Observation enrichment, generated descriptions, narrator or NPC context assembly, prompts, LLM calls, UI, API, persistence, SQLite, memory, belief, retrieval, or scheduling.
* Time cost, failed attempts, randomness, sensory traits, concealment, attention, within-location geometry, configurable reason codes, generic resolver protocols, registries, service classes, caches, ID providers, logging, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-023 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/resolvers/observe.py`, with routing in `src/llm_system/simulation/dispatch.py` and public re-export from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_observe_resolver.py`, with dispatch coverage updated in `tests/test_actor_action_dispatch.py`.

The new public name is exactly `resolve_observe`. Existing `project_current_perception`, `dispatch_actor_action`, `ActorObservedEvent`, observation contracts, and reason-code model remain unchanged.

## Acceptance criteria

1. Surroundings and each specific target represented by the corresponding current-state observation succeed at current canonical time without state change or time advancement (`OBSERVE-003`, `OBSERVE-004`, `OBSERVE-007`, `OBSERVE-008`).
2. Unknown, remote, incoming-only, self-character, other-possessed-object, and wrong-namespace targets reject uniformly as `target-not-perceptible`, without canonical existence disclosure or event production (`OBSERVE-005`, `OBSERVE-006`).
3. Success contains exactly one `ActorObservedEvent` with the supplied identities, authorized actor, current time, and proposal's exact target; rejection leaves the event identity unused (`OBSERVE-006`, `OBSERVE-007`, `EVENT-009`).
4. Resolution reuses `project_current_perception` as its sole current-state perceptibility authority and does not duplicate spatial or visibility rules (`OBSERVE-003`, `OBSERVE-004`, `OBSERVE-010`, `PERCEPTION-015` through `PERCEPTION-025`).
5. Observe has no failed branch, rich inspection result, randomness, duration, enrichment, recording, persistence, or presentation behavior (`OBSERVE-001`, `OBSERVE-008`, `OBSERVE-010`).
6. A non-Observe authorized action raises `TypeError` and produces no in-world outcome (`OBSERVE-009`).
7. Dispatcher output for Observe equals direct resolution with exact input and identity pass-through; Speak, Take, Use, and Help retain their typed unavailable-capability error (`DISPATCH-003` through `DISPATCH-009`).
8. Repeated resolution is deterministic and preserves the immutable authorized action and validated world.
9. Public exports, README, and high-level design accurately describe Observe v0, zero-time semantics, perception reuse, non-leaking rejection, dispatch availability, and richer-inspection boundary.
10. Existing package, world-validation, action, authorization, outcome, commitment, Move, Wait, perception, and remaining dispatch behavior remains unchanged.
11. Project and installed metadata plus editable root `uv.lock` report `0.22.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing resolver and dispatch tests before production logic; record the import, unavailable-dispatch, or missing-contract failure.
* Run focused Observe resolver tests after success/evidence, rejection/information-boundary, and determinism/error groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.21.0` to `0.22.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires revealing a fact not already represented by current-state observation membership, distinguishing unknown from hidden targets, changing current perception, adding time or failure semantics, introducing checks or randomness, filtering event feedback, enriching or recording observations, changing existing contracts, adding a dependency, or inventing generic resolver infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
