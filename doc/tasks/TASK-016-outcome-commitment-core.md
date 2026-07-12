# TASK-016: Implement the arbiter outcome-commitment core

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-013, TASK-015

## Objective

Provide a pure deterministic commitment boundary that validates a structurally valid outcome against one `ValidatedWorldState`, applies a complete valid change set atomically, and returns the exact trace outcome paired with the resulting validated world.

This task does not authorize a submission or resolve an action proposal. It establishes safe state-dependent outcome commitment only.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Canonical world state”, “Event”, “Outcome”, “Simulation arbiter”, “State change” if present, and “Validated world state”
* `doc/requirements.md`: `ARBITER-001` through `ARBITER-021`, `STATE-004` through `STATE-006`, `STATE-021` through `STATE-025`, and `ACTION-029` through `ACTION-038`
* `doc/decisions.md`: “Replace immutable world-state snapshots atomically”, “Commit outcomes into one validated-world result”, “Reject invalid commitment with structured atomic issues”, “Validate commitment in outcome order with target gating”, “Preserve world identity when commitment changes no state”, and “Separate arbiter commitment from operation resolution”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/__init__.py`, `tests/test_runtime_state.py`, `tests/test_world_state_validation.py`, `tests/test_outcomes.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `commit_outcome(world: ValidatedWorldState, outcome: Outcome) -> OutcomeCommitResult`.
* `OutcomeCommitResult` is strict and frozen and contains exactly `outcome` and `world`, preserving the exact supplied outcome object.
* `OutcomeCommitIssueCode` is a `StrEnum` with exactly `resolution-time-mismatch`, `unknown-change-target`, `before-value-mismatch`, and `unknown-after-reference`.
* `OutcomeCommitIssue` is strict and frozen with exactly `code`, non-blank `path`, and non-blank `message`.
* `OutcomeCommitError` requires a non-empty tuple containing only `OutcomeCommitIssue` records and exposes the tuple as `issues`.
* Rejected outcomes and valid-attempt outcomes without `SimulationTimeChanged` require `resolved_at_seconds == world.state.simulation_time_seconds`; mismatch path is `outcome.resolved_at_seconds` and is reported before change issues.
* Rejected outcome success returns the exact supplied `ValidatedWorldState`. It has no effects by structural contract.
* For failed and succeeded outcomes, inspect state changes in tuple order and collect all issues before applying anything.
* Character, object, and connection change targets resolve against their respective complete runtime-state tuples, not directly against generic entity definitions.
* Unknown target paths are `outcome.state_changes[N].character_id`, `.object_id`, or `.connection_id`. An unknown target produces only `unknown-change-target` for that change and suppresses its before and after checks.
* For a known character target, compare current `location_id` with `from_location_id`; then validate `to_location_id` against authored locations.
* For a known object target, compare exact current placement with `from_placement`; then validate a `to_placement` location against authored locations or possessor against authored characters. A valid authored possessor does not require a separate check for its runtime overlay because `ValidatedWorldState` already guarantees completeness.
* For a known connection target, compare strict current availability with `from_available`; its boolean after value requires no reference validation.
* For `SimulationTimeChanged`, compare `from_seconds` with current world time and `to_seconds` with outcome completion time. Its paths are the indexed `from_seconds` and `to_seconds` fields.
* Known-target issue ordering is before mismatch followed by independently invalid after reference. Exact nested object after paths end in `to_placement.location_id` or `to_placement.character_id`.
* All issue messages are non-blank and identify the mismatch meaning; exact prose is an implementation choice except paths and codes are stable contracts.
* Any issue raises one `OutcomeCommitError` with the complete deterministic tuple. Inputs remain unchanged and no event is considered committed.
* If no issues exist and no state changes exist, return the exact input world object for rejected, failed, or succeeded outcomes.
* If changes exist, apply them to immutable replacements at existing tuple positions, preserve unaffected record identities and all collection order, and update simulation time only through `SimulationTimeChanged`.
* Pair the replacement state with the exact existing `ValidatedGamePackages` object and call the public `validate_world_state` boundary. An unexpected `WorldStateValidationError` at this point must become an `AssertionError` identifying a kernel invariant defect, preserving the original exception as its cause.
* Events remain inside the exact outcome and are not copied, interpreted, filtered, persisted, or applied by this function.
* The core does not inspect the originating proposal or submission and does not validate proposal IDs, source authority, actionability, operation meaning, or agreement between events and changes.
* No new dependency is required.
* This behavior milestone advances the project version from `0.14.0` to `0.15.0`; the lockfile's editable root-package version must match.

