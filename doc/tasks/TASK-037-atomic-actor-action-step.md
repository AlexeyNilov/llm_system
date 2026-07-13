# TASK-037: Commit one actor action and its trace atomically

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `Default`

**Depends on:** TASK-036 and the completed authorization, dispatch, commitment, perception, and deterministic resolver contracts

## Objective

Add the first application-level simulation-step coordinator. Given one trusted actor-action submission and caller-assigned resolution identities, it must load and validate the authoritative world, compose the existing deterministic authority chain, derive the actor's immediate perception, and atomically persist the next world revision, canonical events, and one minimal completed-step trace before returning success.

Add the concrete SQLite V1-to-V2 migration required for append-only trace history. Preserve the scheduled queue exactly; this task must not invent execution semantics for scheduled environmental, NPC, or System-director activities.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Action proposal`, `Action proposal submission`, `Canonical`, `Canonical world state`, `Event`, `Outcome`, `Perception snapshot`, `Primary persistence`, `Simulation step`, and `Validated world state`
* `doc/requirements.md`: `WORLD-001` through `WORLD-006`, `STATE-004` through `STATE-009`, `ACTION-003`, `ACTION-006` through `ACTION-010`, `ACTION-024` through `ACTION-033`, `ARBITER-001` through `ARBITER-009`, `AUTHZ-001` through `AUTHZ-015`, `DISPATCH-001` through `DISPATCH-010`, `PERCEPTION-015` through `PERCEPTION-016`, `PERCEPTION-026` through `PERCEPTION-035`, `STORE-001` through `STORE-014`, and `STEP-001` through `STEP-010`
* `doc/decisions.md`: `Separate proposal payloads from trusted submission metadata`, `Replace immutable world-state snapshots atomically`, `Commit outcomes into one validated-world result`, `Give one application transaction ownership of step completion`, `Persist the current world as a typed snapshot with separate history`, `Expose persistence through an explicitly committed unit of work`, `Keep package resolution outside the world repository`, `Protect world replacement with a monotonic revision`, `Order canonical event history by durable insertion sequence`, `Persist the minimal completed actor-action trace`, `Compose the first coordinator before scheduled execution`, and `Migrate SQLite V1 to V2 for trace history`
* `doc/high_level_design.md`: `Turn coordinator`, `Simulation-step flow`, `Persistence and consistency`, and `Observability and evaluation`
* Initial source entrypoints: `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/dispatch.py`, `src/llm_system/simulation/commitment.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/perception_engine.py`, `src/llm_system/simulation/validation.py`, `src/llm_system/persistence/records.py`, and `src/llm_system/persistence/sqlite.py`
* Initial test entrypoints: `tests/test_actor_action_authorization.py`, `tests/test_actor_action_dispatch.py`, `tests/test_use_resolver.py`, `tests/test_self_event_feedback.py`, and `tests/test_sqlite_persistence.py`
* Project boundary: `pyproject.toml`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, other role guides, or planning-chat history. Inspect additional source or tests only when tracing a dependency from the named entrypoints.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 400 |
| Role guide | Implementation and TDD procedure | `doc/agent_roles/implementer.md` | 380 |
| Task brief | Execution contract | This file | 2,250 |
| Glossary | Coordinator and trace vocabulary | Ten named entries | 330 |
| Requirements | Existing authority chain and new atomic behavior | Named ID ranges above | 1,650 |
| Decisions | Fixed authority, trace, transaction, and migration choices | Twelve named entries | 2,350 |
| High-level design | Component flow and observability | Four named sections | 520 |
| **Total before source exploration** |  |  | **7,880** |

Source and tests discovered while tracing the named implementation path are excluded from this pre-code documentation budget. If measured extracts exceed the soft limit materially, narrow surrounding prose while retaining every named contract rather than loading entire documents.

## Fixed assumptions

* Add a small application orchestration boundary; do not move coordination into the pure simulation kernel or SQLite repositories.
* Expose one strict immutable `CompletedActorActionStepTrace` at trace payload schema version 1. It contains exactly `trace_schema_version`, `simulation_step_id`, `decision_context_id`, `submission`, `outcome`, `current_perception`, and immutable `self_event_feedback`.
* The trace validates identity agreement among its envelope, submission, and outcome, plus submitted actor and committed simulation-time agreement across current perception and self feedback.
* Expose one strict immutable completed-step result containing exactly durable `world_id`, non-negative `resulting_world_revision`, and the exact completed trace.
* The coordinator contract is equivalent in responsibility to `execute_actor_action_step(store, packages, submission, *, outcome_id, event_id) -> CompletedActorActionStep`. Use stronger names only if they preserve this exact boundary.
* The coordinator receives `ValidatedGamePackages`; it matches their manifest identities and versions to the `StoredWorld` package references, then calls `validate_world_state` on the decoded state. Persistence still does not locate package files.
* The coordinator reuses `authorize_actor_action`, `dispatch_actor_action`, `commit_outcome`, `project_current_perception`, and `project_self_event_feedback`; it does not duplicate their rules or catch and flatten their domain errors.
* Every resolved outcome uses `worlds.replace`, including rejected or otherwise unchanged outcomes, so every completed trace receives one unique next durable world revision. The scheduled queue passed to replacement is the exact loaded queue object.
* Append only `outcome.events`; rejected outcomes have no events. Persist one trace for the resulting revision, then explicitly commit before constructing or returning completion.
* SQLite schema V2 adds one append-only trace table. New databases create V2 directly; V1 migrates directly and transactionally to V2; no generic migration framework is introduced.

## In scope

* Strict completed actor-action trace and completed-step result contracts.
* One application coordinator for trusted actor-action submissions.
* Exact package-ownership comparison and relational validation of loaded state before simulation use.
* Existing authorization, dispatch, commitment, current-state perception, and self-event-feedback composition.
* SQLite V2 new-database bootstrap and direct transactional V1-to-V2 migration.
* Strict append-only trace repository bound to the existing unit of work, including ordered history reads and duplicate identity protection.
* Atomic success and rollback tests using real SQLite files and real Greybridge `0.2.0` packages.
* The KRV-001 regression: successful Greybridge reinforcement through authorization, dispatch, commitment, perception, durable world/event/trace commit, and restart recovery.
* A minor project version bump.

## Out of scope

* Player text interpretation, private thought handling, LLM calls, NPC policies, System director behavior, narration, notifications, FastAPI, or Streamlit.
* Scheduled-activity selection, consumption, execution, retries, recurrence, or queue modification.
* Witness, addressed-speech, or overheard-speech feedback; event delivery cursors; memory; beliefs; or presentation traces.
* Durable traces for package, authorization, dispatch, commitment, or persistence failures that occur before a resolved outcome commits.
* World creation, package discovery, resume path selection, reset, save slots, concurrent execution infrastructure, or general locking.
* A generic trace-stage dictionary, optional placeholders for future stages, a generic migration registry, ORM, or new dependency.
* Governance-document changes.

## Expected contracts and files

Likely additions or changes:

* a focused trace-contract module under `src/llm_system/simulation/` or a similarly dependency-safe domain location;
* a focused coordinator module under a new `src/llm_system/application/` package;
* `src/llm_system/persistence/records.py`, `sqlite.py`, `errors.py`, and public exports;
* `tests/test_actor_action_step.py` and focused persistence migration/trace cases;
* `tests/test_package.py`, `pyproject.toml`, and `uv.lock` for the version bump; and
* this task brief for handoff only.

The unit of work must expose a trace repository alongside worlds and events. Its append operation accepts a world identity, current resulting revision, and strict completed trace; its list operation returns strict stored records in durable insertion order. A stored trace record retains insertion sequence, world identity, resulting revision, and the exact trace payload.

Use application-owned explicit errors for absent world or package-ownership mismatch where existing persistence errors do not already express the condition. Do not expose raw SQLite connections or make repositories commit independently.

## Acceptance criteria

1. A new SQLite database is V2. A representative V1 database containing a world and canonical event migrates to V2 without losing or changing either record; reopening V2 preserves all data, while unsupported versions still fail unchanged. (`STORE-009`)
2. Trace append requires the current world identity and revision, assigns durable insertion order, rejects duplicate simulation-step identity, and strictly decodes and cross-checks explicit step, outcome, and status metadata. (`STORE-013`, `STORE-014`)
3. Trace construction rejects disagreement in simulation-step, decision-context, proposal, actor, or committed-time evidence and accepts the exact coherent output of the existing authority and perception chain. (`STEP-004`, `STEP-005`)
4. The coordinator loads the singleton world inside its unit of work, rejects missing or package-incompatible data before resolution, validates the runtime state against the exact supplied validated packages, and generates no identities. (`STEP-001`, `STEP-002`)
5. A successful real Greybridge `0.2.0` Use submission flows through the existing authorization and dispatcher, reinforces the bridge, advances simulation time by 300 seconds, projects the player's current perception and exact self-event feedback, and commits world revision 1, one `ObjectUsedEvent`, and one completed trace. Reopening the database recovers all three consistently. (`STEP-003` through `STEP-007`)
6. The coordinator returns only after commit and returns the committed world identity, revision, and exact trace. The stored trace contains the exact trusted submission and outcome, including ordered state changes, rather than a reconstructed summary. (`ACTION-028`, `STEP-004`, `STEP-010`)
7. A rejected resolved action still commits one trace and advances the durable revision by one while preserving the exact canonical state and scheduled queue and appending no canonical event. (`ARBITER-007`, `STEP-006`)
8. A trace failure after world replacement and event append rolls back all three participants. Authorization, package compatibility, dispatch, commitment, or persistence failure returns no completed result and leaves the last committed world, events, and traces recoverable unchanged. (`STORE-004`, `STORE-006`, `STORE-008`, `STORE-014`, `STEP-007`)
9. A non-empty scheduled queue is preserved exactly through a completed time-advancing step; no scheduler function is called and no activity is removed, executed, or added. (`STEP-008`)
10. Coordinator and persistence code contain no Greybridge-specific branch, duplicated operation rules, generated identity, LLM invocation, presentation logic, raw connection exposure, repository commit, generic trace dictionary, migration framework, ORM, or new dependency.
11. `pyproject.toml` and `uv.lock` record version `0.35.0` without dependency drift.

## Required verification

Follow TDD and record the first focused behavioral-test failure before implementation logic.

Run:

* `uv sync --locked`
* `uv run pytest tests/test_actor_action_step.py tests/test_sqlite_persistence.py` or the actual focused paths
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires:

* execution or consumption of a scheduled activity;
* a trace field for an LLM, cognition, memory, director, narration, presentation, or pre-resolution failure stage;
* accepting raw or untrusted proposal data at the coordinator boundary;
* package discovery or filesystem loading inside persistence;
* a world revision policy other than exactly one increment for each completed coordinated outcome;
* repository-owned commit behavior or non-atomic visibility;
* a migration other than direct V1-to-V2; or
* a new runtime dependency.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
