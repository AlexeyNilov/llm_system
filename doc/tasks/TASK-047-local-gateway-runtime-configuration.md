# TASK-047: Configure the local gateway at server bootstrap

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-042 and TASK-046

## Objective

Enable live local player interpretation through optional, complete runtime environment configuration without moving environment access into application or simulation code.

## Context manifest

Read `AGENTS.md`, `doc/agent_roles/implementer.md`, requirements `API-010` through `API-012` and `LLM-010` through `LLM-016`, decisions “Build the first local gateway around functional structured output”, “Add a thin free-form player-turn HTTP boundary”, and “Configure the local gateway only at runtime bootstrap”, plus `server.py`, `api.py`, `application/model_gateway.py`, and their tests. No live endpoint.

## Fixed assumptions

* In `server.py` only, read all-or-none `LLM_SYSTEM_MODEL_BASE_URL`, `LLM_SYSTEM_MODEL`, `LLM_SYSTEM_MODEL_TIMEOUT_SECONDS`, and `LLM_SYSTEM_MODEL_MAX_TOKENS`.
* None means call `create_app` without a gateway. Complete valid values construct `HttpLocalModelGateway` and pass it as `gateway`. Partial, blank, nonpositive, noninteger, or invalid gateway settings raise `ValueError` before app creation.
* Add deterministic environment tests; update README local-LLM/runtime guidance. No `.env`, new dependency, API/coordinator/gateway behavior change, live call, UI, or version bump (runtime wiring only).

## Acceptance criteria

1. None, complete valid, partial, and invalid configurations have deterministic tested behavior.
2. Environment access is confined to bootstrap; configured gateway reaches `create_app` and absent config preserves safe fallback.
3. Tests, format, lint, mypy, lock, and diff checks pass.

## Required verification

* `uv run pytest tests/test_server.py tests/test_api.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending
