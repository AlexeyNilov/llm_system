# TASK-036: Persist the current world and canonical event history in SQLite

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `Default`

**Depends on:** TASK-035 and the accepted M3.6 context-routing foundation

## Objective

Add the first authoritative SQLite boundary for the single persistent world. A process must be able to create, commit, reopen, strictly decode, and revision-check the current immutable world and its scheduled queue while retaining canonical events in durable commit order.

The persistence layer stores validated domain results and owns transaction mechanics; it must not resolve game packages, evaluate simulation rules, or introduce a step-trace contract that does not yet exist.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Canonical`, `Canonical world state`, `Event`, `Game package`, `Primary persistence`, `Scheduled activity queue`, `Simulation step`, and `Validated world state`
* `doc/requirements.md`: `WORLD-001` through `WORLD-006`, `STATE-004` through `STATE-009`, `ACTION-020` through `ACTION-021`, `EVENT-001` through `EVENT-009`, and `STORE-001` through `STORE-012`
* `doc/decisions.md`: `Begin with one persistent world`, `Use SQLite as the initial authoritative store`, `Replace immutable world-state snapshots atomically`, `Give one application transaction ownership of step completion`, `Persist the current world as a typed snapshot with separate history`, `Expose persistence through an explicitly committed unit of work`, `Bootstrap one version-gated SQLite schema before building migrations`, `Keep package resolution outside the world repository`, `Protect world replacement with a monotonic revision`, and `Order canonical event history by durable insertion sequence`
* `doc/high_level_design.md`: `Persistence and consistency`
* Initial source entrypoints: `src/llm_system/simulation/state.py`, `src/llm_system/simulation/scheduling.py`, `src/llm_system/simulation/events.py`, `src/llm_system/game_packages/models.py`, and `src/llm_system/simulation/_types.py`
* Initial test entrypoints: JSON round-trip cases in `tests/test_runtime_state.py`, `tests/test_scheduled_activity_contracts.py`, and `tests/test_events.py`
* Project boundary: `pyproject.toml`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, other role guides, or planning-chat history. Inspect additional source or tests only when tracing a dependency from the named entrypoints.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 400 |
| Role guide | Implementation and TDD procedure | `doc/agent_roles/implementer.md` | 380 |
| Task brief | Execution contract | This file | 1,420 |
| Glossary | Persistence vocabulary | Eight named entries | 260 |
| Requirements | Observable persistence and existing event/state contracts | Named ID ranges above | 1,050 |
| Decisions | Fixed representation, authority, transaction, revision, and ordering choices | Ten named entries above | 2,250 |
| High-level design | Component relationship | `Persistence and consistency` | 330 |
| **Total before source exploration** |  |  | **6,090** |

Source and tests discovered while tracing the named implementation path are excluded from this pre-code documentation budget.

## Fixed assumptions

* Use Python's standard-library `sqlite3`; add no ORM, migration framework, database service, or runtime dependency.
* The database schema version and the stored-world payload schema version are distinct integer version boundaries. Both begin at 1.
* One SQLite database contains at most one current world. Use a generated application-assigned UUID for its durable identity.
* A strict immutable `StoredWorld` record contains payload schema version, world identity, non-negative revision, exact rule- and scenario-package IDs and versions, `WorldState`, and `ScheduledActivityQueue`.
* The repository decodes stored domain contracts but does not locate packages or produce `ValidatedWorldState`.
* World creation assigns revision 0. Replacement retains identity and package ownership, requires the loaded revision, and lets the repository calculate revision plus one.
* Canonical events are appended only for the current resulting world revision. Their database insertion sequence, not simulation occurrence time, defines history order.
* Unit-of-work repositories share one active connection and expose no commit method. Only explicit unit-of-work commit makes changes durable.

## In scope

* A focused `llm_system.persistence` package containing strict storage records, SQLite schema bootstrap, repository boundaries, unit of work, and task-required exceptions.
* Transactional creation of V1 tables for the singleton current world and append-only canonical events.
* Strict Pydantic serialization and decoding of `WorldState`, `ScheduledActivityQueue`, package references, and the discriminated `CanonicalEvent` union.
* Singleton world create, load, and revision-checked replacement.
* Canonical-event batch append and ordered history read.
* Explicit commit, rollback on exceptions, and rollback when the context exits without commit.
* Behavioral tests using temporary SQLite files and real connections.
* A minor project version bump for the new persistence capability.

## Out of scope

* Game-package location, loading, validation, migration, or compatibility policy.
* World initialization from a scenario, resume orchestration, development reset, save slots, branching, or offline progression.
* Simulation-step coordinator, trace model or trace table, proposal/outcome persistence, perception, narration, FastAPI, or Streamlit.
* Character memories, beliefs, Qdrant projections, random-generator state, and execution of scheduled activities.
* General migration machinery or a V1-to-V2 migration.
* Event replay as world reconstruction, history deletion, compaction, filtering, or pagination.
* Governance-document changes.

## Expected contracts and files

Likely additions:

* `src/llm_system/persistence/__init__.py`
* focused modules under `src/llm_system/persistence/` for records and SQLite I/O
* `tests/test_sqlite_persistence.py` or a similarly focused persistence test module

Expose a small public API equivalent in responsibility to:

* `StoredWorld` and `StoredCanonicalEvent`
* `SQLiteStore.open(path)`
* `SQLiteStore.unit_of_work()`
* a unit of work exposing `worlds`, `events`, and explicit `commit()`
* world `get`, `create`, and `replace` operations
* event batch `append` and ordered `list_for_world` operations
* typed failures for unsupported schema, stored-record decoding, existing or missing world, stale revision, and duplicate event identity

Names may follow stronger existing project conventions, but responsibilities and failure distinctions must remain explicit. Do not expose a raw connection as the application-facing persistence API.

## Acceptance criteria

1. Opening a new database transactionally creates schema V1 and sets `PRAGMA user_version` to 1; reopening V1 preserves data, while opening any unsupported version fails without changing that database. (`STORE-009`)
2. A committed create stores exactly one world at revision 0 with explicit identity, package ownership, strict `WorldState`, and strict `ScheduledActivityQueue`; a second create fails. (`WORLD-001`, `STATE-009`, `STORE-007`, `STORE-010`, `STORE-011`)
3. Loading an empty store reports absence without inventing a world. Loading a stored world strictly reconstructs the typed record without loading package files or claiming it is a `ValidatedWorldState`. (`STORE-010`)
4. Replacement succeeds only for the currently stored identity and revision, preserves package ownership, increments revision by exactly one, and returns the stored replacement. Missing-world and stale-revision failures are distinguishable and make no associated writes durable. (`STORE-011`)
5. A batch of canonical events is stored for the current resulting revision with unique event identities and database-assigned insertion sequence. Reading history returns strict canonical events in batch and commit order even when occurrence times are equal. (`EVENT-001` through `EVENT-009`, `STORE-012`)
6. Duplicate event identity, invalid stored payload, inconsistent explicit event metadata, or an event association to a non-current world revision fails explicitly rather than returning partially trusted data. (`STORE-004`, `STORE-012`)
7. Explicit unit-of-work commit makes world and event changes visible after reopening. An exception or context exit without commit rolls them all back. Repositories cannot independently commit. (`STORE-002`, `STORE-004`, `STORE-006`, `STORE-008`)
8. One behavioral test replaces a world and appends at least two same-time canonical events in one unit of work, then proves restart recovery, revision increment, and preserved event order. A corresponding failure test proves neither participant is durable after rollback.
9. Persistence code contains no simulation-rule evaluation, package filesystem access, Greybridge identifiers, trace placeholder, generic migration registry, ORM, or new dependency.
10. `pyproject.toml` and `uv.lock` record the accepted minor version bump without dependency drift.

## Required verification

Follow TDD and record the failing behavioral test before implementation logic.

Run:

* `uv sync --locked`
* `uv run pytest tests/test_sqlite_persistence.py` or the actual focused persistence test path
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires:

* a simulation-step trace shape or table;
* package filesystem resolution inside persistence;
* a choice about package upgrade or saved-world migration;
* multiple worlds or concurrent writer policy beyond revision checking;
* repository-owned commit behavior;
* an event order other than durable insertion order; or
* a new runtime dependency.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented the schema-version-gated SQLite store, strict stored-world and stored-event records, singleton world repository, append-only ordered event repository, and explicitly committed rollback-safe unit of work. Restart recovery behavior covers exact replacement of a non-empty typed scheduled activity queue.

**Changed files:** `src/llm_system/persistence/__init__.py`, `src/llm_system/persistence/errors.py`, `src/llm_system/persistence/records.py`, `src/llm_system/persistence/sqlite.py`, `tests/test_sqlite_persistence.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and this task brief.

**Verification:** Recorded the initial focused-test failure (`ModuleNotFoundError: No module named 'llm_system.persistence'`). The focused restart test replaces, commits, reopens, and exactly asserts a non-empty typed `ScheduledActivityQueue`. Passed `uv sync --locked`; `uv run pytest tests/test_sqlite_persistence.py` (6 passed); `make format`; `make lint`; `make mypy`; `make test` (329 passed); `make check` (329 passed plus format, lint, and mypy); `uv lock --check`; and `git diff --check`.

**Context used:** `AGENTS.md`; this task brief; `doc/agent_roles/implementer.md`; the eight named `doc/glossary.md` entries; the named requirement ranges in `doc/requirements.md`; the ten named decisions in `doc/decisions.md`; `Persistence and consistency` in `doc/high_level_design.md`; the five named initial source entrypoints; the three named initial test entrypoints; `pyproject.toml`; and task-local traces through `src/llm_system/simulation/__init__.py`, `tests/test_package.py`, `uv.lock`, and `Makefile`.

**Deviations:** None.

**Design gaps or follow-ups:** None.
