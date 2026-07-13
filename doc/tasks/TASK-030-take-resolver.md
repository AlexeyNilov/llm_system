# TASK-030: Resolve co-located object acquisition

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-013 through TASK-020

## Objective

Make the accepted Take v0 action executable through a pure deterministic resolver and the actor-action dispatcher. Taking succeeds only when canonical runtime state places the object directly at the authorized actor's exact current location, then transfers that object to actor possession with exact state-change and event evidence.

This task resolves canonical acquisition only. Transfer from another character, theft, permission, witness feedback, and reactions remain separate mechanics.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Event”, “Object accessibility”, “Object placement”, “Operation dispatch”, “Outcome”, “Simulation arbiter”, “Simulation time”, and “Validated world state”
* `doc/requirements.md`: `STATE-001` through `STATE-020`, `ACTION-006` through `ACTION-010`, `ACTION-024` through `ACTION-042`, `TAKE-001` through `TAKE-012`, `DISPATCH-001` through `DISPATCH-010`, and `EVENT-001` through `EVENT-011`
* `doc/decisions.md`: “Model runtime state as an ID-linked mutable-facts overlay”, “Distinguish rejected, failed, and succeeded outcomes”, “Retain typed canonical events without full event sourcing”, “Separate arbiter commitment from operation resolution”, “Introduce partial type-based actor-action dispatch”, and “Resolve Take v0 as direct co-located acquisition”
* `doc/high_level_design.md`: “Simulation arbiter”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/commitment.py`, `src/llm_system/simulation/dispatch.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/resolvers/speak.py`, `src/llm_system/simulation/resolvers/__init__.py`, `src/llm_system/simulation/__init__.py`, `tests/test_actor_action_dispatch.py`, `tests/test_speak_resolver.py`, `tests/test_outcome_commitment.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, unrelated requirements or decisions, experiments, perception-engine implementation, persistence, scheduling, randomness, other operation resolver task briefs, or other completed task briefs.

## Fixed assumptions

* Add public `resolve_take(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` in a focused resolver module.
* Passing an authorized action whose proposal is not `TakeActionProposal` raises `TypeError` with stable non-blank text and produces no outcome.
* Authorization plus validated-world completeness guarantees one runtime character state for the authorized actor. A missing actor state is an upstream invariant defect; do not convert it into an in-world rejection.
* Determine accessibility from canonical runtime character and object state, not authored initial placement or `project_current_perception`.
* The object is accessible only when its identifier resolves in runtime object state and its exact placement is `ObjectAtLocation` whose location equals the actor's current location.
* Unknown, remote, possessed-by-self, possessed-by-another-character, location-namespace, connection-namespace, character-namespace, and otherwise absent or inaccessible object identifiers all return the same `RejectedOutcome` reason `object-not-accessible`. Do not query other namespaces or reveal which condition applied.
* Rejection uses exact current simulation time, originating proposal identity, and supplied outcome identity. It has no effect fields, consumes no time, produces no event, and leaves `event_id` unused.
* Success uses reason `object-taken`, resolves at exact current simulation time, does not advance time, and contains exactly one `ObjectPlacementChanged`. Its `from_placement` is the exact current `ObjectAtLocation` value and its `to_placement` is `ObjectPossessedByCharacter(placement_type="possessed_by_character", character_id=actor_id)`.
* Success contains exactly one `ObjectTakenEvent` using supplied event and outcome identities, current time, authorized actor ID, proposal object ID, and the same exact previous placement used by the state change.
* Take v0 never returns `FailedOutcome`. Do not add duration, capacity, weight, permission, consent, transfer, theft, competition, interruption, object-specific rules, costs, randomness, or checks.
* `dispatch_actor_action` routes `TakeActionProposal` directly to `resolve_take` with the exact action and supplied identities. Use and Help remain unavailable through `OperationResolverUnavailableError`.
* Do not commit inside the resolver, use perception as mutation authority, add witness feedback, alter self-action feedback, invoke an actor policy or LLM, generate a reaction, or perform presentation. Existing commitment and self-event-feedback boundaries consume the emitted contracts separately.
* Repeated resolution for equal inputs and caller identities returns equal outcomes and preserves the exact immutable authorized action, world, submission, proposal, object state, and placement.
* Do not add accessibility services, inventory aggregates, ownership protocols, generic possession mechanics, resolver registries, logging, or configuration.
* No new dependency is required.
* This public resolver milestone advances the project version from `0.28.0` to `0.29.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact Take v0 resolver and expose it from `llm_system.simulation`.
* Route Take through the existing actor-action dispatcher and retain capability errors for Use and Help.
* Add high-signal behavioral tests for accessible success; exact placement change and event evidence; unknown, remote, possessed-by-self, possessed-by-another, and wrong-namespace uniform rejection; zero-time behavior; wrong-operation failure; dispatch pass-through; commitment compatibility; determinism; and input immutability.
* Update README with implemented Take usage, behavior, and explicit exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Perception projection or filtering, witness event feedback, visibility, delivery tracking, NPC reactions, stealing, conflict, consent, permission, transfer, giving, dropping, trading, ownership, encumbrance, weight, capacity, quantities, stacks, containers, destruction, or consumption.
* Duration, time advancement, failure, interruption, skills, difficulty, randomness, checks, costs, object-archetype mechanics, rule-pack lookup, or scenario-specific exceptions.
* NPC policy execution, turn coordination, memory, belief, goals, plans, intent, narration, prompts, LLM calls, or UI behavior.
* Changes to proposal, authorization, state, state-change, outcome, event, perception, commitment, scheduling, randomness, or package contracts.
* Persistence, SQLite, API, logging, metrics, generic resolver protocols, registries, service classes, ID providers, or new dependencies.
* Changes to requirements, decisions, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-030 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/resolvers/take.py`, with routing in `src/llm_system/simulation/dispatch.py` and public re-exports from `src/llm_system/simulation/resolvers/__init__.py` and `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_take_resolver.py`, with dispatch coverage updated in `tests/test_actor_action_dispatch.py`.

