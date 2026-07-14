# Codex task state

## Current objective

Plan the player input interpreter that maps explicit free-form input to the existing action-proposal boundary or a safe clarification result.

## Verified baseline

* M4 is complete: the singleton world persists and advances atomically through FastAPI, and the deterministic Streamlit page remains a thin HTTP client.
* TASK-041 is accepted at project version `0.40.0`.
* `NpcDecisionContext` is a strict immutable application contract containing only application identity, NPC identity context, goals, current plan, and actor-matching perception.
* `decide_greybridge_caretaker` is a pure deterministic proposal producer that uses typed observations for the seek, take, return, and reinforce sequence and falls back to a 60-second Wait.
* The policy receives no canonical world state, creates no trusted submission metadata, makes no LLM call, and performs no mutation or execution.
* TASK-042 is accepted at project version `0.41.0`.
* `HttpLocalModelGateway` uses explicit local configuration and the existing synchronous `httpx2` transport; no live service, new dependency, or environment loader was added.
* Functional calls disable Gemma thinking, request JSON-object syntax, validate only stopped non-blank `message.content` strictly, and make exactly one repair for invalid output.
* Typed immutable results preserve ordered attempt evidence; operational failures do not repair or expose provider details, and role-specific fallback remains outside the gateway.
* Parent verification passes: 56 focused/regression tests, `make check` with 437 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

No known blocker to planning the player interpreter. The contract must distinguish private thought, speech, one optional action proposal, and clarification without inventing player motives or trusted identities. API/UI text integration should follow after the interpreter service itself is accepted.

## Exact next action

Inspect `PLAY-001` and `PLAY-002`, player/time/LLM failure requirements, the existing action proposal union, perception context, and API trust boundary. Settle the smallest strict interpretation result and safe-failure mapping, then prepare TASK-043.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M5
4. `doc/requirements.md`: player interaction, time, action proposal, and LLM failure extracts
5. `doc/high_level_design.md`: “Player input interpreter” and context envelope
6. `src/llm_system/application/model_gateway.py`
7. `src/llm_system/simulation/actions.py`
8. `src/llm_system/api.py`: current player turn trust boundary
