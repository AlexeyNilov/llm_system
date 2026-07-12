# TASK-007: Define the scenario-pack content root

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-006

## Objective

Add one strict immutable scenario-pack content root that composes the existing spatial graph and entity collection definitions. This establishes the typed scenario entrypoint contract without introducing loading, relational validation, scheduled activity, director hooks, objectives, or mechanics.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Entity”, “Entity definition”, “Game package”, “Scenario pack”, and “Spatial graph definition”
* `doc/requirements.md`: `PACK-002`, `PACK-003`, `PACK-006` through `PACK-011`, `SPACE-008`, and `ENTITY-001`
* `doc/decisions.md`: “Author game packages in YAML and validate with Pydantic”, “Separate authored spatial definitions from runtime state”, and “Model scenario inhabitants as discriminated entity definitions”
* `doc/high_level_design.md`: “Package loader and validator”, “Information architecture”, “Principal records”, and “Testing strategy”
* `src/llm_system/game_packages/`, `tests/test_spatial_definitions.py`, `tests/test_entity_definitions.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read the initial scenario, postponed ideas, unrelated requirements, or implementation roadmap beyond this task.

## Fixed assumptions

* `ScenarioPackDefinition` contains exactly `schema_version`, `spatial_graph`, and `entity_collection`.
* The content schema version is strict integer `1`; boolean and string representations are invalid.
* `spatial_graph` is a required `SpatialGraphDefinition` and `entity_collection` is a required `EntityCollectionDefinition`.
* The explicit authored shape is `spatial_graph: {locations: ..., connections: ...}` and `entity_collection: {entities: ...}`. Do not flatten these aggregates or add input aliases.
* Both aggregates may contain empty collections. Structural validity does not imply that a scenario is playable.
* The root is strict, frozen, forbids unknown fields, and is deeply immutable through its existing immutable nested definitions.
* Connection endpoints, placements, possession targets, archetype references, policy references, uniqueness, graph invariants, and player-count requirements are deferred to later semantic validation.
* No new dependency or dependency-version change is authorized. The lockfile's editable root-package version must track the project version.
* This new public contract advances the project version from `0.5.0` to `0.6.0`.

## In scope

* Add `ScenarioPackDefinition` within `llm_system.game_packages` by composing the existing spatial and entity aggregate definitions.
* Export `ScenarioPackDefinition` from `llm_system.game_packages`.
* Add focused behavioral tests for valid nested parsing, required sections, strict schema version and fields, empty aggregates, deep immutability, and deliberate relational-validation deferral.
* Update project version, root lockfile metadata, package-version test, and README public-contract documentation.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* YAML entrypoint loading or changes to `load_package_manifest`.
* Cross-record, graph, cross-package, reference, uniqueness, or playable-scenario validation.
* Scheduled activities, System director hooks, objectives, scenario pressures, mutable state, runtime behavior, or mechanics.
* Changes to existing manifest, spatial, entity, placement, rule-pack, or policy behavior.
* Generic mappings, extensions, includes, defaults, aliases, multiple content schema versions, or convenience input shapes.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, or agent configuration.

## Expected contracts and files

The new public import is:

```python
from llm_system.game_packages import ScenarioPackDefinition
```

The model may live in `src/llm_system/game_packages/scenarios.py`. Existing public imports and validation behavior must remain compatible.

The authored and runtime boundary is equivalent to:

```yaml
schema_version: 1
spatial_graph:
  locations: []
  connections: []
entity_collection:
  entities: []
```

## Acceptance criteria

1. A scenario-pack root accepts strict integer schema version `1` plus valid spatial-graph and entity-collection mappings, and exposes those sections through their existing typed aggregate models (`PACK-002`, `PACK-010`, `SPACE-008`, `ENTITY-001`).
2. The root is immutable, its nested definitions remain immutable, and unknown root fields are rejected (`PACK-010`).
3. Empty location, connection, and entity collections are structurally valid, demonstrating that playability is not enforced by this model.
4. Unsupported, boolean, string, or missing schema versions; missing aggregate sections; malformed aggregate values; and unknown fields fail strict validation (`PACK-010`).
5. Structurally valid unresolved connection endpoints, entity placements, archetype references, and policy references remain representable, proving contextual validation is still assigned to the later semantic-validation layer (`PACK-003`, `PACK-011`).
6. The named public import works and all existing manifest, spatial, entity, and rule-pack tests remain passing without behavior changes.
7. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.6.0`; dependencies and all resolved dependency versions remain unchanged.
8. README documents the scenario root's two explicit aggregate sections, content schema version, and deliberate absence of loading, relational validation, events, hooks, objectives, and mechanics.

## Required verification

* Write and run the first scenario-root behavioral test before adding implementation; record the expected import failure.
* Run focused scenario-root tests after each meaningful behavior group.
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.5.0` to `0.6.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires adding a root field, changing either nested aggregate contract, adding a dependency, loading YAML, resolving references, checking graph or scenario semantics, introducing events or mechanics, weakening strictness or immutability, changing existing public behavior, or changing the content schema version.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented `ScenarioPackDefinition` as the strict frozen content-schema-version-1 scenario root, with typed spatial and entity aggregates.

**Changed files:** `src/llm_system/game_packages/scenarios.py`; `src/llm_system/game_packages/__init__.py`; `tests/test_scenario_pack_definition.py`; `tests/test_package.py`; `pyproject.toml`; `uv.lock`; `README.md`; this task record.

**Verification:** Initial red state: `uv run pytest tests/test_scenario_pack_definition.py` failed during collection with `ImportError: cannot import name 'ScenarioPackDefinition'`. Final: focused contract and compatible existing-definition tests passed (67); `make format`, `make lint`, `make mypy`, `make test`, `make check`, `uv lock --check`, and `git diff --check` passed. Installed distribution metadata reports `0.6.0`. The only `uv.lock` diff is the editable root package version (`0.5.0` to `0.6.0`).

**Deviations:** None.

**Design gaps or follow-ups:** None.

## Integrator review

**Disposition:** Accepted.

The integrator independently confirmed the strict content schema version, explicit spatial-graph and entity-collection composition, deep immutability, public export, and deliberate absence of entrypoint loading and relational validation. The structural deferral evidence covers unresolved connection endpoints, placements, archetypes, locations, and policies without weakening the nested models. `make format`, `make lint`, `make mypy`, `make test`, `make check`, `uv lock --check`, and `git diff --check` succeeded on Python 3.12.3; the final suite contains 90 passing tests. The only lockfile change is the editable root package version from `0.5.0` to `0.6.0`.
