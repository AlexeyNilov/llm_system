# Codex task state

## Current objective

Implement the transactional free-form player-turn coordinator before exposing its HTTP API.

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
* TASK-044 is accepted at project version `0.43.0`.
* Neutral immutable functional-generation and player-interpretation contracts preserve existing `llm_system.application` imports while allowing persistence to decode strict player-input records without importing application or HTTP code.
* `PlayerInputStepTrace` preserves exact interpretation evidence and has exactly thought-only, clarification, or action-linked completion forms. Action links must match an existing completed actor-action trace at the same world and resulting revision.
* SQLite V3 adds append-only player-input trace history, migrates V1/V2 records transactionally, and deletes that history during a development reset together with the existing timeline.
* Parent verification passes: targeted 85-test regression suite, `make check` with 477 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

TASK-045 is Ready. HTTP transport and local-gateway runtime configuration intentionally wait for the coordinator's player-safe, atomic completion contract.

## Exact next action

Commit and delegate `doc/tasks/TASK-045-transactional-freeform-player-turn-coordinator.md`, then independently review and integrate it before preparing the thin free-form HTTP endpoint.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/tasks/TASK-045-transactional-freeform-player-turn-coordinator.md`
4. `doc/requirements.md`: `PLAY-008` through `PLAY-013`, `LLM-008`, `STORE-006` through `STORE-016`, and `STEP-001` through `STEP-015`
5. `doc/decisions.md`: completed actor-action trace, player interpretation, player-input trace, and player-turn coordination decisions
6. `src/llm_system/application/actor_action_step.py`
7. `src/llm_system/application/player_interpreter.py`
8. `src/llm_system/persistence/sqlite.py`: unit of work and both trace repositories
9. `src/llm_system/player_input_traces.py`
10. `tests/test_actor_action_step.py`, `tests/test_player_input_traces.py`, and `tests/test_player_interpreter.py`
