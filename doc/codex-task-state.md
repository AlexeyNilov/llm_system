# Codex task state

## Current objective

Execute and integrate TASK-042: the local functional model gateway with strict validation evidence and one repair.

## Verified baseline

* M4 is complete: the singleton world persists and advances atomically through FastAPI, and the deterministic Streamlit page remains a thin HTTP client.
* TASK-041 is accepted at project version `0.40.0`.
* `NpcDecisionContext` is a strict immutable application contract containing only application identity, NPC identity context, goals, current plan, and actor-matching perception.
* `decide_greybridge_caretaker` is a pure deterministic proposal producer that uses typed observations for the seek, take, return, and reinforce sequence and falls back to a 60-second Wait.
* The policy receives no canonical world state, creates no trusted submission metadata, makes no LLM call, and performs no mutation or execution.
* Parent verification passes: 18 focused/regression tests, `make check` with 418 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

No known blocker. Actor-runtime assembly and scheduled caretaker execution remain separate M5 increments. Narrator prose support and role-specific safe-failure mapping remain outside TASK-042.

## Exact next action

Delegate the Ready TASK-042 to a fresh `implementer`, then independently review its request shape, strict content-only validation, one-repair bound, typed evidence, safe operational failures, resource ownership, and full verification.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M5
4. `doc/tasks/TASK-042-local-functional-model-gateway.md`
5. TASK-042's exact context manifest
6. The implementation diff and handoff evidence
