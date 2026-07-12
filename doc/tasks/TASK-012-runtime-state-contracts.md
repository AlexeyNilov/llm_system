# TASK-012: Define canonical runtime-state structural contracts

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-011

## Objective

Provide strict immutable public contracts for the minimal changing facts in one canonical runtime-state snapshot: simulation time, character locations, object placement or possession, and connection availability.

These models are ID-linked overlays on immutable package definitions. This task establishes structural validity only and does not claim that a snapshot is complete, relationally valid, or ready for simulation resolution.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Canonical”, “Canonical world state”, “Character”, “Connection definition”, “Entity”, “Location definition”, “Object”, “Scenario-pack definition”, and “Simulation kernel”
* `doc/requirements.md`: `STATE-001` through `STATE-004`, `STATE-007` through `STATE-009`, `STATE-012`, and `STATE-014` through `STATE-020`
* `doc/decisions.md`: “Separate authored spatial definitions from runtime state”, “Model runtime state as an ID-linked mutable-facts overlay”, “Store canonical runtime collections as ordered immutable tuples”, “Begin runtime state with exact placement and availability variants”, and “Separate runtime-state structure from world-readiness validation”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/simulation/`, `src/llm_system/game_packages/_types.py`, `src/llm_system/game_packages/entities.py`, `tests/test_actions.py`, `tests/test_entity_definitions.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, completed task briefs, experiments, or implementation roadmap beyond this task.

## Fixed assumptions

* All new contracts are strict, frozen Pydantic 2 models that forbid unknown fields and contain no mutable collection fields or nondeterministic defaults.
* `CharacterState` contains exactly `character_id` and `location_id` authored-domain identifiers.
* `ObjectAtLocation` has placement discriminator `location` and contains exactly `location_id` in addition to that discriminator.
* `ObjectPossessedByCharacter` has placement discriminator `possessed_by_character` and contains exactly `character_id` in addition to that discriminator.
* `ObjectPlacement` is a closed discriminated union of exactly `ObjectAtLocation` and `ObjectPossessedByCharacter`.
* `ObjectState` contains exactly `object_id` and one `ObjectPlacement`.
* `ConnectionState` contains exactly `connection_id` and strict boolean `is_available`.
* `WorldState` contains exactly non-negative integer `simulation_time_seconds`, `characters: tuple[CharacterState, ...]`, `objects: tuple[ObjectState, ...]`, and `connections: tuple[ConnectionState, ...]`.
* All fields are required. Structural collections may be empty and may contain duplicate or unresolved identifiers because relational world-readiness validation belongs to the next task.
* Runtime state does not copy names, topology, traversal duration, archetypes, goals, initial plans, package identities, or persistent world identity.
* There is no unplaced, destroyed, consumed, hidden, quantity, condition, nested-container, inventory-list, or activity state.
* Object placement is exact and exclusive; an object cannot structurally have both a location and possessor or neither.
* Authored references use the same lowercase kebab-case behavior as existing package and action contracts.
* If implementation would otherwise duplicate the private authored-ID constraint now used inside `simulation.actions`, it may move that private alias and shared strict-model base into a private `llm_system.simulation` helper module without changing public action behavior or exporting those helpers.
* No state mutation, lookup helpers, derived indexes, initialization, state replacement, package traversal, semantic validation, or persistence is implemented.
* No new dependency is required.
* This public contract milestone advances the project version from `0.10.0` to `0.11.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact character, object-placement, object, connection, and world snapshot structural contracts.
* Expose the intended contracts through the public `llm_system.simulation` package boundary.
* Add behavioral tests covering exact valid structure, discriminator behavior, strict scalar types, identifier constraints, exclusive object placement, tuple normalization from JSON, immutability, forbidden unknown fields, and deliberate absence of relational validation.
* Preserve all TASK-011 action-contract behavior if private common model constraints are refactored.
* Update README with the runtime overlay boundary, a concise construction example, and the explicit statement that structural state is not world-ready state.
* Update project version, root lockfile metadata, package-version test, and this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* World-readiness validation, completeness, uniqueness, package lookup, reference resolution, or proof that state matches one `ValidatedGamePackages` pair.
* Action outcomes, state changes, canonical events, simulation arbiter, operation resolvers, authorization, randomness, clock behavior, scheduling, perception, persistence, APIs, or UI.
* World construction from a scenario package or default connection availability.
* Runtime names, topology, traversal duration, archetypes, goals, plans, package versions, or persistent world identity.
* Any unplaced-object or lifecycle state, conditions, quantities, nested containment, inventory collections, activities, skills, objectives, bridge facts, or Greybridge-specific mechanics.
* Public mapping/index APIs, mutation methods, setters, builders, repositories, or generic property dictionaries.
* Changes to game-package schemas or public action-contract behavior.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production is `src/llm_system/simulation/state.py`. A private `simulation/_types.py` may share strict-model and authored-ID constraints within the simulation package. These concepts must be directly importable from `llm_system.simulation`: `CharacterState`, `ObjectAtLocation`, `ObjectPossessedByCharacter`, `ObjectPlacement`, `ObjectState`, `ConnectionState`, and `WorldState`.

Likely tests belong in `tests/test_runtime_state.py`; inspect current naming patterns before choosing the exact file.

## Acceptance criteria

1. Character, object, and connection state contain only their accepted changing facts and authored-domain identifiers (`STATE-007`, `STATE-016` through `STATE-018`).
2. `ObjectPlacement` discriminates exactly location and possessing-character variants, rejects both/neither representations, and exposes no unplaced variant (`STATE-017`, `STATE-020`).
3. `WorldState` requires non-negative strict integer simulation seconds and required immutable ordered tuple collections (`STATE-014`, `STATE-015`, `STATE-019`).
4. Runtime models reject unknown fields, mutable assignment, invalid identifier shapes, boolean or floating-point time, non-boolean availability, and invalid placement discriminators (`STATE-004`, `STATE-018`, `STATE-019`).
5. Valid JSON arrays deserialize into tuple collections and serialize deterministically as JSON arrays without exposing mutable dictionaries or generated values (`STATE-014`, `STATE-015`).
6. Structural construction permits empty collections, duplicate record IDs, and unresolved but well-shaped references, proving package-dependent validation is absent (`STATE-012`).
7. Public imports and README explain that runtime state is a minimal ID-linked overlay, not copied package data or proof of world readiness (`STATE-007` through `STATE-009`).
8. Existing action and game-package behavior remains unchanged, including strict actor-action JSON ingestion.
9. Project and installed metadata plus the editable root in `uv.lock` report `0.11.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production runtime-state logic; record the import or missing-contract failure.
* Run focused runtime-state tests after each meaningful contract group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.10.0` to `0.11.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede production contract creation; do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires package-aware validation, world initialization, implicit defaults, changing accepted state fields or placement variants, lifecycle or condition state, mutation or lookup behavior, public action-contract changes, a dependency, or generic mappings.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
