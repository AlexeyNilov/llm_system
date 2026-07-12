# TASK-010: Author the Greybridge package foundation

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default scenario author

**Role:** Scenario author

**Agent:** Default

**Depends on:** TASK-009

## Objective

Author the first real rule-and-scenario package pair as a relationally valid Greybridge content foundation. The repository files must exercise complete package loading and semantic validation while containing only concepts supported by the current strict schemas.

This task does not make Greybridge playable. It establishes inspectable package identities, topology, cast, objects, placements, motivations, and policy references for later mechanics and kernel tasks.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/glossary.md`: “Character archetype definition”, “Decision-policy definition”, “Game package”, “Loaded game package”, “Object archetype definition”, “Rule pack”, “Scenario pack”, and “Validated game packages”
* `doc/requirements.md`: `PACK-007` through `PACK-026`, `RULE-001` through `RULE-006`, `SPACE-008` through `SPACE-014`, `ENTITY-001` through `ENTITY-009`, and `SCENARIO-001` through `SCENARIO-012`
* `doc/decisions.md`: “Use self-contained exact-version game package manifests”, “Separate authored spatial definitions from runtime state”, “Model scenario inhabitants as discriminated entity definitions”, “Begin rule-pack content with typed reference catalogs”, “Load each game package atomically as one typed pair”, “Validate loaded package pairs with structured dependency-aware issues”, and “Author Greybridge first as a validated content foundation”
* `doc/high_level_design.md`: “Package loader and validator”, “Principal records”, and “Testing strategy”
* `doc/initial_scenario.md`: “Package implementation stages”, “Location graph”, “Actors”, and “Explicit exclusions”
* `src/llm_system/game_packages/`, `tests/test_game_packages.py`, `tests/test_game_package_validation.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, unrelated requirements, unrelated scenario sections, experiments, or implementation roadmap beyond this task.

## Fixed assumptions

* The rule package directory is `game_packages/rules/greybridge-rules/0.1.0/`; it contains `manifest.yaml` and entrypoint `rules.yaml`.
* The scenario package directory is `game_packages/scenarios/storm-at-greybridge/0.1.0/`; it contains `manifest.yaml` and entrypoint `scenario.yaml`.
* Both manifests use schema version `1`. The scenario manifest pins rule package `greybridge-rules` at exact version `0.1.0`.
* Both content entrypoints use content schema version `1` and only their current strict fields.
* Rule catalog authored order is object archetypes `medicine`, `reinforcement-materials`; character archetypes `traveler`, `courier`, `caretaker`; decision policies `courier-llm-policy`, `caretaker-rule-policy`.
* `courier-llm-policy` has type `llm`; `caretaker-rule-policy` has type `rule`.
* Location authored order is `greybridge-waystation`, `greybridge-span`, `far-bank`.
* Connection authored order is `waystation-to-span`, `span-to-waystation`, `span-to-far-bank`, `far-bank-to-span`.
* Waystation-span traversal is 60 seconds in each direction. Span-far-bank traversal is 120 seconds in each direction.
* Entity authored order is `player`, `injured-courier`, `bridge-caretaker`, `medicine`, `reinforcement-materials`.
* The player is named `Traveler`, uses character archetype `traveler`, and begins at `greybridge-waystation`.
* The injured courier uses character archetype `courier`, begins at `greybridge-waystation`, and references `courier-llm-policy` with type `llm`.
* Courier goal order is `deliver-medicine`, then `protect-injury`. The courier has a non-blank initial plan consistent with seeking help and crossing before the route closes.
* The bridge caretaker uses character archetype `caretaker`, begins at `greybridge-span`, and references `caretaker-rule-policy` with type `rule`.
* Caretaker goal order is `protect-people`, `preserve-bridge`, `protect-supplies`, then `reach-safety`. The caretaker has a non-blank initial plan consistent with guarding and preserving the bridge while feasible.
* `medicine` references object archetype `medicine` and is possessed by `injured-courier`.
* `reinforcement-materials` references object archetype `reinforcement-materials` and begins at `greybridge-waystation`.
* Exact human-readable titles, names not fixed above, identity summaries, goal descriptions, and plan wording are scenario-authoring choices. They must remain concise and consistent with accepted facts but are not mechanical authority.
* No Fieldcraft, actions, bridge condition, perceptible facts, flood event, director hook, objective, check, progression, mutable state, or other unsupported concept may be added or encoded indirectly.
* The repository root `game_packages/` content is not added to wheel package data in this task.
* No production Python behavior, schema, dependency, or dependency version may change.
* This first authored content milestone advances the project version from `0.8.0` to `0.9.0`; the lockfile's editable root-package version must match.

## In scope

* Add the two exact package directories, manifests, and YAML entrypoints.
* Author the fixed catalogs, topology, entities, placements, NPC goals, plans, and policy references using readable YAML.
* Add repository-level behavioral tests that load both real directories with `load_game_package`, validate them with `validate_game_packages`, and assert their salient accepted content.
* Keep prose assertions limited to non-blank presence where exact wording is not fixed.
* Update project version, root lockfile metadata, package-version test, and README with the package locations, validation command path in Python, represented content, and explicit limitations.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* New Python production logic or changes to loading, validation, manifest, spatial, entity, rule-root, or scenario-root contracts.
* Additional locations, connections, actors, objects, archetypes, policies, or basic-supplies objects.
* Fieldcraft, actions, abilities, effects, conditions, perception facts, bridge damage, flood scheduling, System director hooks, objectives, progression, or runtime state.
* Placeholder, extension, metadata, tag, property, mechanics, event, hook, objective, or generic dictionaries.
* Treating names, identity summaries, goals, or plans as executable rules or canonical mutable state.
* Package discovery, catalog scanning, CLI tooling, Streamlit/FastAPI integration, world creation, persistence, migration, or content generation.
* Wheel/package-data configuration or installed-distribution access to repository content.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

