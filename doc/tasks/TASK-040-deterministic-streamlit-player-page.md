# TASK-040: Add the deterministic Streamlit player page

**Status:** Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-039

## Objective

Add a runnable Streamlit player page that exercises the accepted FastAPI lifecycle and turn endpoints through deterministic structured controls and presentation. It must preserve the HTTP trust boundary and show only validated committed results.

This closes M4 with an honest player-facing seam. Free-form thoughts, LLM interpretation, narration, System notifications, autonomous actors, and inspection remain later work.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Action proposal`, `Canonical`, `Perception`, `Primary persistence`, and `System interface`
* `doc/requirements.md`: `ACTION-001` through `ACTION-010`, `API-001` through `API-009`, `PLAYERPAGE-001` through `PLAYERPAGE-008`, and `DEV-002` through `DEV-006`
* `doc/decisions.md`: `Keep trusted turn metadata on the server side of the first HTTP boundary` and `Begin Streamlit as a thin deterministic HTTP client`
* `doc/high_level_design.md`: `Logical architecture`, `Component responsibilities`: `Streamlit interface` and `FastAPI application API`, and `Persistence and consistency`
* Initial source entrypoints: `src/llm_system/api.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/perception.py`, and `src/llm_system/simulation/events.py`
* Initial test entrypoints: `tests/test_api.py` and `tests/test_package.py`
* Project boundary: `pyproject.toml`, `uv.lock`, and `Makefile`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, other role guides, initial scenario, package files, persistence code, or planning-chat history. Inspect additional source or tests only when tracing a dependency from the named entrypoints.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 400 |
| Role guide | Implementation and TDD procedure | `doc/agent_roles/implementer.md` | 380 |
| Task brief | Execution contract | This file | 2,450 |
| Glossary | Authority and presentation vocabulary | Five named entries | 180 |
| Requirements | Proposal, API, page, and development behavior | Named ID ranges above | 1,650 |
| Decisions | HTTP trust and thin-client choices | Two named entries | 750 |
| High-level design | UI/API ownership and consistency | Named sections | 500 |
| **Total before source exploration** |  |  | **6,310** |

Source and tests discovered while tracing the named implementation path are excluded from this pre-code documentation budget.

## Fixed assumptions

* Add one small player-page module and, if clearer, one adjacent HTTP-client module. The Streamlit layer may construct proposals and present responses but contains no simulation, package, persistence, narration, or answer-generation logic.
* Define a narrow player API protocol with create, resume, development reset, and turn methods. The Streamlit render function receives that protocol so page behavior can be tested without a live server. The default entrypoint constructs the real HTTP client.
* Configure the default client with `LLM_SYSTEM_API_URL`, defaulting to `http://127.0.0.1:8000`, and a five-second request timeout. Normalize only a trailing slash; do not add environment-settings libraries, server discovery, retries, authentication, or deployment bootstrap.
* Use `httpx2` for the synchronous HTTP client and move the already accepted dependency from development-only to runtime. Validate `200` bodies with `LifecycleResponse` or `TurnResponse`, and mapped error bodies with `ApplicationErrorResponse`. Treat transport errors, invalid JSON/schema, unknown status/code combinations, and unexpected statuses as a safe client failure that does not expose arbitrary server response text.
* Add Streamlit as the only new dependency. Do not add a UI framework, state library, templating engine, web server, or plotting dependency.
* On each rerun, resume through `GET /world`. A `world-not-found` response presents one Create world button. Successful create clears presentation history and reruns. Other failures show an error and do not claim a world exists.
* An active-world header shows only world UUID, revision, simulation time, and exact rule/scenario package references returned by lifecycle metadata.
* Provide one action selector with all seven operations in this order: Observe, Move, Speak, Take, Use, Help, Wait. Render only the selected operation's fields. Observe supports surroundings, location, connection, character, or object targets; Use supports location, connection, character, or object targets. Other fields correspond exactly to the existing proposal contracts.
* Convert non-surroundings target input deterministically to the selected target type. Reject blank identifiers or utterance and non-positive Wait duration locally with a visible message and no HTTP request. Do not accept raw JSON, actor/source fields, UUIDs, thoughts, or a generic text action.
* On turn submit, show progress while awaiting the API and append a history item only from a validated `200` `TurnResponse`. Render outcome status and reason, then current observations in returned order and self-event feedback in returned order using stable human-readable labels derived only from returned typed fields. Do not fabricate prose or hide a rejected/failed status.
* Store validated `TurnResponse` values as an ordered tuple or list under one namespaced `st.session_state` key. Do not send history to the API. Clear it after successful create or reset.
* Development reset is visually separate from player actions and requires an unchecked-by-default confirmation control plus a Reset world button. A disabled-reset `403` remains a visible application error; success clears history and reruns.
* Provide a `player-page` Make target that runs the Streamlit entrypoint and document the API URL prerequisite and command concisely in README. Do not add an API server command or imply that this task supplies deployment bootstrap.

