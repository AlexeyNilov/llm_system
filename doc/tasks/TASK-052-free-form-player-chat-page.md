# TASK-052: Present free-form player turns in the Streamlit page

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-046 and TASK-051

## Objective

Make the existing Streamlit player page the usable client for the accepted
free-form `/player-turn` API. A player submits one thought or attempted action
as chat text and sees only validated, player-safe confirmed results.

## Context manifest

Read only `AGENTS.md`; `doc/agent_roles/implementer.md`; the required
`developing-with-streamlit` skill and its chat-UI and session-state references;
glossary entries “Perception snapshot”, “Player-input trace”, and “Scheduled
activity”; requirements `API-010`--`API-013`, `STEP-016`--`STEP-017`, and
`PLAYERPAGE-001`--`PLAYERPAGE-008`; decision “Replace structured player forms
with the free-form player-turn chat boundary”; `api.py`, `player_api.py`,
`player_page.py`, and `tests/test_player_page.py`. Exclude roadmap, ideas,
historical task briefs, narration, inspection, and other UI work.

## Context budget

| Context | Why required | Approximate words |
| --- | --- | ---: |
| Repository and implementation rules | Execution boundary | 2,000 |
| Streamlit chat and state guidance | Native chat/state behavior | 1,500 |
| API/page contracts and decision | Safe HTTP presentation | 1,700 |
| **Total before source exploration** |  | **5,200** |

## Fixed assumptions

* The page remains a thin HTTP client; server-owned interpretation, scheduling,
  persistence, and trusted metadata do not move to Streamlit.
* Replace rather than preserve the seven typed proposal controls in the player
  page. The legacy `/turn` endpoint remains outside this task.
* Present deterministic structured facts only. Narration, System notifications,
  streaming, inspection, new dependencies, and UI styling are out of scope.
* A scheduled-progress result that precedes interpretation must not retain or
  display the newly submitted player text as completed history.

## In scope

* Strict player API client request/response support for `POST /player-turn`,
  including mapped stale-input failure.
* Streamlit chat input, validated response presentation, and session-only
  history for all player-turn response variants.
* Replace obsolete proposal-form tests with behavioral HTTP and page coverage.
* Version bump to `0.50.0`.

## Out of scope

* Narrator, System notifications, streaming, UI restyling, inspection,
  structured `/turn` removal, gateway or scheduler changes, new dependencies,
  and governance changes other than this task's version/test artifacts.

## Expected contracts and files

* `PlayerApi` and `HttpPlayerApi` gain a typed text-to-player-turn operation;
  all successful HTTP bodies remain strictly validated against API models.
* `player_page.py` owns only presentation-state records and deterministic
  rendering of player-safe responses.
* Likely changes: `player_api.py`, `player_page.py`, `tests/test_player_page.py`,
  `tests/test_package.py`, `pyproject.toml`, and `uv.lock`.

## Acceptance criteria

1. The page sends a non-blank chat input only to `/player-turn`, never builds a
   proposal locally, and the HTTP client validates each strict response variant
   plus the mapped `player-turn-stale` error.
2. The page renders thought-only, clarification, settled action,
   action-progress-pending, scheduled-progress-completed, and
   scheduled-progress-pending results without NPC/private/provider/trace
   details. Fields absent from a variant are not invented.
3. Session-only chat history retains the user text only for responses that
   completed that input; a pre-interpretation scheduled-progress response shows
   its status but does not display or retain the discarded text.
4. Transport, malformed response, stale-input, and application errors remain
   visible failures and do not append history. Existing create/resume/reset
   behavior remains intact.

## Required verification

* Write failing behavioral tests before implementation logic.
* `uv run pytest tests/test_player_page.py tests/test_api.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Stop conditions

Stop and report a design gap if narrator text, a new API route, a scheduler
behavior change, a new dependency, persistent chat history, an inspection view,
or a direct application/persistence call becomes necessary.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
