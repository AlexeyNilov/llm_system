# TASK-019: Resolve authorized Move actions

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-013, TASK-014, TASK-015, TASK-016, TASK-017, TASK-018

## Objective

Provide the second pure deterministic operation resolver: transform an authorized Move action into either one effect-free rejection or one exact successful movement outcome derived from authored connection topology and canonical runtime state.

The resolver produces evidence only. It does not commit state, dispatch operations, or process activities made eligible by elapsed time.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Connection”, “Connection definition”, “Event”, “Location”, “Outcome”, “Simulation time”, and “Validated world state” where present
* `doc/requirements.md`: `TIME-001` through `TIME-006`, `ACTION-016`, `ACTION-020`, `ACTION-030`, `ACTION-031`, `ARBITER-001` through `ARBITER-004`, `EVENT-010`, and `MOVE-001` through `MOVE-010`
* `doc/decisions.md`: “Use discrete, action-driven simulation time”, “Use namespace-aware operation references and connection-based movement”, “Inject UUID runtime identities and type submission sources”, “Timestamp outcomes and events at atomic completion”, “Separate arbiter commitment from operation resolution”, and “Resolve basic movement before introducing generic dispatch”
* `doc/high_level_design.md`: “Principal records”, “Actor cognition and action loop”, and “Testing strategy”
* `src/llm_system/game_packages/spatial.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/commitment.py`, `src/llm_system/simulation/resolvers/wait.py`, `src/llm_system/simulation/__init__.py`, `tests/test_wait_resolver.py`, `tests/test_outcome_commitment.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `resolve_move(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome`.
* `outcome_id` and `event_id` are required keyword-only standard-library UUID values supplied by the caller. The resolver generates no IDs and has no ID-source dependency. A rejected Move leaves `event_id` unused.
* The authorized action's exact `world`, `submission`, and `MoveActionProposal` are read-only inputs and remain unchanged.
* If `action.submission.proposal` is not `MoveActionProposal`, raise `TypeError` with a non-blank message before constructing any outcome. Do not return rejection or failure.
* Resolve the proposal's connection against `action.world.packages.scenario_package.definition.spatial_graph.connections`; runtime availability comes from the matching item in `action.world.state.connections`, and actor location comes from the matching item in `action.world.state.characters`.
* `ValidatedWorldState` already guarantees complete, unique, relationally valid character and connection overlays. Do not revalidate the world or add defensive outcomes for invariant-impossible missing runtime records.
* Actionability checks are gated in this exact order: unknown authored connection, actor current location unequal to the connection source, then unavailable runtime connection.
* Rejection reasons are exactly `unknown-connection`, `actor-not-at-connection-source`, and `connection-unavailable`. Every rejection uses the input current simulation time and contains no effect fields by construction.
* Valid movement always succeeds. Completion time is current time plus the connection's exact `base_traversal_seconds`; Python integer arithmetic is canonical and no artificial maximum is added.
* Success returns reason `move-completed` with exactly two ordered changes: `CharacterLocationChanged` followed by `SimulationTimeChanged`.
* The location change identifies the submission actor, connection source as `from_location_id`, and connection destination as `to_location_id`. The time change runs from current time to completion time.
* Success contains exactly one `ActorMovedEvent` using the supplied event identity and outcome causation at completion, identifying the submission actor, connection, source, and destination.
* Outcome, change, and event construction must flow through existing public typed contracts; do not construct dictionaries and best-effort parse them.
* Basic movement has no failed-attempt branch, rule lookup beyond authored connection topology, random check, skill, terrain, encumbrance, interruption, traversal requirement, perception effect, or additional event at this layer.
* The resolver does not call `commit_outcome`, `validate_world_state`, authorization, dispatch, a scheduler, an NPC policy, an LLM, persistence, or presentation.
* No generic resolver protocol, registry, dispatcher, ID provider, clock object, service class, or new dependency is introduced.
* This resolver milestone advances the project version from `0.17.0` to `0.18.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact pure Move resolver and expose it from `llm_system.simulation`.
* Add high-signal behavioral tests for exact success, each rejection reason, gated rejection precedence, exact duration and ordered effects, identity and causation preservation, input immutability, deterministic repeated calls, large integer time, non-Move programmer error, and composition of successful and rejected outcomes with `commit_outcome`.
* Update README with the resolver contract, actionability order, success/rejection effects, injected IDs, exact movement-duration boundary, and commitment/scheduler exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Generic dispatch, resolver protocols, resolver registration, ID generation, or another operation resolver.
* Failed movement, movement costs beyond time, partial movement, interruption, cancellation, random checks, skills, terrain, encumbrance, traversal requirements, or package-configurable movement modifiers.
* Changes to authored or runtime spatial schemas, authorization, outcome commitment, world validation, action/event/change contracts, or reason-code formatting.
* Scheduler eligibility or activity resolution, NPC invocation, perception, persistence, API/UI, narration, or System notifications.
* Greybridge-specific special cases or content changes.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/resolvers/move.py`, with public re-exports from `src/llm_system/simulation/resolvers/__init__.py` and `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_move_resolver.py`.

The one new public name is exactly `resolve_move`.

## Acceptance criteria

1. A valid authorized Move returns the exact successful outcome, ordered location and time deltas, and one moved event with all accepted identities, connection, endpoints, and completion values (`MOVE-002`, `MOVE-006` through `MOVE-008`).
2. Resolution uses current canonical time plus the exact authored base traversal duration, including large integers, without modifiers, wall-clock access, or hidden limits (`TIME-001`, `MOVE-001`, `MOVE-006`).
3. Unknown connection, wrong source, and unavailable connection return exact effect-free rejection variants at current simulation time; their precedence is deterministic when conditions overlap (`MOVE-003` through `MOVE-005`).
4. Caller identities are required and preserved; repeated calls with identical inputs and IDs produce equal outcomes and do not mutate inputs (`ACTION-020`, `MOVE-002`, `MOVE-005`, `MOVE-008`).
5. Passing any authorized non-Move proposal raises `TypeError` and produces no canonical outcome (`MOVE-009`).
6. Successful and rejected outcomes both compose correctly with existing `commit_outcome`: success advances only actor location and simulation time, while rejection returns the exact input world (`MOVE-005` through `MOVE-008`, `ARBITER-007`, `ARBITER-008`).
7. No dispatch, scheduling, movement-modifier mechanics, randomness, LLM, persistence, perception, or presentation behavior is introduced (`MOVE-001`, `MOVE-010`).
8. Public exports and README accurately describe the resolver and composition boundaries.
9. Existing simulation and package behavior remains unchanged.
10. Project and installed metadata plus editable root `uv.lock` report `0.18.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production resolver logic; record the import or missing-contract failure.
* Run focused Move resolver tests after success, rejection, error, and commitment-composition groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.17.0` to `0.18.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires a failed-attempt branch, a different actionability order, conditional duration, movement requirements or modifiers, ID generation, dispatch, scheduler behavior, another operation, a dependency, schema changes, or existing contract changes.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
