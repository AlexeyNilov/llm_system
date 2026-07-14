# TASK-044: Persist durable player-input step traces

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-037, TASK-042, and TASK-043

## Objective

Add strict, append-only SQLite persistence for the exact player interpretation that precedes a free-form player turn. It must represent the three already accepted completion meanings: thought-only, clarification, and one action link to an existing completed actor-action trace.

This is the durable evidence foundation for the later player-turn coordinator and API. It deliberately does not invoke a model, create trusted submissions, execute an action, or expose a free-form endpoint.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: “Action proposal”, “Action proposal submission”, “Functional LLM role”, “Model gateway”, “Perception snapshot”, “Player-input trace”, “Simulation step”, and “Simulation-step trace”
* `doc/requirements.md`: `PLAY-008` through `PLAY-013`, `LLM-008`, `LLM-015`, `LLM-016`, `STORE-006` through `STORE-016`, and `STEP-004` through `STEP-010`
* `doc/decisions.md`: “Persist the minimal completed actor-action trace”, “Migrate SQLite V1 to V2 for trace history”, “Build the first local gateway around functional structured output”, “Interpret one player input without creating authority”, and “Persist player interpretation in a linked input trace”
* Initial source entrypoints: `src/llm_system/application/model_gateway.py`, `src/llm_system/application/player_interpreter.py`, `src/llm_system/simulation/traces.py`, `src/llm_system/persistence/errors.py`, `src/llm_system/persistence/records.py`, `src/llm_system/persistence/sqlite.py`, `src/llm_system/persistence/__init__.py`, and `src/llm_system/application/__init__.py`
* Initial test entrypoints: `tests/test_player_interpreter.py`, `tests/test_actor_action_step.py`, `tests/test_sqlite_persistence.py`, and `tests/test_world_lifecycle.py`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, API/UI code, package content, or planning-chat history. Do not contact a live model endpoint. Trace only task-local source and tests after reading the selections above.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 430 |
| Role guide | Implementation procedure | `doc/agent_roles/implementer.md` | 900 |
| Task brief | Execution contract | This file | 2,100 |
| Vocabulary | Trace and authority terminology | Eight named glossary entries | 360 |
| Requirements | Player evidence and SQLite behavior | Named IDs | 1,100 |
| Decisions | Fixed trace and migration design | Five named decisions | 1,550 |
| **Total before source exploration** |  |  | **6,440** |

## Fixed assumptions

* Preserve the public `llm_system.application` imports for all existing functional-generation and player-interpreter contracts. A contract relocation is permitted only to break the persistence-to-application import cycle cleanly; update existing application modules to re-export their established public names.
* Create a neutral, non-application contract module (or small modules) for the immutable functional-generation evidence and player-input contracts that persistence must strictly decode. It may depend on Pydantic and existing simulation contracts, but must not depend on `llm_system.application`, SQLite, HTTP transport, FastAPI, Streamlit, packages, or a live model.
* The strict immutable `PlayerInputStepTrace` must contain exactly `trace_schema_version: Literal[1]`, application-assigned `player_input_id: UUID`, exact `PlayerInterpretationResult`, and one strict discriminated completion. Its completion variants are exactly:
  * `thought_only`, valid only for an `interpreted` output with a non-null private thought and no proposal;
  * `clarification`, valid only for a `clarification` output; and
  * `action_linked`, valid only for an `interpreted` output with a non-null proposal and a required linked `simulation_step_id: UUID`.
  Do not add optional generic stage data, player-facing prose, trusted submissions, outcomes, state changes, or provider details beyond the already retained generation evidence.
* Keep `CompletedActorActionStepTrace` at schema version 1 unchanged. The player-input trace links to it by simulation-step identity; it is not a nullable extension of it.
* Introduce `StoredPlayerInputStepTrace` with database insertion sequence, world identity, observed and resulting non-negative revisions, and the strict payload. Trace payloads do not own a world identity or revision; the stored record does.
* Make SQLite schema version 3 current. Add one `player_input_step_traces` table with database-assigned insertion sequence; explicit world ID, observed revision, resulting revision, unique player-input ID, completion kind, nullable action simulation-step ID, and JSON payload. Enforce the no-action equal-revision versus action-linked +1 revision relationship in both strict contracts/repository validation and a SQLite check constraint where practical.
* Opening V1 must migrate transactionally through the existing actor-trace table and then add the player-input table; opening V2 adds only the player-input table. Preserve every existing world, canonical event, and actor-action trace row. Opening V3 preserves data. Unsupported versions still fail without modification.
* Add `SQLitePlayerInputTraceRepository` as `unit.player_input_traces`, with `append(...)` and `list_for_world(...)`. `append` requires the current world to match its supplied world and resulting revision, rejects duplicate player-input identities, strictly cross-checks row metadata against payload, and marks the unit of work failed on every persistence or decode invariant failure.
* For `action_linked`, `append` must require one existing `simulation_step_traces` row with the same world ID and resulting revision as the input trace and the exact linked simulation-step identity. It must reject a missing or mismatched actor trace. Thought-only and clarification traces require no actor-action trace and retain equal observed/resulting revision.
* Development timeline reset must delete player-input traces together with the existing world, event, and actor-action history in the same transaction.
* Bump the project minor version from `0.42.0` to `0.43.0`, including the installed-version assertion and lockfile version. Do not add dependencies.

