# Codex task state

## Current objective

Deliver the player-facing free-form chat path over the accepted `/player-turn` API.

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
* TASK-045 is accepted at project version `0.44.0`.
* `coordinate_player_turn` reads perception outside a write transaction, rejects stale interpretations without identities or writes, and atomically commits either a no-action trace or the action/world/events/actor-trace/input-trace set.
* TASK-046 is accepted at project version `0.45.0`; `/player-turn` accepts only player text and maps coordinator results to player-safe HTTP responses.
* TASK-047 configures `HttpLocalModelGateway` only in `server.py`, from a complete all-or-none set of four explicit environment settings. Absent configuration retains the safe unavailable-gateway clarification path; partial, blank, or invalid values fail before app construction.
* Parent verification for TASK-047 passes: focused server/API tests (40 passed), `make check` (503 passed), format, lint, mypy, `uv lock --check`, and `git diff --check`.
* `select_eligible_activities` is pure and deliberately non-executing; the initial stored queue is empty and package schemas do not yet author scheduled runtime occurrences.
* The first executable actor-runtime seam is therefore one explicitly requested `bridge-caretaker` turn. Its policy/context phase remains non-mutating, while its coordinator rechecks the observed world revision before constructing a trusted NPC submission and calling the existing action-step composition.
* TASK-048 is accepted at project version `0.46.0`. `coordinate_caretaker_turn` supports only the authored matching caretaker rule policy, returns a strict completed-or-stale result, and preserves the scheduled queue exactly. Parent verification passes: focused coordinator/policy/action-step tests (31 passed), `make check` (510 passed), format, lint, mypy, `uv lock --check`, and `git diff --check`.
* TASK-049 is accepted at project version `0.47.0`. Scenario packages strictly declare initial NPC eligibility; create and reset materialize Greybridge's time-zero caretaker queue entry with a UUID derived from the caller-supplied world ID and declaration position. Parent verification passes: focused package/lifecycle/persistence tests (53 passed), `make check` (512 passed), format, lint, mypy, `uv lock --check`, and `git diff --check`.
* TASK-050 is accepted at project version `0.48.0`. `coordinate_due_caretaker_activity` selects only the first due activity, retains the policy-to-action decision-context identity, rechecks queue and revision, and atomically consumes a caretaker activity with normal action evidence plus one linked scheduled-activity trace. SQLite V4 migrates V1/V2/V3 and reset clears this history. Parent verification passes: `make check` (517 passed), format, lint, mypy, `uv lock --check`, and `git diff --check`.
* TASK-051 is accepted at project version `0.49.0`. `coordinate_player_turn` attempts one due caretaker activity after a committed action and before a later input is interpreted. Settled turns return the final player perception and revision; stale or operational scheduled execution returns a player-safe pending result without leaking NPC-private evidence. Parent verification passes: focused player-turn/scheduled/API tests (49 passed), `make check` (525 passed), format, lint, mypy, `uv lock --check`, and `git diff --check`.
* TASK-052 is Ready. It replaces the player page's typed proposal forms with a thin free-form chat client for the accepted player-turn API. The page must preserve the API's distinction between completed input and scheduled progress that deliberately discarded a later input.

## Blockers and unresolved questions

No blocker. Full queue draining, recurrence, environmental activity, System director hooks, and narration remain deferred.

## Exact next action

Commit and delegate TASK-052, then independently review the player-safe chat presentation and history behavior.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M5
4. `doc/requirements.md`: `API-010` through `API-013`, `PLAYERPAGE-001` through `PLAYERPAGE-008`, and `STEP-016` through `STEP-017`
5. `doc/decisions.md`: “Replace structured player forms with the free-form player-turn chat boundary”
6. `src/llm_system/player_page.py`, `src/llm_system/player_api.py`, `src/llm_system/api.py`, and `tests/test_player_page.py`
