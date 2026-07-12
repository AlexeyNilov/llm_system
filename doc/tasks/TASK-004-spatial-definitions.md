# TASK-004: Define immutable spatial topology

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-003

## Objective

Add strict immutable package-domain models for authored location nodes, directed connection edges, and their ordered spatial-graph container. These structural definitions must preserve the boundary between package topology and future mutable canonical state without performing semantic graph validation prematurely.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Connection”, “Connection definition”, “Location”, “Location definition”, “Spatial graph definition”, and “Simulation time”
* `doc/requirements.md`: `PACK-009`, `PACK-010`, and `SPACE-001` through `SPACE-014`
* `doc/decisions.md`: “Model space as a location graph with deterministic perception” and “Separate authored spatial definitions from runtime state”
* `doc/high_level_design.md`: “Principal records”, “Package loader and validator”, and “Testing strategy”
* `src/llm_system/game_packages/`, `tests/test_game_packages.py`, `tests/test_package.py`, `pyproject.toml`, and `README.md`

Do not read the initial scenario, postponed ideas, unrelated requirements, or implementation roadmap beyond this task.

## Fixed assumptions

* `LocationDefinition` has exactly `id` and `name`.
* `ConnectionDefinition` has exactly `id`, `name`, `source_location_id`, `destination_location_id`, and `base_traversal_seconds`.
* All record identifiers use the same lowercase kebab-case lexical constraint as package identifiers but remain semantically record identifiers.
* Names must be strings containing at least one non-whitespace character.
* `base_traversal_seconds` is a strict positive integer; booleans, floats, numeric strings, zero, and negative values are invalid.
* Every connection is directed. Reverse travel requires a separate definition; there is no bidirectional flag or implicit edge expansion.
* `SpatialGraphDefinition` has exactly ordered `locations` and `connections` collections. It accepts YAML-style lists at validation and stores immutable tuples without reordering.
* All three definitions and their nested contents are frozen and forbid unknown fields.
* Duplicate identifiers, missing endpoint references, self-loops, parallel-edge policy, reachability, and other graph semantics are not validated by these structural models. `SPACE-014` belongs to the later graph-validation task.
* Runtime state, coordinates, descriptions, features, requirements, visibility, and availability are outside this schema.
* No new dependency is authorized.
* This new public contract advances the project version from `0.2.0` to `0.3.0`.

## In scope

* Add the three spatial definition models within `llm_system.game_packages` using the existing strict Pydantic conventions.
* Reuse one internal record-identifier constraint rather than duplicating location and connection regexes.
* Normalize only YAML list representation into immutable ordered tuples; do not enable general scalar coercion.
* Export `LocationDefinition`, `ConnectionDefinition`, and `SpatialGraphDefinition` from `llm_system.game_packages`.
* Add focused behavioral tests for valid models, ordering, immutability, strict field validation, and the deliberate absence of semantic graph validation.
* Update the project version, package-version test, and README public-contract documentation.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* A spatial-fragment YAML loader or changes to `load_package_manifest`.
* Scenario entrypoint, entity, character, runtime-state, action, perception, or persistence models.
* Identifier uniqueness, endpoint existence, self-loop, parallel-edge, reachability, or connectivity validation.
* Pathfinding, movement resolution, duration arithmetic, bidirectional expansion, or graph-library dependencies.
* Free-form location descriptions, coordinates, tags, features, requirements, visibility, availability, damage, or environmental state.
* Changes to governance documents, roadmap, glossary, scenario, ideas, experiments, or agent configuration.

## Expected contracts and files

The new public import boundary is:

```python
from llm_system.game_packages import (
    ConnectionDefinition,
    LocationDefinition,
    SpatialGraphDefinition,
)
```

The models may live in a new focused module such as `src/llm_system/game_packages/spatial.py`. A small internal constrained-type module is permitted if it removes real duplication without expanding the public API. Existing TASK-003 public imports and behavior must remain compatible.

## Acceptance criteria

1. A valid location definition accepts a lowercase kebab-case identifier and non-blank name, rejects unknown fields, and is immutable (`PACK-009`, `PACK-010`, `SPACE-008`, `SPACE-009`).
2. A valid connection definition preserves its explicit ID, name, source, destination, and positive integer-second duration, rejects unknown or coerced fields, and is immutable (`PACK-009`, `PACK-010`, `SPACE-010`, `SPACE-011`).
3. A spatial graph accepts YAML-style ordered lists, stores both collections as tuples in authored order, and cannot be mutated through either the container or nested definitions (`SPACE-008`, `SPACE-012`).
4. Invalid identifiers, blank names, boolean or non-integer durations, and scalar, string, or mapping collection inputs fail strict validation without introducing another dependency. Tuple inputs may remain tuples; YAML list inputs are the only representation normalized by this task.
5. Structurally valid duplicate IDs, dangling endpoint IDs, self-loops, and parallel directed edges can be represented at this model-only boundary, demonstrating that semantic graph checks remain assigned to the later validator (`SPACE-014`).
6. The three named public imports work while all TASK-003 imports and manifest-loading tests remain unchanged and passing.
7. `pyproject.toml` and installed distribution metadata report `0.3.0`; dependencies and the lockfile do not change.
8. README documents the node/edge mapping, directed reverse-edge rule, integer-second duration, and definition-versus-state boundary without claiming graph validation or scenario content loading exists.

## Required verification

* Write and run the first spatial-model behavioral test before adding any spatial implementation; record the expected import failure.
* Run focused spatial tests after each meaningful behavior group.
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm `uv.lock` is unchanged from the task baseline.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires adding a dependency, loading spatial YAML independently, performing semantic graph validation, adding a field, accepting mutable collections, changing the public names, changing TASK-003 behavior, or introducing runtime-state meaning into package definitions.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
