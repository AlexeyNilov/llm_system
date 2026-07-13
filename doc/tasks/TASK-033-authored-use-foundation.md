# TASK-033: Add the authored Use and boolean-world-fact foundation

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-003 through TASK-016, TASK-030

## Objective

Provide the smallest typed package and canonical-state foundation needed for a deterministic Greybridge reinforcement action: a reusable rule-pack Use mechanic, a concrete scenario binding, one strict boolean world fact, and atomic fact-state commitment.

This task makes the mechanic representable and commit-safe but does not resolve a Use proposal. TASK-034 will consume these accepted contracts.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Boolean world fact”, “Canonical world state”, “Object archetype definition”, “Object-use binding”, “Object-use mechanic definition”, “State change”, “Validated game packages”, and “Validated world state”
* `doc/requirements.md`: `PACK-009` through `PACK-028`, `RULE-001` through `RULE-008`, `SCHEMA-001` through `SCHEMA-004`, `STATE-001` through `STATE-045`, and `SCENARIO-009` through `SCENARIO-013`
* `doc/decisions.md`: “Separate the simulation kernel from game packages”, “Author game packages in YAML and validate with Pydantic”, “Represent state changes as self-verifying before-and-after deltas”, “Commit outcomes into one validated-world result”, and “Begin Use mechanics with bound boolean-world-fact effects”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/game_packages/rules.py`, `src/llm_system/game_packages/scenarios.py`, `src/llm_system/game_packages/validation.py`, `src/llm_system/game_packages/__init__.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/commitment.py`, `src/llm_system/simulation/__init__.py`, `tests/test_rule_pack_definition.py`, `tests/test_scenario_pack_definition.py`, `tests/test_game_package_validation.py`, `tests/test_runtime_state.py`, `tests/test_world_state_validation.py`, `tests/test_state_changes.py`, `tests/test_outcome_commitment.py`, `tests/test_greybridge_packages.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, `uv.lock`, and the four existing Greybridge `0.1.0` package files

Do not read postponed ideas, unrelated requirements or decisions, experiments, persistence, scheduling, randomness, perception, policies, prompts, other task briefs, or resolver implementations beyond what a task-local import or regression requires.

## Fixed assumptions

