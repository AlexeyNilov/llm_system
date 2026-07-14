# TASK-054: Execute one scheduled courier decision with evidence

**Status:** Ready

**Owner:** Implementer

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-050, TASK-051, TASK-053

## Objective

When the authored injured courier is the first due NPC activity, execute its
memory-free LLM decision through the existing authoritative actor-action path.
The decision and its complete functional-generation evidence must remain outside
the write transaction until the exact selected work is rechecked, then commit
atomically with the action, resulting world, and scheduling evidence.

This makes the existing player-turn scheduled-progress behavior settle the
courier on a later request while preserving the rule-driven caretaker behavior.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: **action proposal submission**, **canonical**, **decision context**, **functional-generation evidence**, **scheduled activity**, **simulation arbiter**, **simulation-step trace**
* `doc/requirements.md`: `NPC-013` through `NPC-015`; `LLM-001`, `LLM-003`, `LLM-005`, `LLM-007`, `LLM-008`; `STEP-016` through `STEP-017`; `SCHEDULE-029` through `SCHEDULE-038`
* `doc/decisions.md`: “Consume one due caretaker activity with linked durable evidence”, “Report committed player action when scheduled progress is pending”, “Make the initial courier policy memory-free and generation-evidenced”, and “Execute the courier through the serialized scheduled-activity boundary”
* `src/llm_system/application/scheduled_execution_coordinator.py`
* `src/llm_system/application/player_turn_coordinator.py`
* `src/llm_system/application/npc_decision.py`
* `src/llm_system/simulation/traces.py`
* `src/llm_system/persistence/sqlite.py`
* `game_packages/scenarios/storm-at-greybridge/0.2.0/scenario.yaml`
* `tests/test_scheduled_execution.py`, `tests/test_player_turn_coordinator.py`, `tests/test_sqlite_persistence.py`, and `tests/test_courier_policy.py`

Do not read README, domain guide, roadmap, ideas, reviews, completed task briefs,
architect continuation state, or planning-chat history.

## Context budget

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Execution boundaries and role routing | `AGENTS.md` | 500 |
| Role guide | Implementation and TDD procedure | Implementer guide | 500 |
| Task contract | Fixed outcome and verification | This file | 1,050 |
| Vocabulary | Preserve authority and evidence terms | Seven named glossary entries | 750 |
| Requirements | Observable courier, LLM, player-turn, and scheduler constraints | Named IDs only | 1,600 |
| Decisions | Chosen transaction, evidence, and one-activity behavior | Four named entries | 1,050 |
| Initial code/tests | Trace the real execution and migration paths | Named source and test entrypoints | Excluded from pre-code documentation budget |
| **Total before source exploration** |  |  | **5,450** |

## Fixed assumptions

* The functional gateway already returns typed accepted-or-failed evidence; a failed courier generation is a valid deterministic 60-second Wait policy result, not an operational failure.
* The injected `gateway` argument already available to `coordinate_player_turn` is the only gateway source for scheduled courier execution. Do not add global configuration or another runtime dependency.
* Replace the caretaker-only scheduled coordinator with a clearly named `coordinate_due_npc_activity(...)` entry point. It accepts the injected gateway. Update its internal callers and tests; do not retain a compatibility wrapper only for the old name.
* Keep one first-due activity per scheduler attempt. The new authored courier initial occurrence is time zero and follows the caretaker declaration, so it remains due after caretaker execution and is handled by the next attempt.
* Move only the courier proposal/output/result contracts required by durable trace decoding from `application.npc_decision` to a neutral top-level `llm_system.courier_decision` module, analogous to `player_interpretation`. Preserve current `llm_system.application` exports by re-exporting them from the policy module; do not move policy logic or gateway invocation out of `application.npc_decision`.
* Preserve `ScheduledActivityExecutionTrace` as the immutable caretaker V1 model. Introduce a separate strict `CourierScheduledActivityExecutionTrace` with `trace_schema_version=2`, exact courier `NpcScheduledActivity`, selection time, decision-context ID, simulation-step ID, and exact `CourierPolicyResult`. The stored scheduled-trace record type and decoder may accept the closed union of those two trace shapes.
* SQLite V5 is a transactional, non-rewriting capability migration: existing V4 table layout and stored JSON records remain intact; opening V4 advances only `PRAGMA user_version` to 5. Unknown future versions remain rejected.