## In scope

* Add the commitment issue enum, issue record, application-owned error, immutable result, and public commit operation.
* Implement exhaustive validation and immutable application for all four existing state-change variants.
* Revalidate changed snapshots through `validate_world_state` and preserve accepted object identities and tuple order.
* Expose all intended public contracts from `llm_system.simulation`.
* Add behavioral tests for rejection, event-only and empty valid attempts, every change type, multiple independent changes, exact identities/order, every issue code/path, deterministic aggregation/gating, atomic failure, and invariant-failure wrapping.
* Update README with the commitment boundary, atomicity, exact guarantees, and explicit exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Proposal or submission lookup, source authorization, action dispatch, resolver invocation, outcome generation, reason-code catalogs, or operation-specific semantic agreement.
* Randomness, world initialization, scheduling, perception, persistence, APIs, UI, narration, or System notifications.
* New state, change, event, outcome, or issue variants; partial application; snapshot repair; record sorting; mutable indexes; or generic change dispatch registries.
* Treating canonical events as state mutation commands or persisting them.
* Changes to existing public contract behavior beyond additive commitment exports.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production belongs in `src/llm_system/simulation/commitment.py`, publicly re-exported from `src/llm_system/simulation/__init__.py`. Focused tests likely belong in `tests/test_outcome_commitment.py`.

Public names are exactly `OutcomeCommitIssueCode`, `OutcomeCommitIssue`, `OutcomeCommitError`, `OutcomeCommitResult`, and `commit_outcome`.

## Acceptance criteria

1. Rejected outcomes and no-change valid outcomes commit only when completion time equals current world time, preserve exact outcome and world identity, and expose no duplicated event field (`ARBITER-005` through `ARBITER-007`, `ARBITER-019`, `ARBITER-020`).
2. Every existing state-change variant validates target, before value, after reference, and time semantics at exact indexed paths and accepted ordering (`ARBITER-008`, `ARBITER-015` through `ARBITER-019`).
3. Unknown targets suppress dependent issues; known targets may report before mismatch then independently invalid after reference (`ARBITER-016`, `ARBITER-017`).
4. Multiple independent issues aggregate deterministically, raise one strict `OutcomeCommitError`, and leave the input world and all events uncommitted (`ARBITER-010` through `ARBITER-013`).
5. Successful changes produce one new structurally and relationally validated snapshot, preserve packages, unaffected record identities and tuple order, and replace only affected fields (`ARBITER-008`, `ARBITER-021`).
6. Unexpected failure of final `validate_world_state` is raised as a chained kernel-invariant `AssertionError`, not an ordinary commit issue (`ARBITER-014`).
7. `OutcomeCommitResult` and issue evidence are strict, immutable, and contain only the accepted fields (`ARBITER-006`, `ARBITER-010` through `ARBITER-012`).
8. The core does not inspect proposals, authorize sources, resolve operations, interpret events, or introduce missing mechanics (`ARBITER-001` through `ARBITER-004`, `ARBITER-009`).
9. Public exports and README accurately describe atomic commitment and its exclusions.
10. Existing simulation and package behavior remains unchanged.
11. Project and installed metadata plus editable root `uv.lock` report `0.15.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production commitment logic; record the import or missing-contract failure.
* Run focused commitment tests after each validation and application group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.14.0` to `0.15.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires proposal context, operation semantics, another issue code, different ordering or gating, partial application, state repair, a new public variant, a dependency, or persistence behavior.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
