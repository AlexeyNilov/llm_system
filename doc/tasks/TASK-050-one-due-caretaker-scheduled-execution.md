# TASK-050: Execute one due caretaker activity atomically

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-048 and TASK-049

## Objective

An application caller can process the first due caretaker activity: it is
selected deterministically, decided from bounded context outside a write unit,
then atomically consumed with the ordinary action result and linked scheduling
trace. No due activity returns a typed no-op; unsupported first activity is not
skipped.

## Context manifest

Read only `AGENTS.md`; `doc/agent_roles/implementer.md`; glossary entries
“Scheduled activity”, “Scheduled activity queue”, “Scheduled activity
selection”, “Scheduled activity execution trace”, and “Actor runtime”;
requirements `SCHEDULE-001`--`SCHEDULE-023` and `SCHEDULE-029`--`SCHEDULE-034`;
decisions “Serialize eligible activities deterministically”, “Compose the first
coordinator before scheduled execution”, “Start the actor runtime with one
revision-safe caretaker turn”, and “Consume one due caretaker activity with
linked durable evidence”; `simulation/scheduling.py`, `application/actor_action_step.py`,
`application/npc_turn_coordinator.py`, SQLite persistence, and related
scheduling/actor/persistence tests. Exclude orientation, planning, reviews,
completed briefs, and chat history.

## Context budget

| Context | Why required | Approximate words |
| --- | --- | ---: |
| Repository, role, and task rules | Execution boundary | 2,000 |
| Vocabulary, requirements, decisions | Scheduling authority and failure behavior | 1,800 |
| Source and tests | Existing composition and persistence contracts | Source exploration |
| **Total before source exploration** |  | **3,800** |

## Fixed assumptions

* Process only the first due activity from `select_eligible_activities`.
* Support only an authored caretaker `NpcScheduledActivity`; fail, do not skip,
  another due variant. Do not drain the queue, recur, or batch player turns.
* Run policy outside a write unit; recheck world identity, revision, and first
  due activity before trusted IDs or writes.
* Successful or rejected action removes exactly that activity and atomically
  appends existing action evidence plus one linked scheduling trace. Failure
  rolls everything back.
* Use SQLite schema V4 for a narrow append-only scheduling-trace table and
  direct V1/V2/V3 migration. No generic migration framework.

## In scope

* Typed scheduled-execution results, caretaker preparation reuse/refactor, and
  queue-aware in-unit action composition.
* Strict scheduling trace, persistence V4 migration/reset handling, and tests.
* Version bump to `0.48.0`.

## Out of scope

* Other activity variants, recurrence, full draining, player/API/UI batching,
  LLM courier, narrator, director, and new package authoring.

## Acceptance criteria

1. No due activity is a typed no-write result; an unsupported first due record
   fails without queue change (`SCHEDULE-029`--`030`).
2. Caretaker policy runs outside the write unit; stale selection creates no
   trusted IDs or writes (`SCHEDULE-031`).
3. Successful and rejected execution remove exactly the selected activity and
   atomically persist action and linked scheduling evidence (`SCHEDULE-032`--`033`).
4. V1/V2/V3 migration, reset, strict decode, and rollback protect all histories
   (`SCHEDULE-034`).

## Required verification

* Write failing behavioral tests before implementation.
* Focused new scheduled-execution and existing scheduling/NPC/persistence tests.
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Stop conditions

Stop if another activity variant, recurrence, queue draining, player batching,
or public interface is required.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