## In scope

* Typed neutral courier decision contracts and their stable application exports.
* Courier scheduled trace contract, closed persistence decoding, and SQLite V5 migration/compatibility checks.
* One-due NPC coordinator dispatch for exactly the caretaker rule policy and courier LLM policy, with injected gateway for the courier path.
* Atomic courier action, queue removal, normal actor-action evidence, and linked courier functional-generation trace evidence.
* The second initial Greybridge courier occurrence, after caretaker.
* Targeted behavioral tests, version bump to `0.52.0`, and task handoff only.

## Out of scope

* Generic policy registries, other LLM NPCs, retries, recurrence, queue draining, background work, environmental or System-director execution.
* Memory, beliefs, narration, inspection API/UI, provider configuration, prompt changes, or player-facing response-model changes.
* Requirements, decisions, glossary, roadmap, task workflow, or other governance edits.

## Expected contracts and files

* `src/llm_system/courier_decision.py`: neutral strict courier proposal, generated-output, and policy-result contracts.
* `src/llm_system/application/npc_decision.py`: retain decision logic and re-export moved contracts.
* `src/llm_system/application/scheduled_execution_coordinator.py`: replace the caretaker-only entry point with `coordinate_due_npc_activity` and retain the existing typed result union/error semantics.
* `src/llm_system/application/player_turn_coordinator.py` and `src/llm_system/application/__init__.py`: use/export the replacement entry point.
* `src/llm_system/simulation/traces.py`, `src/llm_system/persistence/records.py`, `src/llm_system/persistence/sqlite.py`, and package exports: represent and decode the closed scheduled-trace union; enforce the courier trace link to the stored actor-action trace.
* Scenario YAML and affected lifecycle/package tests: author the courier occurrence after caretaker.
* `tests/test_scheduled_execution.py`, `tests/test_player_turn_coordinator.py`, `tests/test_sqlite_persistence.py`, and potentially a focused new trace test.

## Acceptance criteria

1. `coordinate_due_npc_activity` selects at most one first due item. It executes only matching authored caretaker or courier NPC policies, rejects an unsupported first-due item without writes, and preserves existing typed no-activity, stale, and operational-failure behavior.
2. Courier policy evaluation receives the caller-injected gateway and happens after the read-only selection but before the recheck write unit. A gateway exception leaves every persistent record unchanged; a typed failed generation commits the courier's deterministic Wait fallback and retains its failure evidence.
3. An unchanged courier selection atomically removes exactly that activity, commits the normal action/world/events/actor trace, and appends exactly one `CourierScheduledActivityExecutionTrace`. Its stored result must retain the exact functional-generation evidence and match the committed actor trace's decision-context and proposal.
4. Existing caretaker V1 trace payloads remain decodable and unchanged. SQLite opens fresh and V1–V4 databases at V5, preserves real V4 records without rewriting, rejects a future V6 version, and reset clears both trace shapes.
5. Greybridge create/reset produces caretaker then courier as equal-time activities in authored insertion order. Player-turn progress runs only the caretaker on its first attempt and runs only courier on the next attempt, without interpreting that later submitted text.
6. All tests are deterministic fakes; no live model or network call is needed. The project version is `0.52.0`.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv run pytest tests/test_courier_policy.py tests/test_scheduled_execution.py tests/test_player_turn_coordinator.py tests/test_sqlite_persistence.py`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if this requires an unaccepted trace shape other than the two fixed variants, a change to player-facing response semantics, a global gateway source, an incompatible SQLite data rewrite, or execution of a non-courier/non-caretaker activity.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
