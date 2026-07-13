# TASK-020: Dispatch authorized actor actions

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-017, TASK-018, TASK-019

## Objective

Provide one pure actor-action operation-dispatch boundary that routes authorized Move and Wait proposals to their accepted deterministic resolvers and reports every other initial actor operation as unavailable software capability.

Dispatch coordinates selection only. It does not authorize, resolve mechanics itself, commit outcomes, or convert missing implementation into simulated reality.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Action proposal”, “Operation dispatch”, “Outcome”, and “Simulation arbiter” where present
* `doc/requirements.md`: `ARBITER-001` through `ARBITER-004`, `AUTHZ-001`, `AUTHZ-002`, `AUTHZ-008`, `WAIT-002`, `WAIT-006`, `MOVE-002`, `MOVE-009`, and `DISPATCH-001` through `DISPATCH-010`
* `doc/decisions.md`: “Use closed operation-specific action proposal contracts”, “Separate arbiter commitment from operation resolution”, “Implement Wait as the first deterministic operation resolver”, “Resolve basic movement before introducing generic dispatch”, and “Introduce partial type-based actor-action dispatch”
* `doc/high_level_design.md`: “Simulation arbiter”, “Principal records”, and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/resolvers/move.py`, `src/llm_system/simulation/resolvers/wait.py`, `src/llm_system/simulation/resolvers/__init__.py`, `src/llm_system/simulation/__init__.py`, `tests/test_move_resolver.py`, `tests/test_wait_resolver.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `dispatch_actor_action(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> Outcome`.
* `outcome_id` and `event_id` are required keyword-only standard-library UUID values supplied by the caller. Dispatch generates no identities and introduces no ID-source dependency.
* Dispatch consumes an already authorized action. It does not accept `ActorActionSubmission` or call `authorize_actor_action`.
* Select by concrete proposal class using the existing closed actor-action proposal variants. Do not route by package content, a string-to-callable mapping, generated output, or configurable registration.
* A `MoveActionProposal` routes to `resolve_move(action, outcome_id=outcome_id, event_id=event_id)`.
* A `WaitActionProposal` routes to `resolve_wait(action, outcome_id=outcome_id, event_id=event_id)`.
* Return the selected resolver's outcome directly. Do not intentionally copy, reconstruct, validate, commit, narrate, or otherwise transform it.
* Do not catch or translate exceptions from an implemented resolver. Incorrect direct resolver inputs remain their existing programmer errors, while operation-specific actionability stays owned by that resolver.
* `ObserveActionProposal`, `SpeakActionProposal`, `TakeActionProposal`, `UseActionProposal`, and `HelpActionProposal` each raise `OperationResolverUnavailableError` before any outcome is produced.
* `OperationResolverUnavailableError` is a public `RuntimeError` subclass. Its constructor accepts the unavailable `ActorActionOperation`, stores it as public typed attribute `operation`, and supplies the exact message `no resolver is available for actor operation: {operation}`.
* The unavailable-resolver exception is one application capability signal, not an issue aggregate, canonical rejection, valid failed attempt, or repairable generated-output error.
* No generic resolver protocol, registry, mapping, decorator, plugin hook, ID provider, event-ID sequence, clock, service class, or dependency is introduced.
* Dispatch does not call `commit_outcome`, process scheduler eligibility, invoke an NPC policy or LLM, perform perception or presentation, access persistence, or add operation mechanics.
* This dispatch milestone advances the project version from `0.18.0` to `0.19.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact partial dispatcher and public unavailable-resolver exception, and expose both from `llm_system.simulation`.
* Add high-signal behavioral tests proving exact Wait routing, exact successful Move routing, exact rejected Move routing, and typed unavailable capability for each of the five unresolved proposal variants.
* Tests shall compare dispatched results for equality with direct resolver behavior and prove exact preservation of caller identities and inputs without mocking internal project logic.
* Update README with the dispatch contract, supported branches, unavailable-operation behavior, caller-ID boundary, and exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Authorization, combined authorize-dispatch or dispatch-commit orchestration, outcome commitment, scheduler processing, persistence, or API/UI integration.
* Observe, Speak, Take, Use, or Help resolver mechanics; generic fallback outcomes; clarification; retries; or safe-failure narration.
* Changes to existing action, authorization, resolver, outcome, event, state-change, package, or runtime-state contracts.
* Resolver injection, monkeypatch-based routing tests, registry/configuration behavior, protocol classes, service objects, ID factories/providers, or speculative multi-event support.
* Exception issue tuples, error codes, Pydantic exception records, exception repair, logging, or exception translation.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/dispatch.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_actor_action_dispatch.py`.

The two new public names are exactly `dispatch_actor_action` and `OperationResolverUnavailableError`.

## Acceptance criteria

1. Authorized Wait dispatch returns the exact Wait resolver outcome with unchanged action and caller identities (`DISPATCH-002`, `DISPATCH-004`, `DISPATCH-005`).
2. Authorized successful and rejected Move dispatch return the exact Move resolver outcomes with unchanged action and caller identities (`DISPATCH-002`, `DISPATCH-004`, `DISPATCH-005`).
3. Each of Observe, Speak, Take, Use, and Help raises `OperationResolverUnavailableError`, exposes its exact typed operation, uses the accepted stable message, and produces no outcome (`DISPATCH-006` through `DISPATCH-008`).
4. Dispatch selection is exhaustive over the existing closed actor-action proposal variants and does not introduce string routing, a registry, configuration, or generated fallback (`DISPATCH-003`, `DISPATCH-010`).
5. Dispatch does not authorize, commit, generate identities, repair exceptions, process scheduling, invoke an LLM, or perform persistence or presentation (`DISPATCH-001`, `DISPATCH-005`, `DISPATCH-009`, `DISPATCH-010`).
6. Public exports and README accurately describe the partial dispatch and capability-error boundaries.
7. Existing authorization, resolver, commitment, package, and simulation behavior remains unchanged.
8. Project and installed metadata plus editable root `uv.lock` report `0.19.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production dispatch logic; record the import or missing-contract failure.
* Run focused dispatch tests after Wait, Move, and unavailable-operation groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.18.0` to `0.19.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires a new resolver, canonical fallback outcome, different identity interface, resolver injection or registration, authorization or commitment orchestration, exception aggregation, a dependency, or existing contract changes.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
