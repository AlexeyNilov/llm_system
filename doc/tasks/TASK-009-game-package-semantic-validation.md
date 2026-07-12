# TASK-009: Validate game-package references and topology

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-008

## Objective

Add one deterministic semantic-validation boundary over a loaded rule-and-scenario pair. It must return a typed relationally validated pair when dependency, uniqueness, references, player setup, and topology are coherent, or aggregate independent authoring defects as structured issues without producing misleading cascades.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Character definition”, “Decision-policy definition”, “Decision-policy reference”, “Entity definition”, “Game-package validation issue”, “Loaded game package”, “Spatial graph definition”, and “Validated game packages”
* `doc/requirements.md`: `PACK-003`, `PACK-009` through `PACK-011`, `PACK-014`, `PACK-019` through `PACK-026`, `RULE-002` through `RULE-006`, `SPACE-008` through `SPACE-014`, and `ENTITY-001` through `ENTITY-009`
* `doc/decisions.md`: “Separate authored spatial definitions from runtime state”, “Model scenario inhabitants as discriminated entity definitions”, “Begin rule-pack content with typed reference catalogs”, “Load each game package atomically as one typed pair”, and “Validate loaded package pairs with structured dependency-aware issues”
* `doc/high_level_design.md`: “Package loader and validator”, “Principal records”, and “Testing strategy”
* `src/llm_system/game_packages/`, `tests/test_game_packages.py`, `tests/test_rule_pack_definition.py`, `tests/test_scenario_pack_definition.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read the initial scenario, postponed ideas, unrelated requirements, or implementation roadmap beyond this task.

## Fixed assumptions

* The public operation is `validate_game_packages(rule_package: LoadedRulePackage, scenario_package: LoadedScenarioPackage) -> ValidatedGamePackages`.
* `ValidatedGamePackages` is strict, frozen, contains exactly `rule_package` and `scenario_package`, and preserves the supplied loaded-package objects. Direct construction is technically possible, but the validator is its only supported creation path.
* `ValidatedGamePackages` proves only this task's dependency, uniqueness, reference, player-count, and topology checks. It is not sufficient evidence for world creation.
* Validation does not mutate either loaded package and is deterministic.
* Failure raises one `GamePackageValidationError` whose public `issues` value is a non-empty immutable ordered tuple of strict frozen `ValidationIssue` records.
* `ValidationIssue` contains exactly `code: ValidationIssueCode`, `path: str`, and `message: str`; path and message are non-blank.
* `ValidationIssueCode` is a public `StrEnum` with exactly `duplicate-id`, `dependency-mismatch`, `unknown-reference`, `policy-type-mismatch`, `invalid-self-loop`, `unreachable-location`, `invalid-player-count`, and `invalid-possession-target`.
* Paths use deterministic dot-separated roots and authored numeric indices, for example `scenario.definition.entity_collection.entities[1].initial_location_id`. IDs are not path selectors because duplicates would make them ambiguous.
* For each namespace, the first occurrence of an ID is the reference candidate. Each later occurrence produces one `duplicate-id` issue at that repeated record's `.id` path.
* Uniqueness namespaces are locations, connections, all entity variants together, object archetypes, character archetypes, decision policies, and goals within each NPC. Identical text across different namespaces is valid.
* The scenario manifest's required rule ID and version must both match the supplied rule manifest. Any mismatch produces one dependency issue at `scenario.manifest.required_rule_pack`.
* Connection endpoints, character initial locations, location object placements, object archetypes, character archetypes, and policy IDs resolve only in their typed namespaces.
* A missing possession target produces `unknown-reference`; a uniquely resolved object target produces `invalid-possession-target`; a uniquely resolved character target is valid.
* An NPC policy type must match its uniquely resolved policy definition. Unused definitions are valid.
* Exactly one player is required. Every location must be reachable from that player's valid starting location by following directed connections. Reverse reachability is not required.
* Self-loops are invalid. Parallel directed connections with distinct IDs are valid.
* A reference to a duplicated target ID does not also produce `unknown-reference`; the duplicate issue is the root defect.
* Scenario-to-rule archetype and policy checks are skipped when the required rule identity does not match the supplied rule package.
* Reachability is skipped unless location IDs and connection IDs are unique, all connection endpoints resolve, exactly one player exists, and that player's initial location resolves uniquely. Self-loop detection remains independent.
* Policy-type comparison is skipped unless the referenced policy resolves uniquely.
* Issue ordering is: dependency mismatch; rule catalog duplicates in object-archetype, character-archetype, then policy order; scenario location and connection duplicates; entity and per-NPC goal duplicates; player count; connection self-loops and endpoints in authored connection order; entity references in authored entity and field order; then unreachable locations in authored location order.
* Policy implementation-registry checks, supported operations, persistent-world compatibility, content lint warnings, and general playability are deferred.
* No new dependency or dependency-version change is authorized. The lockfile's editable root-package version must track the project version.
* This new public contract advances the project version from `0.7.0` to `0.8.0`.

## In scope

* Add the issue-code enum, validation-issue record, aggregate error, validated-pair model, and public validator.
* Implement deterministic namespace indexing, dependency-aware reference checks, player-count validation, self-loop checks, and player-rooted directed reachability.
* Aggregate every independent issue in the fixed order while gating checks whose prerequisites are invalid.
* Export `ValidationIssueCode`, `ValidationIssue`, `GamePackageValidationError`, `ValidatedGamePackages`, and `validate_game_packages` from `llm_system.game_packages`.
* Add focused behavioral tests for a valid complete pair, every issue code, namespace scope, aggregation order, duplicate handling, dependency and reachability gating, one-way reachability, parallel connections, unused definitions, immutability, and input preservation.
* Update project version, root lockfile metadata, package-version test, and README public-contract documentation.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Loading files, changing loaded-package models, or changing any manifest or content definition.
* Policy implementation-registry lookup or executable policy validation required later by `RULE-005`.
* Supported operations, mechanics, scenario completeness, content warnings, general playability, persistent-state compatibility, world creation, or migration.
* Global identifier uniqueness or rejection of unused definitions.
* Strong graph connectivity, reverse reachability, implicit reverse edges, coordinates, path costs, connection-state conditions, or parallel-edge rejection.
* Error severity, warnings, source line/column capture, automated repair, localization, or serialization APIs.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, or agent configuration.

## Expected contracts and files

The new public boundary is:

```python
from llm_system.game_packages import (
    GamePackageValidationError,
    ValidatedGamePackages,
    ValidationIssue,
    ValidationIssueCode,
    validate_game_packages,
)
```

The implementation may use a focused `validation.py` module and private small helpers or indexes. Existing loaded-package, manifest, and definition imports and behavior must remain compatible.

## Acceptance criteria

1. A coherent loaded rule-and-scenario pair returns one frozen `ValidatedGamePackages` preserving both exact input objects, and its nested packages remain immutable (`PACK-020`).
2. Failure raises `GamePackageValidationError` with a non-empty immutable tuple of strict frozen issues; issue codes are the fixed public enum, paths use authored numeric indices, messages are non-blank, and independent issues follow the fixed deterministic order (`PACK-021`).
3. Later duplicate occurrences are reported within every defined namespace, while reuse across distinct namespaces and parallel edges with distinct connection IDs remain valid (`PACK-022`, `RULE-005`, `SPACE-014`, `ENTITY-008`).
4. Exact dependency mismatch produces one issue, does not prevent independent rule and scenario checks, and suppresses only scenario-to-rule archetype and policy checks (`PACK-023`, `PACK-025`).
5. Connection endpoints, character locations, location placements, archetypes, and policy IDs resolve in typed namespaces; possession distinguishes missing from non-character targets; policy type mismatch is reported only after unique resolution (`PACK-023`, `ENTITY-003`, `ENTITY-004`, `ENTITY-006`, `ENTITY-008`).
6. A player count other than one produces one issue. When graph prerequisites are valid, every location not directed-reachable from the player's start produces one issue in authored location order (`PACK-023` through `PACK-025`).
7. Each self-loop produces an independent issue, one-way player-rooted topology is valid, and strong or reverse connectivity is not required (`PACK-024`, `SPACE-014`).
8. References to duplicated target IDs do not create unknown-reference cascades; invalid dependency, ambiguous graph identity, missing endpoints, invalid player count, or missing player start suppress only their defined dependent checks (`PACK-025`).
9. Unused locations, archetypes, and policies do not produce issues, and this validator performs no policy-registry, supported-operation, persistent-state, or general playability checks (`PACK-026`, `RULE-005`).
10. The five named public imports work and all existing loading and structural-definition tests remain passing without behavior changes.
11. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.8.0`; dependencies and all resolved dependency versions remain unchanged.
12. README documents the relational validation boundary, issue aggregation and gating, directed reachability semantics, and explicit limits of `ValidatedGamePackages`.

## Required verification

* Write and run the first valid-pair behavioral test before adding validation implementation; record the expected import failure.
* Run focused semantic-validation tests after each meaningful behavior group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.7.0` to `0.8.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires changing loaded or authored models, adding an issue code, changing path or ordering semantics, globalizing ID uniqueness, failing fast, emitting dependent cascades, inferring cross-namespace targets, requiring reverse reachability, rejecting unused definitions, checking policy implementations or mechanics, adding a dependency, or treating this result as sufficient world-readiness evidence.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