The exact new content files are:

```text
game_packages/rules/greybridge-rules/0.1.0/manifest.yaml
game_packages/rules/greybridge-rules/0.1.0/rules.yaml
game_packages/scenarios/storm-at-greybridge/0.1.0/manifest.yaml
game_packages/scenarios/storm-at-greybridge/0.1.0/scenario.yaml
```

The likely test file is `tests/test_greybridge_packages.py`. Tests must locate content relative to the repository test file rather than depending on the process working directory.

## Acceptance criteria

1. Both exact package directories and filenames exist, and each manifest identity matches its directory and entrypoint (`PACK-012` through `PACK-019`, `SCENARIO-009`).
2. Loading both real directories returns the correct concrete loaded-package types, and `validate_game_packages` returns a `ValidatedGamePackages` pair without bypassing either public boundary (`PACK-020` through `PACK-026`).
3. The rule content contains exactly the fixed two object archetypes, three character archetypes, and two policy definitions in authored order, with correct policy types (`RULE-001` through `RULE-006`).
4. The scenario contains exactly the three fixed locations and four fixed directed connections in authored order, with 60- and 120-second traversal durations as specified (`SPACE-008` through `SPACE-014`, `SCENARIO-010`).
5. The scenario contains exactly the fixed player, courier, caretaker, medicine, and reinforcement-material entities in authored order, with the fixed archetype, location, possession, goal-order, and policy relationships (`ENTITY-001` through `ENTITY-009`, `SCENARIO-011`).
6. NPC identity summaries, goal descriptions, and initial plans are non-blank and consistent with the accepted scenario without being interpreted as mechanics.
7. Strict loading proves neither entrypoint contains unsupported fields, and README does not claim that the content is playable or includes deferred systems (`SCENARIO-012`).
8. Tests read the repository's real YAML files, assert salient identities and relationships rather than reconstructing equivalent temporary packages, and fail if the package pin, topology, cast, placement, or policy assignments regress.
9. All existing loader, semantic-validation, and structural-model behavior remains passing without production Python changes.
10. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.9.0`; dependencies and all resolved dependency versions remain unchanged.
11. README identifies both content directories, explains what schema version 1 currently represents, shows the public loading-then-validation flow, and lists the deferred Greybridge concepts without implying they are encoded in prose.

## Required verification

* Write and run the first real-package behavioral test before adding package content; record the expected missing-directory loading failure.
* Run focused Greybridge package tests after each package and relationship group is authored.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.8.0` to `0.9.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede content creation; do not remove or rename existing files afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if the accepted foundation requires a schema or production-code change, an unsupported field or concept, another content record, different package identity, different topology or placement, package-data configuration, a dependency, or a claim that the package is playable or world-ready.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Real Greybridge rule and scenario packages load from their repository
directories and pass semantic validation as a schema-version-1 content foundation.

**Changed files:** `game_packages/rules/greybridge-rules/0.1.0/manifest.yaml`,
`game_packages/rules/greybridge-rules/0.1.0/rules.yaml`,
`game_packages/scenarios/storm-at-greybridge/0.1.0/manifest.yaml`,
`game_packages/scenarios/storm-at-greybridge/0.1.0/scenario.yaml`,
`tests/test_greybridge_packages.py`, `tests/test_package.py`, `pyproject.toml`,
`uv.lock`, and `README.md`.

**Verification:** Initial red state: `uv run pytest tests/test_greybridge_packages.py -q`
failed before content creation because `load_game_package` raised
`GamePackageLoadError` caused by `NotADirectoryError` for the missing rule package
directory. Final focused test: the same command passed (1 passed). `uv sync --locked`,
`make format`, `make lint`, `make mypy`, `make test` (100 passed), `make check`,
`uv lock --check`, and `git diff --check` all passed. `uv.lock` diff was confirmed
to contain only the editable `llm-system` root-package version change from `0.8.0`
to `0.9.0`.

**Deviations:** None.

**Design gaps or follow-ups:** None. This content intentionally leaves mechanics,
runtime state, and world-readiness to later contracts.

## Integrator review

**Disposition:** Accepted.

The integrator independently loaded both repository package directories through `load_game_package`, validated the pair through `validate_game_packages`, and inspected the exact manifests, catalogs, topology, cast, placements, goals, plans, and policy references. Review strengthened the real-content test to assert every directed connection endpoint as well as ID and duration, and moved all model imports onto the public package boundary. `uv sync --locked`, `make format`, `make lint`, `make mypy`, `make test`, `make check`, `uv lock --check`, and `git diff --check` succeeded on Python 3.12.3; the final suite contains 100 passing tests. The only lockfile change is the editable root package version from `0.8.0` to `0.9.0`.