## In scope

* A strict synchronous HTTP client for the four accepted API operations.
* A thin, injectable Streamlit player page with lifecycle controls, all typed action forms, deterministic committed-result presentation, and session-only history.
* HTTP client tests using in-process mock transport and Streamlit interaction tests without a live API or Streamlit server.
* One local page Make target and concise README setup/status updates.
* Runtime dependency lock changes and a minor version bump.

## Out of scope

* Starting/configuring FastAPI or Uvicorn, combined-process execution, health checks, server discovery, production deployment, authentication, CORS, retries, or idempotency.
* Free-form thoughts/actions, player input interpretation, LLM calls, narration, System notifications, generated prose, NPC activity, director activity, memory, or beliefs.
* Inspection pages, canonical state/history, traces, map visualization, generated images, CSS themes, responsive design work, accessibility audit, localization, or browser end-to-end automation.
* Direct imports or calls to application lifecycle/coordinator functions, package loading, SQLite, persistence repositories, or simulation resolution.
* Changes to API, application, kernel, persistence, package, scenario, event, or perception contracts.
* Governance-document changes.

## Expected contracts and files

Likely additions or changes:

* `src/llm_system/player_page.py` and optionally `src/llm_system/player_api.py`;
* `tests/test_player_page.py` and optionally focused client tests;
* `Makefile` and `README.md` for the runnable local page;
* `tests/test_package.py`, `pyproject.toml`, and `uv.lock` for version `0.38.0`; and
* this task brief for handoff only.

Prefer public boundaries equivalent to:

* `class PlayerApi(Protocol): ...` with typed lifecycle and turn methods;
* `class HttpPlayerApi` constructed from base URL, timeout, and optionally an injected `httpx2.Client` or transport for tests; and
* `render_player_page(api: PlayerApi) -> None`, with `main()` responsible only for configuration and construction.

Keep formatting helpers pure where practical. Do not re-export page internals from the package root.

## Acceptance criteria

