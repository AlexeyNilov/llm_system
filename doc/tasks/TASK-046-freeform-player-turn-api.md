# TASK-046: Add the free-form player-turn API

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-045

## Objective

Expose strict `POST /player-turn` over `coordinate_player_turn`, without changing the existing structured `/turn` endpoint.

## Context manifest

Read only `AGENTS.md`, `doc/agent_roles/implementer.md`, glossary entries “Functional LLM role”, “Player-input trace”, and “Simulation step”; requirements `API-001` through `API-011`, `PLAY-008` through `PLAY-013`, and `STEP-011` through `STEP-015`; the decision “Add a thin free-form player-turn HTTP boundary”; and initial `api.py`, `player_turn_coordinator.py`, `test_api.py`, and `test_player_turn_coordinator.py`. Do not read planning history, API/UI guides, README, or contact a live model.

## Fixed assumptions

* Add strict `PlayerTurnRequest` with exactly `player_text: NonBlankText`.
* Add `POST /player-turn`; preserve `/turn` behavior and its request/response models exactly.
* `create_app` gains optional injected `FunctionalModelGateway`. If absent, use a local typed unavailable gateway returning a failed `FunctionalGenerationResult` with `TRANSPORT_UNAVAILABLE`; do not call HTTP or expose provider details.
* Bind the request only to `_sole_player(initial_packages)` and call `coordinate_player_turn` with configured packages and identity factory.
* Return strict discriminated models for thought-only, clarification, and action-completed results. Action includes only existing `TurnResponse`-equivalent player-safe fields plus optional private thought. Map stale to `409 {"code":"player-turn-stale"}`. Missing world retains `404`; malformed/extra input remains `422`.
* Do not add server provider configuration, UI, narration, retry, model settings, persistence writes outside the coordinator, or dependencies. Bump `0.44.0` to `0.45.0`.

## Acceptance criteria

1. Only player text crosses the HTTP boundary; no client trusted IDs, proposals, revisions, model settings, traces, or canonical state are accepted or returned.
2. Injected fake gateway proves all coordinator result mappings; absent gateway creates the existing durable safe clarification without live I/O.
3. Stale is bounded `409`; committed results return only after coordinator commit; `/turn` regressions remain green.
4. Focused API/coordinator tests, `make check`, lock, format, lint, mypy, and diff checks pass.

## Required verification

* `uv run pytest tests/test_api.py tests/test_player_turn_coordinator.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop for provider runtime configuration, UI, stale retry, changes to structured `/turn`, new dependencies, or an unaccepted response/security boundary.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
