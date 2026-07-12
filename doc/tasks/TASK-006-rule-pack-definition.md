# TASK-006: Define rule-pack reference catalogs

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-005

## Objective

Add strict immutable rule-pack content models that give scenario archetype and decision-policy references explicit typed targets. The initial content root is a reference catalog only and must not invent mechanics, configuration, or executable behavior.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Archetype”, “Character archetype definition”, “Decision-policy definition”, “Decision-policy reference”, “Object archetype definition”, “Rule pack”, and “Rule-pack definition”
* `doc/requirements.md`: `PACK-006` through `PACK-011`, `RULE-001` through `RULE-006`, `ENTITY-003`, `ENTITY-004`, `ENTITY-006`, and `POLICY-001` through `POLICY-004`
* `doc/decisions.md`: “Author game packages in YAML and validate with Pydantic”, “Make NPC decision policies interchangeable”, and “Begin rule-pack content with typed reference catalogs”
* `doc/high_level_design.md`: “Principal records”, “Package loader and validator”, and “Testing strategy”
* `src/llm_system/game_packages/`, `tests/test_entity_definitions.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read the initial scenario, postponed ideas, unrelated requirements, or implementation roadmap beyond this task.

## Fixed assumptions

* `ObjectArchetypeDefinition` and `CharacterArchetypeDefinition` each contain exactly stable `id` and non-blank `name` fields.
* `DecisionPolicyDefinition` contains exactly stable `id`, non-blank `name`, and `policy_type: rule | llm | hybrid`.
* Policy definitions and `DecisionPolicyReference` reuse one internal policy-type constraint; their allowed values must not be duplicated independently.
* `RulePackDefinition` contains exactly strict integer `schema_version: 1`, `object_archetypes`, `character_archetypes`, and `decision_policies`.
* Each root catalog accepts YAML-style lists or tuple inputs, stores an immutable ordered tuple, and may be empty.
* Every model is strict, frozen, and forbids unknown fields. YAML lists may be normalized to tuples without enabling scalar coercion. Boolean or string schema versions are invalid.
* Duplicate IDs, scenario-reference resolution, policy implementation lookup, and all mechanics are deferred to later semantic validation and rule-schema tasks.
* No new dependency or dependency-version change is authorized. The lockfile's editable root-package version must track the project version.
* This new public contract advances the project version from `0.4.0` to `0.5.0`.

## In scope

* Add the three catalog-record definitions and `RulePackDefinition` within `llm_system.game_packages` using existing shared constraints and strict Pydantic conventions.
* Move the shared policy-type annotation from entity implementation into the existing private constrained-types module and use it for both policy references and definitions.
* Normalize only YAML list representation for the three root catalogs into immutable ordered tuples.
* Export `ObjectArchetypeDefinition`, `CharacterArchetypeDefinition`, `DecisionPolicyDefinition`, and `RulePackDefinition` from `llm_system.game_packages`.
* Add focused behavioral tests for valid records, all policy types, strict schema version, strict fields, empty catalogs, authored order, deep immutability, and deliberate duplicate-ID deferral.
* Update project version, root lockfile metadata, package-version test, and README public-contract documentation.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Rule entrypoint YAML loading or changes to `load_package_manifest`.
* Scenario content roots, cross-record or cross-package resolution, duplicate detection, or implementation-registry lookup.
* Actions, abilities, skills, attributes, effects, checks, progression, policy settings, behavior priorities, defaults, overrides, or executable policy logic.
* Generic property dictionaries, tags, inheritance, composition, dependencies, or multiple content schema versions.
* Changes to existing manifest, spatial, entity, placement, or NPC motivation behavior.
* Changes to governance documents, roadmap, glossary, scenario, ideas, experiments, or agent configuration.

## Expected contracts and files

New public imports from `llm_system.game_packages` are:

```python
from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    DecisionPolicyDefinition,
    ObjectArchetypeDefinition,
    RulePackDefinition,
)
```

The models may live in `src/llm_system/game_packages/rules.py`. Existing private constrained types may be extended only for genuinely shared lexical constraints. Existing public imports and validation behavior must remain compatible.

## Acceptance criteria

1. Valid object and character archetype definitions preserve stable IDs and non-blank names, reject coercion and unknown fields, and are immutable (`PACK-009`, `PACK-010`, `RULE-002`).
2. Valid policy definitions accept each of `rule`, `llm`, and `hybrid`, preserve stable ID and name, reject invalid policy types and unknown fields, and are immutable (`RULE-003`, `POLICY-001` through `POLICY-004`).
3. Policy definitions and NPC policy references use one shared internal policy-type annotation, with all existing entity tests remaining unchanged and passing.
4. A rule-pack root accepts strict integer schema version `1` and YAML-style catalogs, stores all catalogs as tuples in authored order, and is deeply immutable (`RULE-001`, `RULE-004`).
5. Empty catalogs and duplicate IDs within or across typed catalogs remain representable at this structural boundary, proving uniqueness remains assigned to `RULE-005`.
6. Unsupported, boolean, string, or missing schema versions; scalar, string, or mapping catalog values; invalid IDs; blank names; and unknown fields fail strict validation (`PACK-010`, `RULE-001` through `RULE-004`).
7. All four named public imports work and every existing manifest, spatial, and entity test remains passing without behavior changes.
8. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.5.0`; dependencies and all resolved dependency versions remain unchanged.
9. README documents the three catalogs, schema version, definition-versus-implementation boundary, and explicit absence of mechanics, content loading, uniqueness validation, and policy execution.

## Required verification

* Write and run the first rule-pack-model behavioral test before adding any rule implementation; record the expected import failure.
* Run focused rule-pack tests after each meaningful behavior group.
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.4.0` to `0.5.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede implementation; do not remove or break existing implementation afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires adding a dependency, adding a catalog or record field, loading YAML, resolving references, checking uniqueness, introducing mechanics or policy behavior, weakening strictness or immutability, changing existing public behavior, or changing the content schema version.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented strict immutable rule-pack reference catalogs and public exports.

**Changed files:** `README.md`, `pyproject.toml`, `uv.lock`, `src/llm_system/game_packages/__init__.py`, `src/llm_system/game_packages/_types.py`, `src/llm_system/game_packages/entities.py`, `src/llm_system/game_packages/rules.py`, `tests/test_package.py`, and `tests/test_rule_pack_definition.py`.

**Verification:** Initial red state: `uv run pytest tests/test_rule_pack_definition.py` failed during collection with `ImportError` for `CharacterArchetypeDefinition`, before rule implementation. Final: focused rule-pack tests (18 passed); `make format`; `make lint`; `make mypy`; `make test` (73 passed); `make check`; `uv lock --check`; and `git diff --check` all passed. Confirmed the only `uv.lock` diff is editable `llm-system` version `0.4.0` to `0.5.0`.

**Deviations:** None.

**Design gaps or follow-ups:** Semantic duplicate-ID validation, package entrypoint loading, reference resolution, policy implementation lookup, and mechanics remain intentionally deferred.

## Integrator review

**Disposition:** Accepted.

The integrator independently confirmed the strict catalog records, shared policy-type vocabulary, schema-version guard, ordered immutable root, public exports, and absence of mechanics or loading behavior. Review added a valid all-empty-root case and separated invalid-ID from blank-name evidence so either constraint cannot mask the other. `uv sync --locked`, `make format`, `make check`, `uv lock --check`, and `git diff --check` succeeded on Python 3.12.3; the final suite contains 75 passing tests. The only lockfile change is the editable root package version from `0.4.0` to `0.5.0`.
