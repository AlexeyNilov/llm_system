# TASK-005: Define immutable scenario entities

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-004

## Objective

Add strict immutable package-domain models for objects, player characters, NPC characters, object placement, NPC motivation context, decision-policy references, and the ordered entity collection. Structural models must make invalid variant combinations unrepresentable while leaving cross-record and cross-package resolution to the next validation task.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Archetype”, “Character”, “Character definition”, “Decision policy”, “Decision-policy reference”, “Entity”, “Entity definition”, “Goal”, “Goal definition”, “NPC”, “Object definition”, “Object placement”, and “Player”
* `doc/requirements.md`: `PACK-009`, `PACK-010`, `ENTITY-001` through `ENTITY-009`, `NPC-002`, `POLICY-001` through `POLICY-006`, and `LOOP-007`
* `doc/decisions.md`: “Make NPC decision policies interchangeable” and “Model scenario inhabitants as discriminated entity definitions”
* `doc/high_level_design.md`: “Principal records”, “Actor runtime”, and “Testing strategy”
* `src/llm_system/game_packages/`, `tests/test_spatial_definitions.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read the initial scenario, postponed ideas, unrelated requirements, or implementation roadmap beyond this task.

## Fixed assumptions

* `EntityDefinition` is the discriminated union of `ObjectDefinition`, `PlayerCharacterDefinition`, and `NpcCharacterDefinition`, selected by `entity_type: object | player_character | npc_character`.
* `CharacterDefinition` is the union of the player and NPC variants.
* All entity variants contain exactly a stable record `id` and non-blank `name` plus their variant-specific fields.
* `ObjectDefinition` requires `object_archetype_id` and one discriminated `initial_placement`.
* `LocationPlacementDefinition` has `placement_type: location` and `location_id`; `PossessedPlacementDefinition` has `placement_type: possessed` and `character_id`. The union forbids ambiguous or mixed placement fields.
* Both character variants require `character_archetype_id` and `initial_location_id`.
* `PlayerCharacterDefinition` has no NPC-only fields.
* `NpcCharacterDefinition` requires non-blank `identity_summary`, a non-empty ordered tuple of `GoalDefinition`, optional non-blank `initial_plan`, and one `DecisionPolicyReference`.
* `GoalDefinition` has exactly a stable `id` and non-blank `description`. Goal tuple order expresses priority; there is no numeric priority.
* `DecisionPolicyReference` has exactly `policy_type: rule | llm | hybrid` and stable `policy_id`; it does not embed configuration or executable logic.
* `EntityCollectionDefinition` accepts YAML-style entity lists or tuple inputs and stores an immutable ordered tuple.
* Every model is strict, frozen, and forbids unknown fields. YAML lists may be normalized to tuples without enabling scalar coercion.
* This task performs no identifier uniqueness, player-count, location, possession, archetype, or policy-reference validation. Forward and backward references are structurally equivalent.
* No new dependency or dependency-version change is authorized. The lockfile's editable root-package version must track the project version.
* This new public contract advances the project version from `0.3.0` to `0.4.0`.

## In scope

* Add the fixed entity, character, placement, goal, policy-reference, and collection models within `llm_system.game_packages` using existing constrained types and strict Pydantic conventions.
* Reuse shared internal record-ID and non-blank-string constraints from the spatial models by moving them to a focused private module if necessary; do not duplicate validators.
* Normalize only YAML list representation for NPC goals and the entity collection into immutable ordered tuples.
* Export the concrete models, union aliases, placement models and alias, goal model, policy reference, and collection from `llm_system.game_packages`.
* Add focused behavioral tests for discriminated parsing, exact variant fields, placement exclusivity, strict scalar behavior, deep immutability, authored order, and deliberate deferral of semantic references.
* Update project version, root lockfile metadata, package-version test, and README public-contract documentation.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Scenario entrypoint loading or changes to `load_package_manifest`.
* Cross-record or cross-package validation, exactly-one-player enforcement, archetype or policy registries, or actual policy behavior.
* Runtime entity, character, location, possession, inventory, goal, plan, condition, or perception state.
* Nested containers, unplaced objects, quantities, stacks, equipment, free-form perceptual descriptions, generic tags or properties, policy configuration, or executable rules.
* Changes to spatial definition behavior or TASK-003 manifest loading.
* Changes to governance documents, roadmap, glossary, scenario, ideas, experiments, or agent configuration.

## Expected contracts and files

New public imports from `llm_system.game_packages` are:

```python
from llm_system.game_packages import (
    CharacterDefinition,
    DecisionPolicyReference,
    EntityCollectionDefinition,
    EntityDefinition,
    GoalDefinition,
    LocationPlacementDefinition,
    NpcCharacterDefinition,
    ObjectDefinition,
    ObjectPlacementDefinition,
    PlayerCharacterDefinition,
    PossessedPlacementDefinition,
)
```

The models may live in `src/llm_system/game_packages/entities.py`, with genuinely shared constrained types moved to a private module such as `_types.py`. Type unions must remain usable as Pydantic field annotations and through `TypeAdapter`; they are not required to be runtime base classes.

## Acceptance criteria

1. Each of the three valid entity variants parses through the discriminated `EntityDefinition` union and rejects fields belonging to another variant (`ENTITY-001`, `ENTITY-002`, `ENTITY-005`).
2. Location and possessed placements parse into the correct frozen variant; absolute meaning is expressed by exactly one location or character reference, and mixed, missing, unknown, or coerced fields fail (`ENTITY-003`).
3. Objects require stable object-archetype references and exactly one placement; characters require stable character-archetype and initial-location references (`ENTITY-003`, `ENTITY-004`).
4. Player definitions reject NPC-only identity, goal, plan, and policy fields (`ENTITY-005`, `LOOP-007`).
5. NPC definitions require a non-blank identity summary, at least one immutable goal, an optional plan that is non-blank when present, and one valid rule, LLM, or hybrid policy reference (`ENTITY-006`, `POLICY-001` through `POLICY-004`).
6. Goal and entity YAML lists become tuples without reordering; every concrete model, nested model, tuple, and contained definition is immutable (`ENTITY-006`, `ENTITY-007`).
7. Structurally valid duplicate IDs, multiple or absent players, dangling location or possession IDs, and unresolved archetype or policy IDs remain representable at this model-only boundary, proving semantic validation remains assigned to `ENTITY-008`.
8. Invalid IDs, blank required text, scalar coercion, unknown fields, invalid discriminator values, and scalar, string, or mapping collection inputs fail strict validation.
9. All named public imports work and all existing manifest and spatial tests remain passing without behavior changes.
10. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.4.0`; dependencies and all resolved dependency versions remain unchanged.
11. README documents the entity variants, single-source object placement, archetype and policy references, NPC motivation fields, definition-versus-state boundary, and deferred semantic validation.

