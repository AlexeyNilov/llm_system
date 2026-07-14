# TASK-055: Render bounded player perception as narration

**Status:** Ready

**Owner:** Implementer

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-046, TASK-052, TASK-054

## Objective

Give the player a readable, deterministic world description after a committed
or settled player-turn result. The renderer uses only the player perception
already returned by the coordinator and approved authored display names for
identifiers already visible there; it never calls an LLM or changes simulation
truth.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: **canonical**, **narrator**, **perception snapshot**, **presentation**, **System interface**
* `doc/requirements.md`: `UI-002` through `UI-005`; `SPACE-005` through `SPACE-006`; `PERCEPTION-007` through `PERCEPTION-015`; `NARR-001` through `NARR-006`
* `doc/decisions.md`: “Separate the hidden System director from the visible System interface”, “Model space as a location graph with deterministic perception”, and “Start narration with deterministic perception rendering”
* `src/llm_system/simulation/perception.py`
* `src/llm_system/game_packages/validation.py`
* `src/llm_system/api.py`
* `src/llm_system/player_api.py`
* `src/llm_system/player_page.py`
* `tests/test_api.py` and `tests/test_player_page.py`
* `developing-with-streamlit` skill: read its `SKILL.md` and the `references/chat-ui.md` and `references/best-practices.md` references before modifying `player_page.py`.

Do not read README, domain guide, roadmap, ideas, reviews, completed task briefs,
architect continuation state, or planning-chat history.

## Context budget

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Execution boundaries and role routing | `AGENTS.md` | 500 |
| Role guide | TDD and scope rules | Implementer guide | 500 |
| Task contract | Fixed outcome | This file | 900 |
| Vocabulary and requirements | Information and presentation boundary | Named entries and IDs only | 1,700 |
| Decisions | Narrator authority and implementation choice | Three named decisions | 900 |
| Streamlit skill | Required chat-page procedure | Skill plus two named references | 1,600 |
| Initial source/tests | Trace response and page path | Named files | Excluded from pre-code documentation budget |
| **Total before source exploration** |  |  | **6,100** |

## Fixed assumptions

* The initial narrator is a pure deterministic renderer, not an LLM call and
  not a functional LLM role. Do not add a gateway method, model configuration,
  generation evidence, repair, prompt, narration persistence, or a new HTTP
  endpoint.
* Create a neutral top-level `llm_system.narration` module. Its public function
  shall accept validated packages plus one player-current `PerceptionSnapshot`
  and return a strict immutable `PlayerNarration` with one non-blank `text`.
* The function shall require the snapshot observer to be the one authored player
  and render exactly these snapshot groups in their snapshot order: current
  location, co-located characters, visible objects, and outgoing connections.
  It may use only package names for IDs that appear in those observations.
* Use a fixed readable grammar. Empty character or object groups are omitted;
  an empty connection group renders a fixed no-exits sentence. Event observations
  are outside this first renderer and must cause a bounded context error rather
  than being narrated from canonical payloads.
* Add `narration: NonBlankText` to the existing player-safe HTTP response
  variants carrying `current_perception`: action completed, action progress
  pending, and scheduled progress completed. The adapter computes it from the
  exact response perception and validated initial packages. Do not add it to
  thought-only, clarification, or scheduled-progress-pending variants.
* Replace raw current-perception observation rendering on the Streamlit player
  page with the returned narration. Preserve explicit outcome status, reason,
  private thought, self-event feedback, scheduled-progress status, session
  history behavior, and existing safety/error handling.

## In scope

* Pure deterministic narration contract and renderer.
* Player-turn response schema/adapter/client validation for existing perception
  variants.
* Streamlit chat rendering and high-signal tests.
* Version bump to `0.53.0` and task handoff only.

## Out of scope

* Any LLM, prompts, gateway changes, narration persistence, narration endpoint,
  streaming, System notifications, event narration, raw perception inspection,
  or mechanics changes.
* Requirements, decisions, glossary, roadmap, task workflow, or other
  governance edits.

## Expected contracts and files

* `src/llm_system/narration.py` and focused tests: strict pure renderer.
* `src/llm_system/api.py`, `src/llm_system/player_api.py`, and tests: extend
  only relevant player-safe response variants.
* `src/llm_system/player_page.py` and tests: render returned narration in the
  assistant chat message without direct state reconstruction.
* `pyproject.toml`, `uv.lock`, and version test.

## Acceptance criteria

1. Given valid Greybridge player perception, narration is deterministic,
   non-blank, readable, and names only observed location, characters, objects,
   and outgoing connections. It never exposes hidden possession or unobserved
   package records.
2. Invalid observer, unknown visible ID, missing current location, or event
   observation produces a typed bounded renderer error without fallback to
   canonical state or arbitrary package search.
3. `/player-turn` emits narration exactly where the response already carries
   current player perception; the text agrees with that snapshot and no
   narration appears in the other three response forms.
4. The Streamlit page renders returned narration and no longer renders raw
   current-perception IDs. It preserves player-safe status, thought, feedback,
   discarded-input, and error behaviors.
5. No model/network call is used by narration tests. Project version is `0.53.0`.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv run pytest tests/test_narration.py tests/test_api.py tests/test_player_page.py`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation needs an LLM or prompt, a new
presentation persistence model, unrestricted package/world lookup, narration of
event observations, a System notification, or a player-facing result not fixed
above.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list only the named documentation extracts and
initial source/test files actually consulted.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
