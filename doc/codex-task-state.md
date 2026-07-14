# Codex task state

## Current objective

Implement durable player-input step traces so functional interpretation evidence survives both action and non-action inputs before the free-form API is exposed.

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
* TASK-043 is accepted at project version `0.42.0`.
* `PlayerInterpreterOutput` strictly represents explicit private thought plus at most one Observe, Move, Speak, Take, Use, or Wait proposal, or clarification; Help and trusted metadata are excluded.
* `interpret_player_input` sends only deterministic instructions, exact player text, and current ID-linked perception through the injected gateway and preserves generation evidence.
* Gateway failure maps to one fixed clarification, while accepted model clarification is preserved; the service creates no identity, submission, execution, time, persistence, or narration effects.
* Parent verification passes: 64 focused/regression tests, `make check` with 466 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

TASK-044 is Ready. Direct API integration intentionally waits for its accepted storage contract: the existing actor-action trace cannot retain required functional-generation evidence for thought-only, clarification, or interpreted-action paths. The task fixes the contract and persistence seam, but the later coordinator still owns observed-revision recheck and atomic player-turn completion.

## Exact next action

Commit and delegate `doc/tasks/TASK-044-durable-player-input-step-traces.md` to the configured fresh implementer. Independently review and integrate the result, then plan the player-turn coordinator and free-form API over the durable trace contract.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/tasks/TASK-044-durable-player-input-step-traces.md`
4. `doc/requirements.md`: `PLAY-008` through `PLAY-013`, `LLM-008`, and `STORE-007` through `STORE-016`
5. `doc/decisions.md`: minimal completed actor-action trace, SQLite V2, player interpretation, and player-input trace decisions
6. `src/llm_system/simulation/traces.py`
7. `src/llm_system/persistence/records.py`
8. `src/llm_system/persistence/sqlite.py`: schema, trace repository, and decoding
9. `src/llm_system/application/player_interpreter.py`
10. `src/llm_system/application/actor_action_step.py`