* Keep rule and scenario content `schema_version: 1`. New root catalogs default to immutable empty tuples so existing schema-version-1 package inputs remain structurally valid.
* Add public strict frozen `ObjectUseMechanicDefinition` with fields `id`, `name`, `object_archetype_id`, `target_type: Literal["location"]`, strictly positive integer `duration_seconds`, and `effect_type: Literal["set_boolean_world_fact"]`.
* Add `object_use_mechanics: tuple[ObjectUseMechanicDefinition, ...] = ()` to `RulePackDefinition`, preserving authored YAML order and using the same list-or-tuple normalization as existing catalogs.
* Add public strict frozen `BooleanWorldFactDefinition` with exactly `id`, `name`, and strict `initial_value: bool`.
* Add public strict frozen `ObjectUseBindingDefinition` with exactly `id`, `mechanic_id`, `object_id`, `target_location_id`, `fact_id`, and strict `fact_value: bool`.
* Add `boolean_world_facts: tuple[BooleanWorldFactDefinition, ...] = ()` and `object_use_bindings: tuple[ObjectUseBindingDefinition, ...] = ()` to `ScenarioPackDefinition`, preserving authored YAML order and normalizing only lists or tuples.
* All authored IDs use existing `RecordId`; all names use existing `NonBlankText`; strict booleans reject integers and strings; duration rejects booleans, zero, negative values, floats, and strings.
* Extend semantic validation in deterministic existing phase order. Index object-use mechanics after existing rule catalogs, boolean facts after graph namespaces, and bindings after entities. Preserve all existing issue ordering before new namespaces.
* Extend `ValidationIssueCode` with exact values `object-archetype-mismatch` and `ambiguous-use-binding`. Reuse `duplicate-id` and `unknown-reference` for duplicate catalog IDs and unresolved typed references.
* Validate every mechanic's `object_archetype_id` against the paired rule pack regardless of scenario dependency matching. Validate scenario binding `mechanic_id` and the resolved mechanic/object archetype agreement only when the package dependency matches, consistent with existing cross-package suppression.
* Every binding's `object_id` must resolve to exactly one `ObjectDefinition`; `target_location_id` to one location; and `fact_id` to one boolean fact. A uniquely resolved object must have the object archetype required by a uniquely resolved mechanic or emit `object-archetype-mismatch` at the binding's `object_id`.
* More than one binding with the same uniquely resolved `(object_id, target_location_id)` is invalid even when binding IDs differ. Emit `ambiguous-use-binding` at the later binding's `target_location_id` in encounter order. Suppress this dependent conclusion when either reference is absent or ambiguous. Do not require unique object-only, location-only, fact-only, or mechanic-only use.
* Structural package models defer uniqueness and reference validation to `validate_game_packages`; no model performs package lookup.
* Add public strict frozen `BooleanWorldFactState` with exactly `fact_id: AuthoredId` and strict `value: bool`.
* Add `boolean_world_facts: tuple[BooleanWorldFactState, ...] = ()` to `WorldState`; normalize JSON arrays to tuples with existing runtime collections and preserve current construction behavior for scenarios with no authored facts.
* World-state validation treats boolean facts as the fourth complete overlay after characters, objects, and connections. It reuses existing overlay issue codes, ordering, paths, and gating with collection path `boolean_world_facts` and identifier field `fact_id`.
* Add public `BooleanWorldFactChanged` with discriminator `change_type="boolean_world_fact"`, `fact_id`, strict boolean `from_value`, and strict boolean `to_value`; equal values are invalid.
* Add the fact delta to the closed `StateChange` union. Do not change existing variants or their parsing and behavior.
* Outcome commitment resolves facts against the runtime fact overlay. An absent target emits existing `unknown-change-target` at `outcome.state_changes[N].fact_id`; a known target whose value differs from `from_value` emits existing `before-value-mismatch` at `.from_value`. No after-reference check exists for a boolean.
* Valid commitment replaces only the matching fact's `value` at its existing tuple position, preserves unaffected record identities and tuple order, carries facts through every replacement `WorldState`, and reuses final world validation. Existing validation and application order remains exact with the fact variant placed after connection availability and before simulation time.
* Add Greybridge rule and scenario package directories at version `0.2.0`; preserve the existing `0.1.0` directories unchanged.
* `greybridge-rules/0.2.0` preserves all `0.1.0` catalogs and adds one mechanic: `id=reinforce-structure`, non-blank name, `object_archetype_id=reinforcement-materials`, `target_type=location`, `duration_seconds=300`, and `effect_type=set_boolean_world_fact`.
* `storm-at-greybridge/0.2.0` preserves all `0.1.0` topology and entities, pins `greybridge-rules` exactly at `0.2.0`, defines `bridge-reinforced` initially false, and binds `reinforce-structure` plus concrete `reinforcement-materials` at `greybridge-span` to `bridge-reinforced=true`.
* The real-package test targets and verifies `0.2.0`, while at least one focused compatibility assertion proves the retained `0.1.0` pair still loads and validates.
* Do not add package discovery, copying, migration, world initialization, resolver behavior, automatic initial-state construction, consumption, quantities, randomness, progression, flood effects, or a generic effects engine.
* This public contract milestone advances the project version from `0.31.0` to `0.32.0`; the lockfile's editable root-package version must match.

## In scope

