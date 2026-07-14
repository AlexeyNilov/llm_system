# Codex task state

## Current objective

Plan the server-owned free-form player turn boundary that invokes interpretation and executes only a present proposal.

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

No known blocker to planning API integration. The boundary must project current player perception before interpretation, preserve server-owned identities, execute only a present proposal through the existing atomic coordinator, and return thought-only or clarification without advancing revision or simulation time. Streamlit text integration and narration remain later tasks.

## Exact next action

Inspect the FastAPI lifecycle and turn contracts, current-perception projection, interpreter result, identity factory, and atomic coordinator. Settle a strict free-text request and discriminated response that preserves the existing structured `/turn` compatibility while adding an honest non-committing path, then prepare TASK-044.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M5
4. `doc/requirements.md`: API, player interpretation, time, and trace extracts
5. `doc/high_level_design.md`: player interpreter and simulation-step flow
6. `src/llm_system/api.py`
7. `src/llm_system/application/player_interpreter.py`
8. `src/llm_system/application/actor_action_step.py`
9. `src/llm_system/simulation/perception_engine.py`
