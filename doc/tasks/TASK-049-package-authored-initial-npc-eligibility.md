# TASK-049: Materialize initial NPC eligibility from scenario packages

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-038 and TASK-048

## Objective

New and development-reset Greybridge worlds persist one package-authored,
one-shot caretaker NPC activity eligible at simulation time zero. It is only
durable eligibility data: this task does not select or execute it.

## Context manifest

Read only `AGENTS.md`; `doc/agent_roles/implementer.md`; glossary entries
“Scheduled activity”, “Scheduled activity queue”, “Scenario pack”, and “Actor
runtime”; requirements `SCHEDULE-007`--`SCHEDULE-014`, `SCHEDULE-024`--
`SCHEDULE-028`, and `WORLD-001`--`WORLD-006`; decisions “Author initial NPC
eligibility in scenario packages” and “Materialize initial state without
requiring future actor policies”; design sections “Game packages” and
“Persistence and consistency”; `game_packages/scenarios.py`,
`game_packages/validation.py`, `application/world_lifecycle.py`, and
`simulation/scheduling.py`; and the related scenario, validation, lifecycle,
and SQLite tests. Do not read orientation, planning, review, completed-task, or
chat-history artifacts.

## Context budget

| Context | Why required | Approximate words |
| --- | --- | ---: |
| Repository/role/task rules | Execution boundary | 2,050 |
| Vocabulary, requirements, decisions, design | Behavior and authority | 1,550 |
| Initial source/tests | Existing contracts | Source exploration |
| **Total before source exploration** |  | **3,600** |

## Fixed assumptions

* Add only ordered initial one-shot NPC declarations with
  `eligible_at_seconds` and `npc_id`; tuple order supplies insertion sequence
  beginning at zero.
* Derive activity UUIDs deterministically from supplied `world_id` and stable
  declaration identity. Do not author runtime IDs/sequences or use random UUIDs.
* Validate authored NPC references but not executable policy availability.
* Materialize only on create and development reset. Resume stays read-only;
  nothing selects, executes, consumes, or reschedules the queue.

## In scope

* Strict scenario schema and semantic validation for initial NPC declarations.
* Deterministic lifecycle materialization and Greybridge content with one
  caretaker occurrence due at time zero.
* Focused tests, exports if necessary, and project version bump to `0.47.0`.

## Out of scope

* Scheduled execution/consumption/retry/recurrence/traces, public HTTP/UI,
  LLM/courier/narrator/director/environment mechanics, persistence migration,
  dependencies, and configuration.
* Governance changes other than this brief’s status and handoff.

## Acceptance criteria

1. Strict parsing accepts only ordered initial NPC declarations; executable or
   runtime metadata is rejected (`SCHEDULE-024`).
2. Validation rejects missing/non-NPC references without requiring executable
   policies (`SCHEDULE-025`).
3. Create/reset persist a deterministic time-zero Greybridge caretaker queue
   entry with derived UUID and authored-order sequence (`SCHEDULE-026`--`027`).
4. Resume preserves the queue; no events/traces or scheduled execution occur
   (`SCHEDULE-027`--`028`).

## Required verification

* Write failing behavioral tests before implementation logic.
* `uv run pytest tests/test_scenario_pack_definition.py tests/test_game_package_validation.py tests/test_world_lifecycle.py tests/test_sqlite_persistence.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Stop conditions

Stop if execution, consumption, recurrence, policy availability at load time,
a persistence migration, or a public interface becomes necessary.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
