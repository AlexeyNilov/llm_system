# TASK-018: Resolve authorized Wait actions

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-014, TASK-015, TASK-016, TASK-017

## Objective

Provide the first pure deterministic operation resolver: transform an authorized Wait action into one exact successful outcome containing its simulation-time delta and canonical waited event.

The resolver produces evidence only. It does not commit state or process activities made eligible by elapsed time.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Action proposal”, “Event”, “Outcome”, “Simulation time”, and “Validated world state” where present
* `doc/requirements.md`: `TIME-001` through `TIME-006`, `ACTION-019`, `ACTION-020`, `EVENT-012`, and `WAIT-001` through `WAIT-007`
* `doc/decisions.md`: “Use discrete, action-driven simulation time”, “Use namespace-aware operation references and connection-based movement”, “Inject UUID runtime identities and type submission sources”, “Timestamp outcomes and events at atomic completion”, and “Implement Wait as the first deterministic operation resolver”
* `doc/high_level_design.md`: “Principal records”, “Actor cognition and action loop”, and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/commitment.py`, `src/llm_system/simulation/__init__.py`, `tests/test_actor_action_authorization.py`, `tests/test_outcome_commitment.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `resolve_wait(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> SucceededOutcome`.
* `outcome_id` and `event_id` are required keyword-only standard-library UUID values supplied by the caller. The resolver generates no IDs and has no ID-source dependency.
* The authorized action's exact `world`, `submission`, and `WaitActionProposal` are read-only inputs and remain unchanged.
* If `action.submission.proposal` is not `WaitActionProposal`, raise `TypeError` with a non-blank message before constructing any outcome. Do not return rejection or failure.
* Current time is exactly `action.world.state.simulation_time_seconds`.
* Completion time is current time plus `proposal.duration_seconds`; Python integer arithmetic is canonical and no artificial maximum duration is added.
* Return exactly one `SucceededOutcome` with status `succeeded`, caller `outcome_id`, submission `proposal_id`, reason code `wait-completed`, calculated completion time, one state-change tuple item, and one event tuple item.
* The one change is `SimulationTimeChanged(change_type="simulation_time", from_seconds=current_time, to_seconds=completion_time)`.
* The one event is `ActorWaitedEvent(event_type="actor_waited", event_id=event_id, outcome_id=outcome_id, occurred_at_seconds=completion_time, actor_id=submission.actor_id, duration_seconds=proposal.duration_seconds)`.
* Outcome, change, and event construction must flow through existing public typed contracts; do not construct dictionaries and best-effort parse them.
* Wait has no failure branch, target lookup, package mechanic, random check, policy decision, perception effect, or additional event at this layer.
* The resolver does not call `commit_outcome`, `validate_world_state`, authorization, a scheduler, an NPC policy, an LLM, persistence, or presentation.
* No generic resolver protocol, registry, dispatcher, ID provider, clock object, or service class is introduced.
* No new dependency is required.
* This first resolver milestone advances the project version from `0.16.0` to `0.17.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact pure Wait resolver and expose it from `llm_system.simulation`.
* Add behavioral tests for exact successful outcome shape, current/completion time, ID and proposal causation, actor and duration event payload, input immutability, deterministic repeated calls, large integer duration, non-Wait programmer error, and successful composition with `commit_outcome`.
* Update README with the resolver contract, exact output, injected IDs, composition boundary, and scheduler exclusion.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Dispatch, generic resolver interfaces, resolver registration, unsupported-operation outcomes, or another operation resolver.
* Authorization logic, state commitment implementation, world-state validation changes, ID generation, clocks, random sources, or package rule configuration.
* Scheduler eligibility or activity resolution, NPC invocation, perception, persistence, API/UI, narration, or System notifications.
* Wait limits, interruption, cancellation, checks, costs beyond time, additional events, failure/rejection semantics, or Greybridge-specific behavior.
* Changes to existing public contract behavior beyond additive Wait resolver export.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production belongs in `src/llm_system/simulation/resolvers/wait.py`, with a minimal `resolvers/__init__.py` only if needed and public re-export from `src/llm_system/simulation/__init__.py`. Focused tests likely belong in `tests/test_wait_resolver.py`.

The one new public name is exactly `resolve_wait`.

## Acceptance criteria

1. An authorized Wait returns the exact successful outcome, one time delta, and one waited event with all accepted identities, actor, duration, and completion values (`WAIT-002` through `WAIT-005`).
2. Resolution uses current canonical time plus exact requested duration, including large integers, without wall-clock access or hidden limits (`TIME-001`, `TIME-004`, `WAIT-003`).
3. Caller identities are required and preserved; repeated calls with identical inputs and IDs produce equal outcomes and do not mutate inputs (`ACTION-020`, `WAIT-002`, `WAIT-005`).
4. Passing any authorized non-Wait proposal raises `TypeError` and produces no canonical outcome (`WAIT-006`).
5. The returned outcome commits successfully through existing `commit_outcome`, advancing only simulation time and preserving the outcome's waited event (`WAIT-007`).
6. No dispatch, scheduling, package mechanics, randomness, LLM, persistence, or presentation behavior is introduced (`WAIT-001`, `WAIT-007`).
7. Public export and README accurately describe the resolver and composition boundaries.
8. Existing simulation and package behavior remains unchanged.
9. Project and installed metadata plus editable root `uv.lock` report `0.17.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production resolver logic; record the import or missing-contract failure.
* Run focused Wait resolver tests after success, error, and composition groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.16.0` to `0.17.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires another operation, failure semantics, duration limits, ID generation, scheduler behavior, package mechanics, a generic dispatcher, a dependency, or existing contract changes.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented the pure deterministic Wait resolver, public export,
behavioral coverage, README contract, and `0.17.0` version milestone.

**Changed files:** `README.md`, `doc/tasks/TASK-018-wait-resolver.md`,
`pyproject.toml`, `src/llm_system/simulation/__init__.py`,
`src/llm_system/simulation/resolvers/__init__.py`,
`src/llm_system/simulation/resolvers/wait.py`, `tests/test_package.py`,
`tests/test_wait_resolver.py`, and `uv.lock`.

**Verification:** Initial `uv run pytest tests/test_wait_resolver.py` failed
during collection with `ImportError: cannot import name 'resolve_wait' from
'llm_system.simulation'`. Focused success/determinism, error, and commitment
groups then passed (2, 1, and 1 tests). `uv sync --locked`, `make format`,
`make lint`, `make mypy`, `make test` (152 passed), `make check` (152 passed),
`uv lock --check`, and `git diff --check` passed. The only `uv.lock` diff is
the editable root package version from `0.16.0` to `0.17.0`.

**Deviations:** None.

**Design gaps or follow-ups:** None.

## Integrator review

**Disposition:** Accepted.

The integrator independently reviewed exact Wait outcome construction, injected
UUID causation, proposal and actor identity, time arithmetic, input immutability,
large-duration behavior, wrong-dispatch `TypeError`, public export,
documentation, and composition through `commit_outcome`. No correctness defect
was found. Twenty-one focused and adjacent tests passed, followed by `uv sync
--locked`, `make format`, `make lint`, `make mypy`, `make test`, `make check`,
`uv lock --check`, and `git diff --check`; the full suite contains 152 passing
tests. The only `uv.lock` change is the editable root-package version from
`0.16.0` to `0.17.0`.
