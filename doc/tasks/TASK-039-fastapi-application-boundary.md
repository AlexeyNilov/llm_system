# TASK-039: Add the minimal FastAPI application boundary

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-037 and TASK-038

## Objective

Expose the accepted singleton lifecycle and atomic actor-action coordinator through a minimal FastAPI application factory. The boundary must turn an untrusted typed player proposal into a server-owned trusted submission and return only player-safe structured results after durable completion.

The API is an application seam for the next deterministic Streamlit task, not a text interpreter, narrator, inspection service, or general administration framework.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Action proposal`, `Proposal submission`, `Canonical`, `Primary persistence`, and `Validated world state`
* `doc/requirements.md`: `WORLD-001` through `WORLD-004`, `ACTION-001` through `ACTION-010`, `ACTION-024` through `ACTION-033`, `STORE-004`, `STORE-008`, `LIFECYCLE-003` through `LIFECYCLE-008`, `STEP-001` through `STEP-010`, and `API-001` through `API-009`
* `doc/decisions.md`: `Give one application transaction ownership of step completion`, `Compose the first coordinator before scheduled execution`, `Use explicit create, resume, and destructive development-reset operations`, and `Keep trusted turn metadata on the server side of the first HTTP boundary`
* `doc/high_level_design.md`: `Logical architecture`, `Component responsibilities`: `FastAPI application API` and `Turn coordinator`, and `Persistence and consistency`
* Initial source entrypoints: `src/llm_system/application/actor_action_step.py`, `src/llm_system/application/world_lifecycle.py`, `src/llm_system/application/__init__.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/traces.py`, `src/llm_system/game_packages/entities.py`, and `src/llm_system/persistence/errors.py`
* Initial test entrypoints: `tests/test_actor_action_step.py`, `tests/test_world_lifecycle.py`, and `tests/test_package.py`
* Concrete package fixture: `game_packages/rules/greybridge-rules/0.2.0/` and `game_packages/scenarios/storm-at-greybridge/0.2.0/`
* Project boundary: `pyproject.toml`, `uv.lock`, and `Makefile`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, other role guides, or planning-chat history. Inspect additional source or tests only when tracing a dependency from the named entrypoints.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 400 |
| Role guide | Implementation and TDD procedure | `doc/agent_roles/implementer.md` | 380 |
| Task brief | Execution contract | This file | 2,450 |
| Glossary | Trust and persistence vocabulary | Five named entries | 180 |
| Requirements | Existing service behavior and new HTTP contract | Named ID ranges above | 2,000 |
| Decisions | Transaction, lifecycle, coordinator, and trust choices | Four named entries | 1,350 |
| High-level design | API ownership and flow | Named sections | 450 |
| **Total before source exploration** |  |  | **7,210** |

Source and tests discovered while tracing the named implementation path are excluded from this pre-code documentation budget.

## Fixed assumptions

* Add one focused API module with a FastAPI application factory. Do not introduce a service container, repository abstraction, command bus, middleware framework, environment-settings library, or module-global mutable runtime.
* The factory receives an existing `SQLiteStore`, configured game-package root, validated initial package pair, an optional zero-argument UUID factory defaulting to UUID4, and an explicit development-reset-enabled boolean defaulting to false.
* Expose exactly `POST /world`, `GET /world`, `POST /development/reset`, and `POST /turn`. Do not add aliases, version prefixes, health, inspection, event-history, trace-history, or direct state routes in this task.
* `POST /world` and enabled reset have empty request bodies and use one server-assigned world UUID. `GET /world` uses exact recorded-package resume. All three return the same strict lifecycle metadata: world UUID, revision, simulation time, and exact rule/scenario package references. They never return `ActiveWorld`, package contents, canonical state, the scheduled queue, events, or traces.
* Disabled reset fails with `403` and a stable non-secret error code without invoking lifecycle behavior or consuming an identity. Enabled reset invokes only `reset_world_for_development` with the configured initial packages and one server-assigned UUID.
* `POST /turn` accepts a strict object containing exactly `proposal: ActorActionProposal`. It resumes the current world, derives the sole player definition from the validated scenario, creates one `ActorActionSubmission` with a `PlayerInterpreterActionSource` whose fixed non-secret `interpreter_id` is `structured-api`, and calls `execute_actor_action_step`.
* The turn path consumes exactly five UUIDs in this order: proposal, simulation step, decision context, outcome, and event. Clients cannot provide these IDs, source, actor, packages, world revision, or canonical effects. The injected factory exists for deterministic tests, not for exposing identity selection over HTTP.
* Return a strict turn result with world UUID, resulting revision, simulation-step UUID, outcome status, reason code, current perception, and self-event feedback taken from the completed trace. Do not return the proposal/submission, outcome ID, state changes, raw canonical event list, full outcome, full trace, package data, or scheduled queue.
* Return `200` for all durably completed domain outcomes, including rejected and failed. Map `MissingWorldError` to `404` with code `world-not-found`, `ExistingWorldError` to `409` with code `world-already-exists`, and disabled reset to `403` with code `development-reset-disabled`. Let FastAPI produce `422` for malformed inputs. Do not catch unexpected failures or expose their details in a custom response.
* Use a small strict application-owned error body for the three mapped errors. Do not globally replace FastAPI validation responses or add a general exception taxonomy.
* Add FastAPI as the narrowly bounded runtime dependency and HTTPX as a development dependency for in-process API tests. Do not add `fastapi[standard]`, Uvicorn, an environment loader, ORM, authentication library, or Streamlit.

## In scope

* Strict API request, lifecycle response, turn response, and mapped-error models.
* A dependency-explicit FastAPI application factory composing accepted lifecycle and actor-action services.
* Deterministic in-process HTTP tests against real temporary SQLite and real Greybridge `0.2.0` packages.
* OpenAPI evidence that the turn request is the discriminated proposal union and does not expose trusted metadata.
* Runtime/development dependency lock changes and a minor project version bump.

## Out of scope

* Free-form player text, thoughts, interpretation, LLM calls, narration, or System notifications.
* Scheduled-activity selection or execution, NPC policies, director behavior, memory, beliefs, or randomness.
* Streamlit, inspection APIs, event/trace browsing, canonical-state reads, direct mutation, or package administration.
* Production authentication, authorization, CSRF/CORS policy, rate limits, retries, idempotency keys, deployment entrypoints, Uvicorn, environment configuration, or multiple worlds.
* Changes to lifecycle, coordinator, kernel, persistence semantics, SQLite schema, package schemas, scenario content, or canonical events.
* Governance-document changes.

## Expected contracts and files

Likely additions or changes:

* `src/llm_system/api.py` and public application exports if useful;
* `tests/test_api.py`;
* `tests/test_package.py`, `pyproject.toml`, and `uv.lock` for version `0.37.0`; and
* this task brief for handoff only.

Prefer a public factory equivalent to:

`create_app(*, store: SQLiteStore, package_root: Path, initial_packages: ValidatedGamePackages, identity_factory: Callable[[], UUID] = uuid4, development_reset_enabled: bool = False) -> FastAPI`

Application-owned response models may be public when needed for FastAPI schema generation and client typing. Keep internal route wiring private.

## Acceptance criteria

1. The application factory has no mutable global runtime and injects all configured resources. Constructing it does not create, resume, reset, or advance a world. (`API-001`)
2. `POST /world` consumes one injected UUID, durably creates the configured initial world, and returns only exact lifecycle metadata. Repeating it returns `409` with code `world-already-exists` without changing stored data. (`API-002`, `API-007`)
3. `GET /world` returns equal lifecycle metadata after reopening the same SQLite database, performs exact recorded-version resolution, and does not change revision or histories. A missing world returns `404` with code `world-not-found`. (`API-003`, `API-007`)
4. Disabled `POST /development/reset` returns `403` with code `development-reset-disabled`, does not consume an identity, and changes nothing. Enabled reset consumes one UUID, atomically replaces the timeline, and returns replacement lifecycle metadata only. (`API-004`, `API-007`)
5. `POST /turn` accepts each existing proposal variant through the discriminated request schema but accepts no extra fields or trusted envelope fields. OpenAPI exposes the proposal discriminator and no client fields for actor/source/proposal ID/step ID/context ID/outcome ID/event ID. (`ACTION-001`, `API-005`)
6. A real Greybridge turn binds the proposal to `player`, records source `player_interpreter` with interpreter `structured-api`, consumes five UUIDs in the fixed order, commits through the coordinator, and returns matching revision, step ID, status, reason, current player perception, and self-event feedback without forbidden canonical or provenance fields. (`STEP-001` through `STEP-010`, `API-005`, `API-006`)
7. A rejected action is returned as HTTP `200` with structured rejected status/reason and still advances the durable revision and trace exactly as the coordinator specifies. It is not mapped to transport failure. (`STEP-006`, `API-007`)
8. Missing-world turn returns the mapped `404` without consuming turn identities or writing data. Request validation returns `422` for malformed variants, unknown operations, extra request or proposal fields, and client attempts to supply trusted metadata. (`API-005`, `API-007`)
9. Unexpected service failures propagate to FastAPI's normal server-error handling in the deployed ASGI boundary, do not expose application-formatted exception details, and preserve underlying transactional behavior. (`API-008`)
10. No endpoint returns canonical state, scheduled activities, state changes, package contents, other-actor private data, raw history, or a complete trace. No endpoint interprets text or invokes deferred components. (`API-006`, `API-009`)
11. `pyproject.toml` and `uv.lock` record version `0.37.0`, FastAPI as a bounded runtime dependency, and HTTPX as a development dependency without unrelated drift.

## Required verification

Follow TDD and record the first focused behavioral-test failure before implementation logic.

Run:

* `uv sync --locked`
* `uv run pytest tests/test_api.py tests/test_actor_action_step.py tests/test_world_lifecycle.py`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires:

* client-supplied actor, source provenance, runtime UUID, world revision, or canonical effects;
* exposing canonical state, scheduled work, state changes, complete traces, or other actors' private information;
* changing lifecycle, coordinator, persistence, kernel, package, scenario, or event semantics;
* text interpretation, narration, LLM or policy calls, scheduled execution, or inspection history;
* production authentication, a deployment server, environment configuration, generic dependency injection, middleware infrastructure, or another runtime dependency; or
* broad exception handling that turns unexpected failures into successful or detail-leaking responses.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented the minimal dependency-explicit FastAPI application factory with exactly the four accepted HTTP operations, strict player-safe request and response models, server-owned trusted turn metadata, deterministic identity injection, create-route-only conflict mapping, and no module-global mutable runtime. Default OpenAPI, Swagger UI, and ReDoc HTTP routes are disabled while programmatic `app.openapi()` schema generation remains available.

**Changed files:** `src/llm_system/api.py`; `tests/test_api.py`; `tests/test_package.py`; `pyproject.toml`; `uv.lock`; `doc/tasks/TASK-039-fastapi-application-boundary.md`.

**Verification:** TDD red recorded first: `uv run pytest tests/test_api.py -q` failed during collection with `ModuleNotFoundError: No module named 'fastapi'`. After implementation and review-finding corrections: `uv sync --locked` passed; `uv run pytest tests/test_api.py tests/test_actor_action_step.py tests/test_world_lifecycle.py` passed (40 tests); `make format` passed; `make lint` passed; the first review-correction `make mypy` run identified an optional `APIRoute.methods` annotation in the new route-surface test, which was corrected, and the rerun passed; `make test` passed (370 tests); `make check` passed (format check, lint, mypy, and 370 tests); `uv lock --check` passed; `git diff --check` passed. FastAPI's TestClient emitted one upstream Starlette deprecation warning recommending a future `httpx2` package, but all required checks passed with the task-authorized HTTPX dependency. The reset failure regression uses a real SQLite trigger to abort replacement insertion after timeline deletion starts, observes a detail-free HTTP 500, and verifies the prior world, events, and traces remain recoverable.

**Context used:** `AGENTS.md`; `doc/agent_roles/implementer.md`; `doc/agent_workflow.md`; `doc/glossary.md` entries `Action proposal`, `Action proposal submission`, `Canonical`, `Primary persistence`, `Validated game packages`, and `Validated world state`; `doc/requirements.md` named WORLD, ACTION, STORE, LIFECYCLE, STEP, and API extracts; `doc/decisions.md` entries `Give one application transaction ownership of step completion`, `Compose the first coordinator before scheduled execution`, `Keep trusted turn metadata on the server side of the first HTTP boundary`, and `Use explicit create, resume, and destructive development-reset operations`; `doc/high_level_design.md` named logical architecture, component responsibility, and persistence extracts; initial source entrypoints `src/llm_system/application/actor_action_step.py`, `src/llm_system/application/world_lifecycle.py`, `src/llm_system/application/__init__.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/traces.py`, `src/llm_system/game_packages/entities.py`, and `src/llm_system/persistence/errors.py`; initial test entrypoints `tests/test_actor_action_step.py`, `tests/test_world_lifecycle.py`, and `tests/test_package.py`; the Greybridge `0.2.0` package pair; `pyproject.toml`; `uv.lock`; and `Makefile`.

**Deviations:** None.

**Design gaps or follow-ups:** None required for this task. The upstream TestClient deprecation warning can be revisited when FastAPI/Starlette's HTTPX transition is part of an accepted dependency update; replacing the task-required HTTPX dependency now would exceed scope.
