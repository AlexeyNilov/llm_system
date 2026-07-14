# TASK-057: Demote development reset control

**Status:** Ready

**Owner:** Implementer

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-056

## Objective

Keep free-form player chat as the main Streamlit experience by moving the
destructive development-reset UI into collapsed secondary developer tooling.
The existing confirmation, reset request, history clearing, and error behavior
must remain unchanged.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Presentation`, `Simulation`
* `doc/requirements.md`: `PLAYERPAGE-001` through `PLAYERPAGE-009`, `API-009` through `API-013`
* `doc/decisions.md`: `Replace structured player forms with the free-form player-turn chat boundary`; `Report committed player action when scheduled progress is pending`
* `src/llm_system/player_page.py`: `render_player_page`, `_render_player_turn_input`, `_render_development_reset`
* `tests/test_player_page.py`: player-page history, scheduled-progress, and reset tests

Do not read README, domain guide, roadmap, ideas, architect continuation state,
reviews, completed task briefs, or planning-chat history.

## Context budget

Use the soft 8,000-word pre-code documentation limit from
`doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 450 |
| Role guide | Implementation procedure | `implementer.md` | 1,350 |
| Task brief | Execution contract | This file | 900 |
| Glossary | Presentation vocabulary | named entries | 100 |
| Requirements | Player-page and HTTP boundaries | named IDs | 900 |
| Decisions | Current player-turn presentation behavior | named entries | 650 |
| **Total before source exploration** |  |  | **4,350** |

## Fixed assumptions

* `POST /development/reset`, `PlayerApi.reset_world`, and their API response
  contracts remain unchanged.
* Development reset remains available only after an active world is present.
* The page's main content order remains lifecycle metadata, returned chat
  history, then the sole free-form `st.chat_input`.
* Use native Streamlit layout only; no custom CSS, new dependency, page split,
  dialog, or client-side simulation path.

## In scope

* Put the existing reset UI inside one native collapsed expander labelled
  `Developer tools` after the main chat input.
* Retain the existing confirmation checkbox, disabled-until-confirmed reset
  button, request/error handling, history clearing, and rerun behavior.
* Add or update focused AppTest coverage proving reset is secondary and its
  confirmed and failed behavior is preserved.
* Bump `pyproject.toml` to the next semantic minor version.

## Out of scope

* Any player-turn, scheduler, API, persistence, model, narrator, scenario,
  authentication, or M6 behavior.
* Changing reset availability, confirmation wording/semantics, HTTP client
  calls, lifecycle data, or history semantics.
* README, roadmap, requirements, decisions, or other governance changes.

## Expected contracts and files

* Update `src/llm_system/player_page.py` only for native Streamlit hierarchy.
* Update `tests/test_player_page.py` to retain behavioral reset coverage and
  assert secondary placement/label.
* Update `pyproject.toml`, `uv.lock`, and the installed-version assertion
  following the established semantic-minor release pattern.

## Acceptance criteria

1. With an active world, player-facing main content presents lifecycle metadata,
   returned history, and exactly one free-form chat input; no reset control is
   rendered as a primary page section.
2. The reset controls are inside one collapsed `Developer tools` expander after
   the chat input. They retain the existing explicit confirmation requirement.
3. A confirmed reset makes the same `PlayerApi.reset_world` call, clears only
   session history after success, and reruns. A failed reset preserves history
   and shows the same safe mapped error.
4. No player-turn input, API, response schema, simulation, persistence, or
   narrator behavior changes.
5. Focused AppTest coverage, full suite, formatting, lint, type check, lock
   check, and diff check pass.

## Required verification

* Write a failing focused behavioral test before implementation logic.
* `uv run pytest tests/test_player_page.py`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if satisfying the hierarchy requires changing the
reset API, player-turn contract, confirmation semantics, adding a dependency,
or beginning any M6 scope.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