The one new public name is exactly `resolve_take`. Existing `TakeActionProposal`, `ObjectAtLocation`, `ObjectPossessedByCharacter`, `ObjectPlacementChanged`, `ObjectTakenEvent`, outcome and commitment contracts, dispatch API, unavailable error, runtime state, perception, and self-event-feedback behavior remain unchanged.

## Acceptance criteria

1. Taking an object directly at the authorized actor's exact canonical location succeeds at current canonical time without time advancement (`TAKE-001`, `TAKE-003`, `TAKE-006`).
2. Unknown, remote, possessed-by-self, possessed-by-another-character, and wrong-namespace objects reject uniformly as `object-not-accessible`, without canonical existence or possession disclosure (`TAKE-004`, `TAKE-005`).
3. Success contains exactly one `ObjectPlacementChanged` from the exact current location placement to authorized-actor possession and no simulation-time change (`TAKE-006`, `TAKE-007`).
4. Success contains exactly one `ObjectTakenEvent` with supplied identities, current time, authorized actor, proposal object, and the exact same previous placement; rejection leaves the event identity unused (`TAKE-005`, `TAKE-008`, `EVENT-011`).
5. The resolver uses canonical runtime state directly and does not call or treat perception as canonical mutation authority (`TAKE-001`, `TAKE-003`, `TAKE-011`).
6. Take has no failed branch, duration, random check, object-specific mechanic, transfer, theft, permission, witness feedback, reaction, persistence, or presentation behavior (`TAKE-009`, `TAKE-011`).
7. A non-Take authorized action raises `TypeError` and produces no in-world outcome (`TAKE-010`).
8. Dispatcher output for Take equals direct resolution with exact input and identity pass-through; Use and Help retain their typed unavailable-capability error (`DISPATCH-003` through `DISPATCH-009`).
9. Committing a successful Take through the existing commitment core produces a validated replacement world in which the exact object is possessed by the actor, while the resolver itself does not mutate or commit the input.
10. Repeated resolution is deterministic and preserves the immutable authorized action and validated world (`TAKE-012`).
11. Public exports and README accurately describe Take v0, canonical-state accessibility, zero-time semantics, uniform rejection, exact state-change and event evidence, dispatch availability, and excluded transfer and witness mechanics.
12. Existing package, world-validation, action, authorization, outcome, commitment, Move, Wait, Observe, Speak, perception, randomness, scheduler, and remaining dispatch behavior remains unchanged.
13. Project and installed metadata plus editable root `uv.lock` report `0.29.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing resolver and dispatch tests before production logic; record genuine red evidence.
* `uv run pytest tests/test_take_resolver.py tests/test_actor_action_dispatch.py tests/test_outcome_commitment.py tests/test_self_event_feedback.py tests/test_package.py -q`
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.28.0` to `0.29.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires perception-based mutation authority, transfer from a character, theft or consent semantics, a duration, a failed-attempt or random-check mechanic, object-specific rules, witness feedback or reaction, an existing contract change, a dependency, or generic resolver infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
