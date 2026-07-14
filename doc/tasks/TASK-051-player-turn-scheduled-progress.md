# TASK-051: Report and settle scheduled progress around player turns

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-046 and TASK-050

## Objective

`POST /player-turn` honestly reports a committed player action when its required
post-action caretaker progress is pending. It settles one due caretaker activity
before returning normal action completion, or before interpreting later input.

## Context manifest

Read only `AGENTS.md`; `doc/agent_roles/implementer.md`; glossary entries
“Action proposal”, “Scheduled activity”, “Scheduled activity execution trace”,
and “Perception snapshot”; requirements `API-010`--`API-013`, `STEP-011`--
`STEP-017`, `TIME-005`, and `SCHEDULE-029`--`SCHEDULE-034`; decisions “Coordinate
a player turn around model latency and one commit”, “Add a thin free-form
player-turn HTTP boundary”, and “Report committed player action when scheduled
progress is pending”; `application/player_turn_coordinator.py`,
`scheduled_execution_coordinator.py`, `api.py`, and their tests. Exclude all
other orientation, planning, review, completed-task, and chat artifacts.

## Context budget

| Context | Why required | Approximate words |
| --- | --- | ---: |
| Repository, role, task rules | Execution boundary | 2,000 |
| Contracts and decisions | Completion and safe presentation | 1,600 |
| Source/tests | Existing player/scheduled seams | Source exploration |
| **Total before source exploration** |  | **3,600** |

## Fixed assumptions

* Keep player input trace/action atomicity unchanged; scheduled work is a later
  independently committed step.
* Attempt only one existing due caretaker activity. No queue drain, retries,
  background work, other variants, narration, or UI changes.
* A successful/no-due post-action result exposes final player perception and
  current revision. Stale/operational progress returns a strict committed-action
  pending result without NPC-private details.
* Before a new input is interpreted, attempt pending scheduled progress. A
  completed progress result discards that submitted text without persisting or
  interpreting it; no-due continues normal player handling.

## In scope

* Application result variants and coordinator composition; player-safe API
  response variants and tests; version bump to `0.49.0`.

## Out of scope

* Streamlit, narrator, generic scheduler, retries/background workers, queue
  draining, other activity variants, persistence schema changes, and new deps.

## Acceptance criteria

1. Post-action due completion/no-due returns final player perception/revision;
   pending honestly retains committed player action (`STEP-016`, `API-013`).
2. A later request settles due work before any interpreter call or input trace;
   completed progress returns a safe distinct result (`STEP-017`).
3. API responses expose no NPC private evidence and preserve stale player-input
   behavior. Tests cover all result variants and identity/trace preservation.

## Required verification

* Write failing behavioral tests before logic.
* `uv run pytest tests/test_player_turn_coordinator.py tests/test_scheduled_execution.py tests/test_api.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Stop conditions

Stop if retry policy, queue draining, another variant, public UI, narrator, or
a persistence migration becomes necessary.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
