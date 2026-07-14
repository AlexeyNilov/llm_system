# Codex task state

## Current objective

Plan the local model gateway that will support the player interpreter, courier policy, and narrator without crossing simulation authority boundaries.

## Verified baseline

* M4 is complete: the singleton world persists and advances atomically through FastAPI, and the deterministic Streamlit page remains a thin HTTP client.
* TASK-041 is accepted at project version `0.40.0`.
* `NpcDecisionContext` is a strict immutable application contract containing only application identity, NPC identity context, goals, current plan, and actor-matching perception.
* `decide_greybridge_caretaker` is a pure deterministic proposal producer that uses typed observations for the seek, take, return, and reinforce sequence and falls back to a 60-second Wait.
* The policy receives no canonical world state, creates no trusted submission metadata, makes no LLM call, and performs no mutation or execution.
* Parent verification passes: 18 focused/regression tests, `make check` with 418 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

No known blocker to planning the local model gateway. Actor-runtime assembly and scheduled caretaker execution remain separate M5 increments. The gateway must preserve the accepted local Gemma thinking-disable, strict validation, one-repair, and role-specific safe-failure boundaries without importing simulation authority.

## Exact next action

Inspect the accepted structured-output preflight evidence, local-model decisions and requirements, current dependencies, and the three concrete M5 consumers. Settle the smallest shared transport and functional structured-output boundary, then prepare TASK-042 for the local model gateway.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M5
4. `doc/reports/structured_output_preflight.md`
5. `doc/requirements.md`: `LLM-001` through `LLM-009`
6. `doc/decisions.md`: local Gemma structured-output decisions
7. `README.md`: current local-model endpoint configuration only
