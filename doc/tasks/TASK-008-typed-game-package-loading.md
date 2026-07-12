# TASK-008: Load complete typed game packages

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-007

## Objective

Replace the public manifest-only loading boundary with one atomic game-package loader that returns a strict immutable manifest-definition pair only after both package documents validate. Rule and scenario packages must be selected by their validated manifest type and must fail behind one application-owned loading error without exposing partial results.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Game package”, “Loaded game package”, “Rule pack”, “Rule-pack definition”, “Scenario pack”, and “Scenario-pack definition”
* `doc/requirements.md`: `PACK-001` through `PACK-019`, `RULE-001` through `RULE-006`, `SPACE-008`, and `ENTITY-001`
* `doc/decisions.md`: “Author game packages in YAML and validate with Pydantic”, “Use self-contained exact-version game package manifests”, and “Load each game package atomically as one typed pair”
* `doc/high_level_design.md`: “Package loader and validator”, “Principal records”, and “Testing strategy”
* `src/llm_system/game_packages/`, `tests/test_game_packages.py`, `tests/test_rule_pack_definition.py`, `tests/test_scenario_pack_definition.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read the initial scenario, postponed ideas, unrelated requirements, or implementation roadmap beyond this task.

## Fixed assumptions

* The only public loading operation is `load_game_package(package_directory: Path) -> LoadedGamePackage`.
* `load_package_manifest` is removed completely rather than retained publicly or as a same-named private helper.
* `PackageManifestError` is replaced by `GamePackageLoadError`; loader failures preserve the originating exception as `__cause__`.
* `LoadedRulePackage` pairs exactly `RulePackageManifest` with `RulePackDefinition`; `LoadedScenarioPackage` pairs exactly `ScenarioPackageManifest` with `ScenarioPackDefinition`.
* Both loaded-package wrappers are strict and frozen. They do not duplicate `package_type`; their concrete class is the runtime discriminator and the manifest remains the sole data-level source of package type.
* `LoadedGamePackage` is the public union of those two concrete wrappers.
* The validated manifest selects the entrypoint definition. The loader never infers package type from entrypoint keys.
* Loading is atomic: no manifest, raw mapping, or other partial result is returned when either document or any path check fails.
* The loader processes exactly one package-version directory. It preserves a scenario manifest's exact required-rule-pack reference but does not locate, load, or validate that dependency.
* Reference resolution, uniqueness, graph invariants, package compatibility, supported-operation validation, and playability remain deferred.
* Existing safe YAML parsing, exact directory-identity rules, and entrypoint containment rules remain in force.
* No new dependency or dependency-version change is authorized. The lockfile's editable root-package version must track the project version.
* This replacement public contract advances the project version from `0.6.0` to `0.7.0`.

## In scope

* Add strict immutable loaded-rule and loaded-scenario wrapper models plus their public union.
* Add `load_game_package` and refactor private loader stages as needed to load and validate both manifest and selected entrypoint.
* Remove `load_package_manifest` and `PackageManifestError` from implementation, public exports, current tests, and README documentation. Completed historical task records remain unchanged.
* Add and export `GamePackageLoadError`, `LoadedGamePackage`, `LoadedRulePackage`, `LoadedScenarioPackage`, and `load_game_package`.
* Preserve existing manifest, spatial, entity, rule-root, and scenario-root contracts.
* Add focused behavioral tests for valid rule and scenario loading, concrete wrapper pairing, immutability, manifest-directed schema selection, atomic failure, safe paths and YAML, error chaining, and non-resolution of scenario dependencies.
* Update project version, root lockfile metadata, package-version test, and README public-contract documentation.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Package discovery or catalog scanning.
* Loading, locating, or validating a scenario's required rule package.
* Cross-record, graph, cross-package, reference, uniqueness, supported-operation, compatibility, or playable-scenario validation.
* A partial-manifest, metadata browsing, diagnostic-result, or error-code API.
* Changes to manifest or content schemas, package filesystem layout, authored models, or safe-YAML policy.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, or agent configuration.

## Expected contracts and files

The replacement public loading boundary is:

```python
from llm_system.game_packages import (
    GamePackageLoadError,
    LoadedGamePackage,
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
)
```

The existing concrete manifest and content-definition models remain public. `load_package_manifest` and `PackageManifestError` no longer exist in the public package or loader implementation.

Likely implementation files are `src/llm_system/game_packages/loader.py`, `errors.py`, `models.py` or one focused loaded-package module, and `__init__.py`. Existing private helpers may be renamed or split where that makes the atomic loading flow clearer.

## Acceptance criteria

1. A valid rule package loads as a frozen `LoadedRulePackage` containing its exact `RulePackageManifest` and validated `RulePackDefinition` (`PACK-001`, `PACK-010`, `PACK-018`, `PACK-019`).
2. A valid scenario package loads as a frozen `LoadedScenarioPackage` containing its exact `ScenarioPackageManifest` and validated `ScenarioPackDefinition`, while its required-rule reference remains data and need not exist on disk (`PACK-002`, `PACK-014`, `PACK-018`, `PACK-019`).
3. `LoadedRulePackage` cannot contain scenario manifest or definition types, `LoadedScenarioPackage` cannot contain rule types, unknown wrapper fields are rejected, and both wrappers and their nested values are immutable (`PACK-010`, `PACK-019`).
4. The validated manifest type alone selects entrypoint validation; rule-shaped content under a scenario manifest and scenario-shaped content under a rule manifest raise `GamePackageLoadError` rather than being inferred or returned (`PACK-018`).
5. Missing, malformed, unsafe, invalid, or directory-inconsistent manifests and entrypoints raise `GamePackageLoadError`, preserve a non-null underlying `__cause__`, and return no partial package (`PACK-003`, `PACK-010`, `PACK-011`, `PACK-015` through `PACK-017`).
6. Existing absolute, traversal, non-YAML, missing, directory, and symlink-escaping entrypoint rejection remains covered, and unsafe YAML constructors are never executed (`PACK-011`, `PACK-016`, `PACK-017`).
7. `load_game_package`, the loaded-package types, and `GamePackageLoadError` are public; `load_package_manifest` and `PackageManifestError` are absent from the package and implementation.
8. Every existing manifest and content-definition behavior remains passing after tests are migrated from partial loading to complete package loading.
9. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.7.0`; dependencies and all resolved dependency versions remain unchanged.
10. README documents atomic complete-package loading, concrete result pairing, manifest-directed selection, the single error boundary, and explicit deferral of dependency and semantic validation. It must not describe manifest-only loading as available.

## Required verification

* Write and run the first complete-package-loading behavioral test before adding the replacement implementation; record the expected import failure.
* Run focused loader tests after each meaningful behavior group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.6.0` to `0.7.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires exposing a partial result, retaining the old loader or error, duplicating package type, inferring content type, resolving a dependency or reference, adding semantic validation, changing an authored schema or filesystem layout, adding a dependency, weakening safe parsing, path containment, strictness, or immutability, or changing either schema version.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
