# TASK-038: Create, resume, and reset the singleton world

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-036 and TASK-037

## Objective

Add the application lifecycle boundary that turns validated authored packages into the authoritative singleton world, reconstructs that active world after restart from its exact recorded package versions, and provides one explicitly destructive development reset.

Creation and reset must become durable only through explicit SQLite commit. Resume must validate exact package ownership and runtime completeness without changing authoritative data.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Canonical`, `Canonical world state`, `Character definition`, `Connection definition`, `Entity definition`, `Primary persistence`, `Rule package`, `Scenario package`, and `Validated world state`
* `doc/requirements.md`: `WORLD-001` through `WORLD-006`, `PACK-019` through `PACK-028`, `RULE-005`, `STATE-001` through `STATE-018`, `STATE-045`, `STORE-001` through `STORE-014`, and `LIFECYCLE-001` through `LIFECYCLE-008`
* `doc/decisions.md`: `Begin with one persistent world`, `Separate authored spatial definitions from runtime state`, `Model scenario inhabitants as discriminated entity definitions`, `Model runtime state as an ID-linked mutable-facts overlay`, `Require complete overlays at world readiness`, `Store canonical runtime collections as ordered immutable tuples`, `Persist the current world as a typed snapshot with separate history`, `Expose persistence through an explicitly committed unit of work`, `Keep package resolution outside the world repository`, `Protect world replacement with a monotonic revision`, `Materialize initial state without requiring future actor policies`, and `Use explicit create, resume, and destructive development-reset operations`
* `doc/high_level_design.md`: `Logical architecture`, `Component responsibilities`: `Turn coordinator`, and `Persistence and consistency`
* Initial source entrypoints: `src/llm_system/game_packages/loader.py`, `src/llm_system/game_packages/validation.py`, `src/llm_system/game_packages/entities.py`, `src/llm_system/game_packages/scenarios.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/simulation/scheduling.py`, `src/llm_system/persistence/records.py`, `src/llm_system/persistence/sqlite.py`, and `src/llm_system/application/__init__.py`
* Initial test entrypoints: `tests/test_greybridge_packages.py`, `tests/test_world_state_validation.py`, `tests/test_sqlite_persistence.py`, and `tests/test_actor_action_step.py`
* Concrete package fixture: `game_packages/rules/greybridge-rules/0.2.0/` and `game_packages/scenarios/storm-at-greybridge/0.2.0/`
* Project boundary: `pyproject.toml`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, other role guides, or planning-chat history. Inspect additional source or tests only when tracing a dependency from the named entrypoints.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 400 |
| Role guide | Implementation and TDD procedure | `doc/agent_roles/implementer.md` | 380 |
| Task brief | Execution contract | This file | 2,300 |
| Glossary | Lifecycle and package vocabulary | Nine named entries | 300 |
| Requirements | Existing storage/state rules and lifecycle behavior | Named ID ranges above | 1,550 |
| Decisions | Fixed initialization, ownership, and reset choices | Twelve named entries | 2,500 |
| High-level design | Component ownership and persistence flow | Three named sections | 450 |
| **Total before source exploration** |  |  | **7,880** |

Source and tests discovered while tracing the named implementation path are excluded from this pre-code documentation budget. If measured extracts materially exceed the soft limit, narrow surrounding prose while retaining every named contract rather than loading whole documents.

## Fixed assumptions

* Add one focused application lifecycle module; do not put package loading or initial-state construction into SQLite repositories.
* Expose a strict immutable active-world result containing the exact `StoredWorld` and its package-aware `ValidatedWorldState`. It must reject disagreement between their state or package identities and versions. The stored scheduled queue remains available through the stored record.
* Initial-state construction accepts `ValidatedGamePackages`, sets simulation time to 0, and preserves authored order while mapping every character, object, connection, and boolean world fact to its explicit runtime counterpart.
* Map `LocationPlacementDefinition` to `ObjectAtLocation` and `PossessedPlacementDefinition` to `ObjectPossessedByCharacter`. Every authored connection starts available. Use each authored boolean fact's initial value.
* The initial scheduled queue is empty. No current package schema authors scheduled occurrences, so do not infer the Greybridge flood, director hooks, or NPC work.
* Creation accepts a caller-assigned UUID and validated packages. It constructs and validates state, calls the existing singleton `worlds.create`, explicitly commits, and returns only after commit.
* Resume accepts the SQLite store and configured `game_packages` root. It loads the singleton record, constructs only `rules/{recorded-id}/{recorded-version}` and `scenarios/{recorded-id}/{recorded-version}`, loads both through `load_game_package`, checks their concrete package kinds, semantically validates the pair, requires exact recorded ownership, validates the stored state, and returns without writes.
* Resume performs exact lookup, not directory scanning, newest-version selection, fallback, or package copying. Preserve existing public package-load and validation errors rather than flattening them unless a new lifecycle-specific mismatch error is required.
* Development reset is exposed only through an explicitly named method such as `reset_world_for_development`. It requires an existing singleton, deletes all trace rows, event rows, then the current-world row inside the same unit of work, creates the supplied known initial world at revision 0, and explicitly commits.
* Add the narrow unit-of-work capability needed to clear the complete singleton timeline for development reset. Do not expose a raw connection, general delete repositories, direct state editing, or repository-owned commits.
* Reset accepts a new caller-assigned UUID. It does not preserve revision, prior world identity, events, or traces and emits no replacement event or trace. A reset failure at any point rolls the entire deletion and replacement back.
* Policy references remain inert authored data here. Do not add a policy registry, placeholder implementation, policy readiness flag, or actor execution.

## In scope

* Pure deterministic initial `WorldState` construction and validation from a `ValidatedGamePackages` pair.
* Strict active-world result contract shared by create, resume, and reset.
* Application services for create, resume from exact filesystem package paths, and explicit destructive development reset.
* One narrow atomic SQLite unit-of-work reset capability covering the singleton world and its event and trace histories.
* Real SQLite restart tests and Greybridge `0.2.0` end-to-end lifecycle tests.
* Rollback tests proving a failed reset preserves the prior timeline.
* A minor project version bump.

## Out of scope

* FastAPI, Streamlit, player turns, text interpretation, narration, or inspection UI.
* Actor policy implementation or availability registries, LLM calls, System director hooks, world-creation hook invocation, or NPC activity.
* Scheduled-activity authoring, generation, selection, execution, recurrence, or persistence changes.
* Multiple worlds, save slots, branching history, production authorization, soft reset, archive, backup, or restore.
* Package discovery, latest-version selection, compatibility ranges, remote packages, package copying, or persistence-layer package loading.
* New canonical event or trace types for lifecycle operations.
* SQLite schema changes, generic migration machinery, ORM, or new dependency.
* Governance-document changes.

## Expected contracts and files

Likely additions or changes:

* `src/llm_system/application/world_lifecycle.py` and application public exports;
* `src/llm_system/persistence/sqlite.py` for the narrow reset operation;
* `tests/test_world_lifecycle.py` plus focused persistence coverage if needed;
* `tests/test_package.py`, `pyproject.toml`, and `uv.lock` for version `0.36.0`; and
* this task brief for handoff only.

Prefer public contracts equivalent to:

* `build_initial_world(packages: ValidatedGamePackages) -> ValidatedWorldState`;
* `create_world(store: SQLiteStore, packages: ValidatedGamePackages, *, world_id: UUID) -> ActiveWorld`;
* `resume_world(store: SQLiteStore, package_root: Path) -> ActiveWorld`; and
* `reset_world_for_development(store: SQLiteStore, packages: ValidatedGamePackages, *, world_id: UUID) -> ActiveWorld`.

Use an application-owned exact-package mismatch error only if existing load, semantic-validation, or stored-record errors cannot express the failure coherently. Keep the SQLite reset capability transaction-scoped and unusable after commit.

## Acceptance criteria

1. Initial-state construction from real Greybridge `0.2.0` produces simulation time 0; player, injured courier, and caretaker states in authored order at their authored locations; medicine possessed by the courier; reinforcement materials at the waystation; four authored connections available in authored order; `bridge-reinforced=false`; and an empty scheduled queue at persistence time. (`LIFECYCLE-001`, `LIFECYCLE-002`)
2. The derived state passes `validate_world_state` against the exact input packages. Construction is deterministic, does not mutate packages, generate identity, consult filesystem state, invoke policies, or contain Greybridge-specific branches. (`STATE-004`, `STATE-010` through `STATE-018`, `STATE-045`, `LIFECYCLE-001`, `LIFECYCLE-008`)
3. Creation with a caller UUID commits one revision-0 singleton with exact manifest identities and versions, derived state, and empty queue, then returns an internally coherent active-world result. Reopening SQLite and resuming recovers an equal result. (`STORE-010`, `STORE-011`, `LIFECYCLE-003`, `LIFECYCLE-004`)
4. Creating when a singleton exists fails through the existing persistence contract without changing the world, events, or traces. Any pre-commit construction or persistence failure returns no active-world result and leaves durable state unchanged. (`WORLD-001`, `STORE-008`, `LIFECYCLE-003`)
5. Resume uses only the exact recorded rule and scenario directories under the supplied package root. It rejects a missing world, missing or malformed recorded package, wrong concrete package kind, semantic incompatibility, recorded ownership mismatch, or stored-state incompatibility and performs no authoritative write on success or failure. (`STORE-010`, `LIFECYCLE-004`, `LIFECYCLE-005`)
6. Resume never scans for alternatives or silently upgrades: if the recorded version directory is absent while another version exists, it fails and the stored record remains unchanged. (`WORLD-002`, `LIFECYCLE-004`, `LIFECYCLE-008`)
7. Explicit development reset of a non-empty world commits a supplied new world UUID at revision 0 with the selected packages' known initial state and removes all prior canonical events and completed-step traces. Reopening and resuming recovers only the replacement timeline. (`WORLD-004`, `LIFECYCLE-006`, `LIFECYCLE-007`)
8. Reset without an existing singleton fails. A reset failure after deletion begins rolls back atomically so the prior world revision, package references, state, queue, events, and traces remain exactly recoverable. Test this behavior through public outcomes rather than spying on internal repository call order. (`STORE-004`, `STORE-008`, `LIFECYCLE-006`, `LIFECYCLE-007`)
9. The lifecycle code contains no package-version discovery, generated UUID, generic policy registry, scheduled work, LLM call, API/presentation behavior, general state editor, save-slot abstraction, raw SQLite connection exposure, repository commit, schema change, ORM, or new dependency.
10. `pyproject.toml` and `uv.lock` record version `0.36.0` without dependency drift.

## Required verification

Follow TDD and record the first focused behavioral-test failure before implementation logic.

Run:

* `uv sync --locked`
* `uv run pytest tests/test_world_lifecycle.py tests/test_sqlite_persistence.py` or the actual focused paths
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires:

* a policy implementation or policy-availability claim;
* authored or generated scheduled activities;
* a package version other than the exact recorded version during resume;
* preserving any prior timeline data through destructive reset;
* generated world identity or general save-slot behavior;
* package resolution inside a persistence repository;
* lifecycle events, traces, or schema migration;
* repository-owned commit behavior or non-atomic reset; or
* a new runtime dependency.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
