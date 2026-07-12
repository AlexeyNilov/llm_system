# TASK-013: Validate runtime state against game packages

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-012, TASK-009

## Objective

Provide one public relational validation boundary that compares a structural `WorldState` with one `ValidatedGamePackages` pair. Success returns a narrow immutable `ValidatedWorldState`; failure returns deterministic structured runtime-state issues without mutating or repairing either input.

This task proves overlay completeness, uniqueness, definition matching, and current reference validity only. It does not initialize a world or prove executable mechanics, policies, persistence compatibility, or playability.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Canonical world state”, “Validated game packages”, and “Validated world state”
* `doc/requirements.md`: `STATE-010` through `STATE-013` and `STATE-021` through `STATE-037`
* `doc/decisions.md`: “Require complete overlays at world readiness”, “Separate runtime-state structure from world-readiness validation”, “Require a narrow validated-world-state wrapper at the arbiter boundary”, “Give world-state validation its own structured issue vocabulary”, “Order world-state issues by namespace, authorship, and runtime occurrence”, and “Address world-state issues with runtime field paths”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/simulation/state.py`, `src/llm_system/simulation/__init__.py`, `src/llm_system/game_packages/validation.py`, `src/llm_system/game_packages/entities.py`, `src/llm_system/game_packages/spatial.py`, `tests/test_runtime_state.py`, `tests/test_game_package_validation.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other completed task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `validate_world_state(packages: ValidatedGamePackages, state: WorldState) -> ValidatedWorldState`.
* `ValidatedWorldState` is a strict frozen Pydantic model containing exactly the supplied `packages` and `state` objects and preserving their identity.
* The successful wrapper guarantees exactly one runtime record per authored character, object, and connection, with no extra runtime records.
* Authored characters are both player-character and NPC-character definitions; authored objects and connections use their respective typed definitions. Entity authored order is filtered independently for character and object missing-state ordering.
* Character and object current locations resolve against authored scenario locations. Object possessors resolve against authored characters.
* Initial issue codes are exactly `duplicate-state-id`, `missing-state`, `unexpected-state`, and `unknown-runtime-reference` in a `WorldStateValidationIssueCode` `StrEnum`.
* `WorldStateValidationIssue` is strict and frozen with exactly `code`, non-blank `path`, and non-blank `message`.
* `WorldStateValidationError` requires a non-empty tuple containing only `WorldStateValidationIssue` records and exposes it as immutable `issues` evidence.
* Validation order is character overlays, object overlays, connection overlays, then character references followed by object references.
* Within each overlay namespace, duplicate issues follow first-duplicate encounter order, missing issues follow filtered authored order, and unexpected issues follow runtime tuple order.
* Duplicate and unexpected record issues point to their indexed ID fields. Missing issues point to exactly `characters`, `objects`, or `connections` and mention the missing ID in their messages.
* Runtime references are checked only for records whose owning state ID is both expected and unique. Character-reference paths are `characters[N].location_id`. Object reference paths are `objects[N].placement.location_id` or `objects[N].placement.character_id`.
* A location reference is unknown only when its ID is absent from authored locations. A possessor reference is unknown only when its ID is absent from authored characters; a valid authored character with missing runtime state produces only the independent missing-state issue.
* Inputs already contain `ValidatedGamePackages`, so package definitions and their identifiers are relationally coherent. Do not defensively re-run or duplicate package validation.
* Independent issues are aggregated; validation returns no partial wrapper when any issue exists.
* Validation is pure: it does not reorder, normalize, repair, copy-update, or mutate packages or state.
* No world initialization, default availability, operation resolution, policy-registry check, persistence, or playability validation is introduced.
* No new dependency is required.
* This public validation milestone advances the project version from `0.11.0` to `0.12.0`; the lockfile's editable root-package version must match.

## In scope

* Add the issue enum, issue record, application-owned error, validated wrapper, and public validation function.
* Implement complete deterministic validation and the accepted cascade suppression.
* Expose all five public contracts through `llm_system.simulation`.
* Add behavioral tests for valid identity-preserving success, every issue code and path category, deterministic multi-issue ordering, cascade suppression, error invariants, immutability, and input preservation.
* Update README with the relational boundary, exact guarantee and exclusions, and a concise public invocation example.
* Update project version, root lockfile metadata, package-version test, and this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Changes to structural runtime-state, action, game-package, or package-validation public behavior.
* World construction from initial placements, implicit connection availability, snapshot repair, or migrations.
* Outcomes, state changes, events, arbiter or operation logic, authorization, randomness, scheduling, perception, persistence, APIs, or UI.
* Policy implementation registry, supported-mechanics readiness, persistent-world compatibility, or scenario playability.
* New issue codes, warning levels, issue sorting modes, generic validation frameworks, shared package/runtime issue classes, or generic mappings.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production belongs in `src/llm_system/simulation/validation.py`, publicly re-exported from `src/llm_system/simulation/__init__.py`. Likely tests belong in `tests/test_world_state_validation.py`.

The public names are exactly:

* `WorldStateValidationIssueCode`
* `WorldStateValidationIssue`
* `WorldStateValidationError`
* `ValidatedWorldState`
* `validate_world_state`

Follow the existing package validator's immutable result and application-owned error patterns where they fit, but do not reuse its issue enum or issue record.

## Acceptance criteria

1. A complete coherent snapshot returns `ValidatedWorldState` preserving the exact input package and state objects; the result is immutable (`STATE-021`, `STATE-022`).
2. Duplicate, missing, and unexpected character, object, and connection overlays produce their exact codes, paths, messages, namespace ordering, and within-namespace ordering (`STATE-010`, `STATE-011`, `STATE-027`, `STATE-030`, `STATE-031`).
3. Unknown character locations, object locations, and object possessors produce `unknown-runtime-reference` at exact indexed runtime field paths and in accepted reference order (`STATE-028`, `STATE-032`, `STATE-033`, `STATE-035`).
4. References from duplicated or unexpected owning records are suppressed, and a valid authored possessor with missing runtime overlay is not mislabeled as an unknown reference (`STATE-029`, `STATE-034`).
5. Missing-state paths name only the affected collection and messages identify the missing authored IDs (`STATE-036`).
6. Multiple independent defects are returned together in one deterministic immutable issue tuple, while any issue prevents return of `ValidatedWorldState` (`STATE-025`, `STATE-028` through `STATE-032`).
7. The issue record is strict and immutable; the error rejects empty, non-tuple, or wrongly typed issue collections (`STATE-026` through `STATE-028`).
8. Validation leaves both inputs unchanged and does not re-run package validation, initialize defaults, or claim stronger readiness (`STATE-012`, `STATE-024`).
9. Public imports and README describe the narrow relational guarantee and exclusions accurately (`STATE-023`, `STATE-024`, `STATE-037`).
10. Existing action, package, and runtime-state behavior remains unchanged.
11. Project and installed metadata plus the editable root in `uv.lock` report `0.12.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production validation logic; record the import or missing-contract failure.
* Run focused world-state validation tests after each meaningful validation group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.11.0` to `0.12.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede production validator creation; do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires another issue code, different ordering or path semantics, package revalidation, snapshot repair or initialization, changing existing public models, adding a stronger readiness claim, a dependency, or generic validation infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