## In scope

* Strict neutral functional-generation and player-input contract placement, preserving existing public application imports.
* `PlayerInputStepTrace`, its exact completion variants, strict coherence validation, stored record, persistence errors, repository API, public exports, and SQLite V3 migration.
* Focused tests for contract coherence, strict decoding/metadata tamper detection, append/list ordering, duplicate input identity rollback, current-world/revision mismatch rollback, action-link presence/world/revision checks, V1/V2/V3 migration retention, reset cleanup, and prior actor-action trace compatibility.
* Version and lockfile updates, plus this brief's status and handoff report only.

## Out of scope

* Calling a live or fake model from a new coordinator, changing request/repair behavior, prompt changes, or changing the interpreter's observable semantics.
* Free-form API endpoints, Streamlit inputs, trusted identity/source/submission/outcome/event construction, action authorization or execution, stale-input presentation, narration, scheduling, NPC runtime, inspection UI, or System notifications.
* Changing `CompletedActorActionStepTrace` fields or schema version, replacing its table, generic migration infrastructure, global cross-table timeline ordering, a generic trace union, or storage for other functional LLM roles.
* Changes to requirements, decisions, glossary, high-level design, roadmap, continuation state, README, domain guide, ideas, reviews, packages, or agent governance.

## Expected contracts and files

* New neutral contract modules under `src/llm_system/` for shared functional-generation/player-input trace decoding, with `application/model_gateway.py` and `application/player_interpreter.py` re-exporting established public types.
* `src/llm_system/persistence/errors.py`, `records.py`, `sqlite.py`, and `__init__.py`: V3 schema/migration and player-input trace repository.
* `src/llm_system/application/__init__.py` and, if appropriate, `src/llm_system/simulation/__init__.py`: stable public exports.
* Focused tests, likely `tests/test_player_input_traces.py` plus adjustment of existing persistence/lifecycle/import tests.
* `pyproject.toml`, `uv.lock`, `tests/test_package.py`: version only.

## Acceptance criteria

1. The immutable player-input trace strictly preserves the exact `PlayerInterpretationResult` and accepts only the three specified completion variants with their matching output shape. Unknown fields, coercion, missing required nullable fields, wrong trace version, and mismatched completion/output combinations fail.
2. Existing imports of functional-generation and player-interpreter public contracts through `llm_system.application` remain valid, while persistence does not import the application package or HTTP gateway to decode a stored player-input trace.
3. SQLite V3 bootstraps a fresh database; V1 and V2 stores migrate transactionally without loss of existing world, event, or actor-action traces; V3 reopens unchanged; unsupported versions remain untouched.
4. Player-input records round-trip in insertion order with strict payload-to-column metadata checks. Duplicate player-input identity, bad world/revision, malformed JSON, or metadata tampering marks the unit of work failed and leaves no partial record durable.
5. Thought-only and clarification traces persist only with equal observed/resulting revisions and no action link. An action-linked trace persists only at observed-plus-one revision with a matching, already-appended actor-action trace for the same world and resulting revision. All cross-check failures roll back the surrounding transaction.
6. Development reset removes all player-input traces atomically with the other timeline records. Existing actor-action coordinator, gateway, interpreter, persistence, lifecycle, and API behavior remains compatible.
7. The project is version `0.43.0`; focused, type, quality, lock, and full-suite checks pass without a live model or new dependency.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv run pytest tests/test_player_input_traces.py`
* `uv run pytest tests/test_player_interpreter.py tests/test_model_gateway.py tests/test_actor_action_step.py tests/test_sqlite_persistence.py tests/test_world_lifecycle.py`
* `make format`
* `make lint`
* `make mypy`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires model invocation, an API/UI change, action execution, a change to existing actor-action trace schema, a generic trace/migration framework, a new dependency, rewriting current persistence history, a global trace timeline contract, or governance changes outside this brief.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
