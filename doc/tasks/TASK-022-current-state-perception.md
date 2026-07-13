# TASK-022: Project deterministic current-state perception

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-013, TASK-021

## Objective

Provide the first pure deterministic perception-engine operation: project one validated canonical world snapshot into the exact current-state observations available to one character under the accepted coarse spatial rules.

This task filters current state only. Canonical-event feedback, richer sensory mechanics, context enrichment, recording, cognition, and presentation remain separate boundaries.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Connection”, “Observation”, “Perception engine”, “Perceptual filtering”, “Perception snapshot”, and “Validated world state”
* `doc/requirements.md`: `SPACE-001` through `SPACE-007`, `KNOW-001`, `PERCEPTION-001` through `PERCEPTION-008`, `PERCEPTION-011` through `PERCEPTION-025`, and `LOOP-001`
* `doc/decisions.md`: “Model space as a location graph with deterministic perception”, “Separate truth, perception, memory, and belief”, “Begin perception with typed deterministic observation values”, and “Project current state before filtering event feedback”
* `doc/high_level_design.md`: “Perception engine”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/game_packages/entities.py`, `src/llm_system/game_packages/spatial.py`, `src/llm_system/simulation/_types.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/__init__.py`, `tests/test_world_state_validation.py`, `tests/test_perception_contracts.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* The public operation is `project_current_perception(world: ValidatedWorldState, observer_id: AuthoredId) -> PerceptionSnapshot`.
* The public `PerceptionObserverNotFoundError` subclasses `ValueError`. Its constructor accepts the supplied `AuthoredId`, stores public typed attribute `observer_id`, and supplies exact message `perception observer not found: {observer_id}`.
* Resolve the observer only in `world.state.characters`. Any identifier absent there, including an authored object identifier, raises `PerceptionObserverNotFoundError` before producing a snapshot.
* `ValidatedWorldState` already guarantees complete unique runtime overlays and valid package references. Do not call `validate_world_state`, add issue aggregates, or invent defensive branches for invariant-impossible missing runtime connection, character, or object records.
* Successful snapshot `perceived_at_seconds` and every observation `observed_at_seconds` equal `world.state.simulation_time_seconds`; every observation has `observer_id` equal to the requested observer and `source_type="current_state"`.
* Output starts with exactly one `LocationObserved` for the observer's current `location_id`.
* Next, traverse `world.packages.scenario_package.definition.spatial_graph.connections` in authored tuple order. Emit `ConnectionObserved` for every connection whose `source_location_id` equals the observer location, including unavailable connections, using the matching runtime connection state's exact `is_available`. Exclude connections that only terminate at the location.
* Next, traverse `world.packages.scenario_package.definition.entity_collection.entities` in authored tuple order. For each player or NPC character other than the observer, emit `CharacterObserved` when its matching runtime character state has the observer location. Exclude the observer and all characters elsewhere.
* Finally, traverse the same authored entity tuple in authored order. For each object, emit `ObjectObserved` with its exact runtime placement only when it is `ObjectAtLocation` at the observer location or `ObjectPossessedByCharacter` naming the observer. Exclude objects elsewhere and every object possessed by another character, including a co-located character.
* Group order is location, connections, characters, then objects. Runtime state tuple order must not affect output ordering.
* Output contains no `EventObserved`; the function accepts no canonical-event argument.
* Repeated calls for equal inputs return equal snapshots and do not mutate, copy, replace, or commit the validated world.
* Do not add concealment, hearing, line of sight, environmental facts, capability, condition, attention, confidence, salience, within-location geometry, names, descriptions, enrichment, recording, persistence, memory, belief, narration, LLM calls, randomness, configuration, protocols, registries, or service classes.
* No new dependency is required.
* This projection milestone advances the project version from `0.20.0` to `0.21.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact current-state projection and observer error, and expose both from `llm_system.simulation`.
* Add high-signal behavioral tests for the exact heterogeneous snapshot and canonical time, outgoing versus incoming connections, unavailable-connection inclusion, self and remote-character exclusion, direct and own-possession object inclusion, other-possession and remote-object exclusion, authored grouping/order despite deliberately different runtime tuple order, missing and object observer errors, determinism, and input immutability.
* Update README with the API, exact ordering and visibility rules, observer error, authored-order boundary, and explicit exclusions from events and richer perception or presentation behavior.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Event feedback or `EventObserved` production, pre-outcome state, event-location reconstruction, hearing, speech visibility, movement witness rules, or outcome processing.
* Observe action resolution, actor-action dispatch changes, narrator or NPC context assembly, restricted definition enrichment, prompts, LLM invocation, or UI/API work.
* Concealment, sensory traits, environmental state, conditions, attention, geometry, confidence, salience, randomness, or package-configurable perception mechanics.
* Observation identity or persistence, episodic memory, beliefs, retrieval, Qdrant, SQLite, or scheduler behavior.
* Changes to existing package, runtime-state, event, observation, snapshot, action, outcome, resolver, authorization, commitment, or dispatch contracts.
* Generic filtering frameworks, protocols, registries, service classes, caches, ID providers, logging, or new dependencies.
* Changes to governance documents, roadmap, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/perception_engine.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_current_state_perception.py`.

The two new public names are exactly `PerceptionObserverNotFoundError` and `project_current_perception`.

## Acceptance criteria

1. A known character observer receives the exact current-state snapshot at canonical time, grouped and ordered as location, authored outgoing connections, authored co-located other characters, and authored visible objects (`PERCEPTION-015`, `PERCEPTION-017` through `PERCEPTION-022`).
2. Projection includes unavailable outgoing connections with exact runtime availability and excludes incoming-only connections, independent of runtime connection tuple order (`PERCEPTION-019`, `PERCEPTION-022`).
3. Projection excludes the observer and remote characters while preserving authored entity order for co-located others, independent of runtime character tuple order (`PERCEPTION-020`, `PERCEPTION-022`).
4. Projection includes directly co-located objects and the observer's own possessions, excludes remote objects and every other character's possessions, and preserves authored entity order independent of runtime object tuple order (`PERCEPTION-013`, `PERCEPTION-021`, `PERCEPTION-022`).
5. An unknown identifier or object identifier raises the exact typed observer error and produces no snapshot (`PERCEPTION-016`).
6. Repeated projection is deterministic, preserves the exact immutable input world, trusts validated-world invariants, and emits no event observation or side effect (`PERCEPTION-023` through `PERCEPTION-025`).
7. Output contains only accepted ID-linked current-state fields without definition enrichment, scores, generated identities, or prose (`PERCEPTION-006`, `PERCEPTION-012`, `PERCEPTION-014`, `PERCEPTION-025`).
8. Public exports and README accurately describe current-state projection and its event-feedback boundary.
9. Existing package, world-validation, contract, resolver, dispatch, commitment, and authorization behavior remains unchanged.
10. Project and installed metadata plus editable root `uv.lock` report `0.21.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production projection logic; record the import or missing-contract failure.
* Run focused projection tests after full-snapshot, exclusion/error, and determinism groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.20.0` to `0.21.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires event visibility, a different observer namespace, a different ordering or object-visibility rule, richer sensory mechanics, enrichment, recording, persistence, memory or belief behavior, an Observe resolver, a dependency, or existing contract changes.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
