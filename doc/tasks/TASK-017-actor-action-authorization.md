# TASK-017: Authorize actor-action submissions

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-011, TASK-013

## Objective

Provide a pure deterministic authorization boundary that binds a trusted actor-action submission source to the intended authored character and configured NPC policy. Success returns a type-proven immutable wrapper preserving the exact validated world and submission.

This task establishes source authority only. It does not inspect proposal targets, actionability, operation rules, outcomes, or commitment.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Action proposal submission”, “Actor”, “Character”, “Decision policy”, “Player”, “NPC”, and “Validated world state” where present
* `doc/requirements.md`: `ACTION-011` through `ACTION-014`, `ACTION-020` through `ACTION-023`, and `AUTHZ-001` through `AUTHZ-015`
* `doc/decisions.md`: “Separate proposal payloads from trusted submission metadata”, “Inject UUID runtime identities and type submission sources”, “Authorize actor submissions before operation dispatch”, and “Gate authorization errors from actor identity to policy”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/__init__.py`, `src/llm_system/game_packages/entities.py`, `tests/test_actions.py`, `tests/test_world_state_validation.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `authorize_actor_action(world: ValidatedWorldState, submission: ActorActionSubmission) -> AuthorizedActorAction`.
* `AuthorizedActorAction` is a strict frozen Pydantic model containing exactly `world` and `submission`, preserving the exact supplied objects.
* `ActorActionAuthorizationIssueCode` is a `StrEnum` with exactly `unknown-actor`, `source-actor-mismatch`, `actor-type-mismatch`, and `policy-mismatch`.
* `ActorActionAuthorizationIssue` is strict and frozen with exactly `code`, non-blank `path`, and non-blank `message`.
* `ActorActionAuthorizationError` requires a non-empty tuple containing only typed authorization issues and exposes it as `issues`.
* Resolve the intended actor only from `submission.actor_id` against authored player-character and NPC-character definitions in `world.packages`. `ValidatedWorldState` already guarantees its runtime overlay exists.
* Unknown intended actor raises one `unknown-actor` issue at `submission.actor_id`; no source-specific checks run.
* A `PlayerInterpreterActionSource` is authorized only when the intended authored actor is the one `PlayerCharacterDefinition`. Its `interpreter_id` is retained as trusted provenance and is not checked against configuration or an allowlist.
* A player-interpreter source targeting a known NPC raises one `actor-type-mismatch` issue at `submission.actor_id`.
* For `NpcPolicyActionSource`, compare `source.npc_id` with `submission.actor_id` before actor type or policy. Mismatch raises one `source-actor-mismatch` at `submission.source.npc_id` and stops.
* A matching NPC-policy source targeting the authored player raises one `actor-type-mismatch` at `submission.actor_id` and stops.
* A matching NPC-policy source targeting an authored NPC compares `source.policy_id` with exactly `npc.decision_policy.policy_id`. Mismatch raises one `policy-mismatch` at `submission.source.policy_id`.
* Policy type requires no second check: `ValidatedGamePackages` already proves the NPC policy reference agrees with its package definition, while the source contract carries only policy identity.
* Current rules produce exactly one root issue on failure, but the error uses the project-standard non-empty tuple contract.
* Authorization is pure and does not mutate, normalize, copy-update, repair, or replace either input.
* Do not inspect `submission.proposal`, proposal target IDs, simulation-step ID, decision-context ID, actor current location, connection availability, possession, or any operation-specific state.
* Do not dispatch, resolve, generate an outcome, commit state, interpret events, or invoke an LLM.
* No new dependency is required.
* This public authorization milestone advances the project version from `0.15.0` to `0.16.0`; the lockfile's editable root-package version must match.

## In scope

* Add the authorization issue enum, issue record, application-owned error, immutable authorized wrapper, and public authorization operation.
* Implement exhaustive source-specific authorization over the closed source union and authored character union.
* Expose all intended public contracts from `llm_system.simulation`.
* Add behavioral tests for player and NPC success, exact identity preservation, every issue code/path, all cascade suppression, error invariants, immutability, interpreter provenance non-validation, and deliberate proposal/actionability non-validation.
* Update README with the authority boundary, exact source rules, trusted interpreter provenance, and explicit exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Operation dispatch, resolver registries, resolver invocation, proposal-target or actionability validation, outcome generation, commitment, or event semantics.
* Interpreter configuration or allowlists, session authentication, API authorization, user accounts, policy implementation registry, or LLM-provider trust.
* Randomness, scheduling, perception, persistence, APIs, UI, narration, or System notifications.
* World-action or scheduled-activity authorization, additional actor source variants, role hierarchies, permissions, capabilities, or generic authorization frameworks.
* New issue codes, multi-principal aggregation, warnings, or generic metadata dictionaries.
* Changes to existing public contract behavior beyond additive authorization exports.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production belongs in `src/llm_system/simulation/authorization.py`, publicly re-exported from `src/llm_system/simulation/__init__.py`. Focused tests likely belong in `tests/test_actor_action_authorization.py`.

Public names are exactly `ActorActionAuthorizationIssueCode`, `ActorActionAuthorizationIssue`, `ActorActionAuthorizationError`, `AuthorizedActorAction`, and `authorize_actor_action`.

## Acceptance criteria

1. Player-interpreter source for the authored player and matching NPC-policy source for an authored NPC return immutable wrappers preserving exact input identity (`AUTHZ-002` through `AUTHZ-006`).
2. Unknown actor, player-to-NPC, NPC-source identity mismatch, NPC-source-to-player, and configured-policy mismatch produce exact codes and paths with accepted gating (`AUTHZ-009` through `AUTHZ-015`).
3. Interpreter identity is retained but not allowlisted, and NPC policy type is not redundantly revalidated (`AUTHZ-007`).
4. Error and issue contracts reject empty, non-tuple, wrongly typed, blank, extra, or mutated evidence (`AUTHZ-009`, `AUTHZ-010`).
5. Authorization leaves both inputs unchanged and does not inspect or validate a proposal's operation-specific target or current actionability (`AUTHZ-001`, `AUTHZ-008`).
6. Closed source and character variants are handled exhaustively without a generic role string or permission dictionary.
7. Public exports and README accurately describe trusted-envelope actor binding and all exclusions.
8. Existing simulation and package behavior remains unchanged.
9. Project and installed metadata plus editable root `uv.lock` report `0.16.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production authorization logic; record the import or missing-contract failure.
* Run focused authorization tests after each source branch and error group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.15.0` to `0.16.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires dispatch, operation semantics, another source or issue code, interpreter configuration, different gating, proposal inspection, a dependency, or generic authorization infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