* Add and publicly export the five definition, state, and change models and extend the three aggregate root contracts plus the `StateChange` union exactly as specified.
* Add package semantic validation for new namespaces, references, object-archetype agreement, and binding ambiguity.
* Add complete boolean-world-fact overlay validation and atomic outcome-commitment support.
* Add retained Greybridge `0.2.0` package files and update real-package tests and README examples to use them while preserving `0.1.0` compatibility.
* Add high-signal behavioral tests for strict parsing and immutability, defaults, YAML list normalization, semantic issue codes/paths/order/suppression, complete fact overlays, strict fact values, fact delta invariants, commitment success and atomic failure, identity/order preservation, serialization, and regressions of every extended closed union and aggregate.
* Update README with the authoring/runtime/commitment distinction and explicit exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Use resolution, dispatch changes, authorization changes, canonical-event changes, outcome changes, perception or witness feedback, narration, APIs, UI, persistence, or world initialization.
* Generic conditions, arbitrary facts, non-boolean values, formulas, expressions, callbacks, scripts, effect unions beyond the one literal, connection/character/object targets, requirements, checks, randomness, progression, skills, consumption, destruction, quantities, inventory capacity, or repeated-use policy.
* Flood scheduling or execution, connection availability changes caused by the fact, System director behavior, Help mechanics, NPC policies, LLM calls, or presentation.
* Deleting or modifying Greybridge `0.1.0`, changing content schema version, adding a dependency, or changing existing error meanings and behavior.
* Changes to requirements, decisions, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-033 status transition.

## Expected contracts and files

Likely production files are the named game-package and simulation modules in the context manifest. New focused tests may be added when that keeps existing test files readable. Greybridge `0.2.0` files belong beside retained `0.1.0` directories.

New public names are exactly `ObjectUseMechanicDefinition`, `BooleanWorldFactDefinition`, `ObjectUseBindingDefinition`, `BooleanWorldFactState`, and `BooleanWorldFactChanged`. Existing public package, state, validation, change, commitment, event, resolver, and perception contracts remain stable except for the explicitly additive aggregate fields and `StateChange` member.

## Acceptance criteria

1. Schema-version-1 rule and scenario packages parse strict immutable new catalogs, preserve authored order, and keep omitted new catalogs empty; existing packages remain compatible (`RULE-001` through `RULE-008`, `SCHEMA-001` through `SCHEMA-004`).
2. Semantic validation deterministically reports duplicate IDs, unresolved references, object-archetype mismatches, and ambiguous concrete object-location bindings with the accepted paths and suppression (`PACK-020` through `PACK-028`).
3. Runtime facts are strict, immutable, ordered, default-empty, and validated as a complete fourth authored overlay without changing existing overlay semantics (`STATE-001` through `STATE-037`).
4. `BooleanWorldFactChanged` is a strict self-verifying fifth `StateChange` variant and preserves every existing variant's behavior (`STATE-038` through `STATE-043`).
5. Outcome commitment validates and atomically applies fact changes with exact issue paths, position and identity preservation, fact propagation through other changes, and final world revalidation (`STATE-044`).
6. Greybridge `0.2.0` loads and validates with the exact accepted mechanic, fact, binding, 300-second duration, and exact package pin; retained `0.1.0` still loads and validates (`SCENARIO-009` through `SCENARIO-013`).
7. No Use proposal resolves, no object is consumed, no flood or progression consequence occurs, and no generic effects, conditions, or fact dictionary is introduced.
8. README and public exports accurately distinguish authored mechanic, scenario binding, canonical fact state, self-verifying delta, and atomic commitment.
9. Existing tests and public behavior remain green aside from fixtures intentionally extended for a scenario that now authors facts.
10. Project and installed metadata plus editable root `uv.lock` report `0.32.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before implementation logic; record genuine red evidence.
* Run the relevant focused package, state, validation, change, commitment, Greybridge, and package-version tests.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Verify installed metadata reports `0.32.0`.
* Verify `uv.lock` changes only the editable root-package version unless a concrete existing inconsistency is documented.
* `git diff --check`

Record every command and exact result in the handoff report. If a command cannot run, record the concrete reason rather than substituting silently.

## Stop conditions

Stop and report a design gap if implementation requires a resolver, a second effect or target kind, generic effect data, changing schema version, modifying Greybridge `0.1.0`, a new issue code beyond the two accepted values, different issue ordering or suppression, automatic world initialization, another state/change variant, a dependency, persistence, or any public behavior not fixed above.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
