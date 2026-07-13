# Codex task state

## Current objective

Plan the next actionable M4 increment: world creation, resume, and development reset on top of the accepted SQLite V2 and atomic actor-action coordinator.

## Verified baseline

* TASK-037 is independently reviewed and accepted at project version `0.35.0`.
* The coordinator loads the singleton world, verifies exact supplied package ownership, validates runtime state, composes authorization through actor perception, and returns only after explicit SQLite commit.
* SQLite V2 atomically persists the next world revision, canonical events, and one strict completed actor-action trace; V1 world and event data migrate directly to V2.
* Rejected outcomes still receive one durable next revision and trace. The scheduled queue is preserved exactly.
* Independent verification passes: 19 focused tests, `make check` with 342 tests, `uv sync --locked`, `uv lock --check`, and `git diff --check`.

## Deferred boundary

Scheduled-activity execution is not the next actionable task. Environmental, NPC, and System-director activity variants have deterministic eligibility records but no accepted execution semantics; consuming them now would invent or lose work.

## Blockers and unresolved questions

No blocker to world lifecycle planning. The next brief must define initial-state construction, exact package selection/resume, and destructive development-reset behavior without weakening the one-world authority boundary.

## Exact next action

After committing accepted TASK-037 work, inspect existing package and runtime-state construction contracts, settle the minimal world lifecycle boundary, prepare TASK-038, then automatically commit and delegate it when Ready.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M4
4. `doc/high_level_design.md`: API boundary and persistence lifecycle
5. World, package, state, and persistence requirements and accepted decisions
6. `src/llm_system/game_packages/`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/validation.py`, and `src/llm_system/persistence/`
