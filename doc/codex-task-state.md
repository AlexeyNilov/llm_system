# Codex task state

## Current objective

Implement and review TASK-038: deterministic initial-world creation, exact recorded-package resume, and atomic destructive development reset.

## Verified baseline

* The working tree was clean before TASK-038 planning.
* TASK-037 is accepted at project version `0.35.0`; SQLite V2 and the atomic actor-action coordinator are available.
* Initial runtime overlays and relational validation exist, but no application lifecycle service derives them from authored placements.
* Package loading accepts one exact directory; persistence records exact package identity and version without resolving files.

## Decisions settled for TASK-038

* Policy implementation availability moves from world creation to policy execution, avoiding a false M4 dependency on M5.
* Creation derives time-zero state in authored order, with all authored connections available, authored boolean initial values, and an empty scheduled queue.
* Resume resolves only recorded versions beneath a configured package root and performs no authoritative write.
* Development reset requires an existing world and atomically deletes the prior world, event history, and trace history before creating a caller-identified revision-0 world.

## Blockers and unresolved questions

None. Scheduled-activity execution remains deferred until its variants have accepted execution semantics.

## Exact next action

Commit the Ready TASK-038 planning artifacts, delegate the brief to a fresh implementer, then independently review its diff and verification evidence.

## Files to re-read before integration

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/tasks/TASK-038-world-lifecycle.md`
4. The TASK-038 implementation diff and handoff
5. `doc/roadmap.md`: M4