1. Importing the page performs no HTTP call, Streamlit render, filesystem access, package load, or authoritative operation. `main()` constructs only the configured HTTP client and delegates to the render function. (`PLAYERPAGE-001`, `PLAYERPAGE-002`)
2. The real client sends exactly `GET /world`, empty `POST /world`, empty `POST /development/reset`, and `POST /turn` with exactly `{"proposal": ...}`. It uses the configured base URL/timeout and validates every recognized body into the existing API models. (`API-002` through `API-007`, `PLAYERPAGE-001`, `PLAYERPAGE-002`)
3. Mapped API errors retain HTTP status and stable code without arbitrary response detail. Transport, malformed body, and unexpected status failures use a distinct safe client error. No failure is returned as a successful lifecycle or turn model. (`API-007`, `API-008`, `PLAYERPAGE-002`, `PLAYERPAGE-007`)
4. Missing world shows Create world; successful creation reruns into lifecycle metadata and clears history. Active lifecycle metadata contains no state, scheduled work, trace, or package contents. (`PLAYERPAGE-003`, `PLAYERPAGE-006`)
5. Every operation selector branch produces exactly its accepted discriminated proposal shape. Local incomplete input sends nothing and displays failure. The page contains no free-form thought/action box, raw JSON editor, actor/source selector, UUID input, or direct state control. (`ACTION-001`, `PLAYERPAGE-003`, `PLAYERPAGE-004`)
6. A validated completed turn is appended once in response order and displayed with exact status/reason, ordered current observations, and ordered self-event feedback. Rejected and failed outcomes remain visibly completed domain results. (`PLAYERPAGE-005`, `PLAYERPAGE-006`)
7. Transport, schema, mapped application, or unexpected HTTP failure appends no history, does not advance displayed metadata, and presents no invented success. (`PLAYERPAGE-007`)
8. Reset is separate, confirmation-gated, and unchecked by default. Disabled reset remains an error; successful reset clears history and reruns. The page cannot edit canonical state directly. (`PLAYERPAGE-003`, `PLAYERPAGE-006`, `PLAYERPAGE-007`)
9. Page and client tests require no live API, Streamlit server, LLM, SQLite, package load, or network. Tests assert structured widgets, submitted payloads, state transitions, and typed presentation rather than incidental framework markup or exact generated prose. (`DEV-006`)
10. The implementation contains no simulation rule, direct application/persistence path, narration, inspection, deployment bootstrap, retry framework, authentication, custom CSS, or speculative UI architecture. (`PLAYERPAGE-001`, `PLAYERPAGE-008`)
11. `make player-page` runs the page entrypoint; README states the separate API prerequisite and `LLM_SYSTEM_API_URL` override without claiming an API launch command. `pyproject.toml` and `uv.lock` record version `0.38.0`, Streamlit runtime, and `httpx2` runtime without unrelated drift.

## Required verification

Follow TDD and record the first focused behavioral-test failure before implementation logic.

Run:

* `uv sync --locked`
* `uv run pytest tests/test_player_page.py tests/test_api.py`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires:

* direct application, package, simulation, SQLite, or persistence access from the player page;
* an API contract change or client-supplied trusted metadata;
* free-form interpretation, narration, LLM calls, NPC/System execution, inspection data, or canonical history;
* starting an ASGI server, adding deployment/authentication/retry infrastructure, or combining API and UI processes;
* another runtime dependency beyond Streamlit or promotion of the existing `httpx2`; or
* tests that require a live service, external network, browser automation, or model endpoint.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Implemented the deterministic Streamlit player page, strict synchronous HTTP client with explicit owned-resource cleanup, typed action controls, validated committed-result history, lifecycle and reset controls, local runner target, and runtime dependency/version updates. Review findings were resolved with owned-versus-injected client lifecycle evidence, page-level failed-turn/reset history preservation, and complete Observe/Use target-shape coverage.

**Changed files:** `src/llm_system/player_api.py`, `src/llm_system/player_page.py`, `tests/test_player_page.py`, `tests/test_package.py`, `Makefile`, `README.md`, `pyproject.toml`, `uv.lock`, and this task brief.

**Verification:** TDD first failure recorded: `uv run pytest tests/test_player_page.py -q` failed during collection with `ModuleNotFoundError: No module named 'llm_system.player_api'`. After resolving review findings, passed `uv sync --locked`; `uv run pytest tests/test_player_page.py tests/test_api.py` (57 passed); `make format`; `make lint`; `make mypy`; `make test` (406 passed); `make check` (format, lint, mypy, and 406 tests passed); `uv lock --check`; and `git diff --check`.

**Context used:** `AGENTS.md`; `doc/agent_roles/implementer.md`; this task brief; the named Action proposal, Canonical, Perception snapshot, Primary persistence, and System interface glossary entries; requirements `ACTION-001` through `ACTION-010`, `API-001` through `API-009`, `PLAYERPAGE-001` through `PLAYERPAGE-008`, and `DEV-002` through `DEV-006`; the named trusted-turn-metadata and thin-Streamlit-client decisions; the named logical architecture, Streamlit/API responsibilities, and persistence/consistency design extracts; `src/llm_system/api.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/perception.py`, `src/llm_system/simulation/events.py`, `tests/test_api.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `Makefile`.

**Deviations:** None.

**Design gaps or follow-ups:** None.