## Required verification

* Write and run the first entity-model behavioral test before adding any entity implementation; record the expected import failure.
* Run focused entity tests after each meaningful behavior group.
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.3.0` to `0.4.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires adding a dependency, adding or removing a field, changing a discriminator, loading entity YAML independently, resolving references, adding runtime state, weakening immutability or strictness, changing existing public behavior, or permitting ambiguous object placement.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Ready for review

**Changed files:** `README.md`; `pyproject.toml`; `uv.lock`; `src/llm_system/game_packages/_types.py`; `src/llm_system/game_packages/entities.py`; `src/llm_system/game_packages/spatial.py`; `src/llm_system/game_packages/__init__.py`; `tests/test_entity_definitions.py`; `tests/test_package.py`; and this task record.

**Verification:** Initial red state: `uv run pytest tests/test_entity_definitions.py` failed during collection with `ImportError: cannot import name 'DecisionPolicyReference'`. Final: focused entity tests (10 passed); `make format`; `make lint`; `make mypy`; `make test` (45 passed); `make check` (45 passed); `uv lock --check`; and `git diff --check` all passed. `uv.lock` differs only in the editable root-package version from `0.3.0` to `0.4.0`.

**Deviations:** None.

**Design gaps or follow-ups:** Semantic entity validation remains intentionally deferred: identifier uniqueness, player count, and all referenced-record resolution.

## Integrator review

**Disposition:** Accepted.

The integrator independently inspected the entity, character, placement, goal, policy-reference, union, and collection contracts. Review added focused coverage for the public `CharacterDefinition` union, invalid discriminators, required NPC goals, blank plans, all supported policy types, and deliberately unresolved possession, goal, archetype, location, and policy references. One avoidable test type suppression was removed, and the shared internal strict-model base was renamed so auxiliary records are not mislabeled as entities. `uv sync --locked`, `make format`, `make check`, `uv lock --check`, and `git diff --check` succeeded on Python 3.12.3; the final suite contains 55 passing tests. The only lockfile change is the editable root package version from `0.3.0` to `0.4.0`.
