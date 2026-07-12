# TASK-003: Load trusted game-package manifests

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-002

## Objective

Provide one application-owned function that safely loads a rule or scenario `manifest.yaml` from a versioned game-package directory and returns a strict immutable manifest model. Invalid YAML, schema violations, directory inconsistencies, and unsafe or missing entrypoints must fail without exposing raw mappings to downstream code.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Game package”, “Rule pack”, and “Scenario pack”
* `doc/requirements.md`: `PACK-001` through `PACK-017` and `DEV-001` through `DEV-006`
* `doc/decisions.md`: “Author game packages in YAML and validate with Pydantic”, “Standardize the initial Python project foundation”, and “Use self-contained exact-version game package manifests”
* `doc/high_level_design.md`: “Package loader and validator” and “Testing strategy”
* `pyproject.toml`, `Makefile`, and the existing `src/` and `tests/` trees

Do not read the initial scenario, postponed ideas, experiment report, or unrelated architecture sections.

## Fixed assumptions

* Packages live below `game_packages/rules/<package-id>/<package-version>/` or `game_packages/scenarios/<package-id>/<package-version>/` and use the exact filename `manifest.yaml`.
* The initial manifest schema contains `schema_version`, `package_id`, `package_version`, `package_type`, `title`, and `entrypoint`.
* `schema_version` is the strict integer literal `1`; booleans, strings, and coerced values are invalid.
* Package identifiers match lowercase kebab-case and versions match stable `MAJOR.MINOR.PATCH`. Version ranges, prereleases, and build metadata are invalid in schema version 1.
* `package_type` is the discriminator: `rule` manifests reject `required_rule_pack`, while `scenario` manifests require one exact `package_id` and `package_version` under `required_rule_pack`.
* The entrypoint is one relative path ending in `.yaml`. Absolute paths, traversal, non-YAML paths, directory targets, missing files, and resolved paths outside the package directory are invalid.
* This task validates only manifests and entrypoint safety. It does not parse entrypoint content or resolve whether a scenario's required rule-pack directory exists.
* Pydantic 2 and PyYAML are the only new runtime dependencies authorized by this task.
* This new public feature advances the project version from `0.1.0` to `0.2.0`.

## In scope

* Add Pydantic 2 and PyYAML as bounded runtime dependencies and refresh `uv.lock`.
* Add strict frozen manifest models and a discriminated rule-or-scenario union below `src/llm_system/game_packages/`.
* Add `load_package_manifest(package_directory: Path) -> PackageManifest`.
* Safely parse YAML, validate the typed schema, confirm the package directory suffix matches type, identifier, and version, and validate the resolved entrypoint.
* Add one application-owned `PackageManifestError` that preserves underlying parse or validation failures as exception causes.
* Export only `PackageManifest`, `PackageManifestError`, `RulePackageManifest`, `ScenarioPackageManifest`, and `load_package_manifest` from `llm_system.game_packages`.
* Add focused behavioral tests using temporary package directories.
* Update project version and README for the new public manifest-loading boundary.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Permanent Greybridge package files or any other authored game content.
* Parsing or modeling rule or scenario entrypoint contents.
* Resolving the scenario's required rule pack, scanning a package catalog, cross-record reference validation, graph validation, or supported-operation validation.
* Dependency ranges, prerelease or build versions, YAML includes, multiple entrypoints, merge behavior, package inheritance, or remote packages.
* A public error-code taxonomy or direct exposure of PyYAML and Pydantic exceptions.
* Changes to `AGENTS.md`, governance documents, roadmap, glossary, high-level design, scenario, ideas, experiments, or delegation configuration.

## Expected contracts and files

The public import boundary is:

```python
from llm_system.game_packages import (
    PackageManifest,
    PackageManifestError,
    RulePackageManifest,
    ScenarioPackageManifest,
    load_package_manifest,
)
```

Likely implementation files are `src/llm_system/game_packages/__init__.py`, `models.py`, `loader.py`, and `errors.py`. Exact internal separation may change if a smaller arrangement remains readable; the public imports must not.

`load_package_manifest` accepts the package-version directory, reads `<package-directory>/manifest.yaml`, and either returns the validated discriminated manifest or raises `PackageManifestError`. Downstream callers do not receive raw YAML dictionaries or library-specific validation exceptions.

## Acceptance criteria

1. A valid rule manifest in a matching `rules/<id>/<version>/` directory loads as a frozen `RulePackageManifest` (`PACK-001`, `PACK-008`, `PACK-012`, `PACK-013`, `PACK-015`).
2. A valid scenario manifest with an exact rule-pack pin loads as a frozen `ScenarioPackageManifest` (`PACK-002`, `PACK-008`, `PACK-012` through `PACK-015`).
3. Rule manifests containing `required_rule_pack`, scenario manifests lacking it, unknown fields, coerced scalar types, unsupported schema versions, invalid IDs, invalid stable versions, or blank titles raise `PackageManifestError` (`PACK-010`, `PACK-012` through `PACK-014`, `PACK-017`).
4. Missing or malformed `manifest.yaml` and YAML containing an unsafe executable tag raise `PackageManifestError`; no executable YAML constructor runs (`PACK-003`, `PACK-010`, `PACK-011`, `PACK-017`).
5. A mismatch between manifest type, identifier, or version and the package directory raises `PackageManifestError` (`PACK-015`, `PACK-017`).
6. Absolute, traversal, non-`.yaml`, missing, directory, or symlink-escaping entrypoints raise `PackageManifestError`, while a regular contained YAML entrypoint is accepted (`PACK-016`, `PACK-017`).
7. The named public imports work, manifest instances cannot be mutated, and loader failures preserve a useful underlying exception as `__cause__` without exposing it as the public exception type.
8. `pyproject.toml` reports version `0.2.0`, declares only Pydantic 2 and PyYAML as runtime dependencies, retains the existing development dependency group, and has a current committed lockfile.
9. README documents the versioned game-package layout, manifest boundary, and explicitly states that entrypoint content and dependency resolution are not implemented yet.

## Required verification

* Write and run the first valid-manifest behavioral test before adding manifest implementation; record the expected import or missing-boundary failure.
* Run focused tests after each meaningful behavior group is implemented.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires interpreting entrypoint content, resolving package dependencies, accepting a second manifest schema, adding another dependency, changing the public imports, weakening strict validation, allowing an entrypoint outside its package directory, or changing the accepted filesystem layout.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
