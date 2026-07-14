# TASK-056: Typed LLM narrator style planning

**Status:** Ready

**Owner:** Implementer

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-055

## Objective

Make the local model select a strict, non-authoritative narration style plan for
completed player-turn narration. Every factual sentence must still be rendered
deterministically from `PlayerNarrationContext`, with a safe default if the
model fails or selects an unsuitable plan.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: `Presentation`, `Perception snapshot`, `Functional LLM role`
* `doc/requirements.md`: `NARR-001` through `NARR-009`, `LLM-001` through `LLM-009`, `API-013`
* `doc/decisions.md`: `Start narration with deterministic perception rendering`; `Restrict LLM narration to typed style planning`; `Configure the local gateway only at runtime bootstrap`
* `doc/high_level_design.md`: `Presentation pipeline`; numbered flow steps 9 through 11; functional-LLM failure paragraph after the flow
* `src/llm_system/narration.py`
* `src/llm_system/functional_generation.py`
* `src/llm_system/application/model_gateway.py`
* `src/llm_system/api.py`: `_UnavailableFunctionalGateway`, `create_app`, `_player_turn_response`, `_narration_for`
* `tests/test_narration.py`
* `tests/test_api.py`: narration-related tests and existing fake functional gateway helpers
* `tests/test_courier_policy.py`: fake-gateway and bounded-context assertion pattern only

Do not read README, domain guide, roadmap, ideas, architect continuation state,
reviews, completed task briefs, or planning-chat history.

## Context budget

Use the soft 8,000-word pre-code documentation limit from
`doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 450 |
| Role guide | Implementation procedure | `implementer.md` | 1,350 |
| Task brief | Execution contract | This file | 1,050 |
| Glossary | Presentation and model vocabulary | named entries | 150 |
| Requirements | Observable boundaries | named IDs | 1,250 |
| Decisions | Accepted authority and gateway choices | named entries | 1,050 |
| Design | Presentation flow and failure boundary | named sections | 400 |
| **Total before source exploration** |  |  | **5,700** |

## Fixed assumptions

* `PlayerNarrationContext` is the sole enriched input to narrator styling; its
  builder remains the only package-aware enrichment boundary.
* The existing injected `FunctionalModelGateway` is reused. Its strict schema,
  disabled-thinking, and one-repair behavior remain unchanged.
* This task changes no player-turn response schema, Streamlit page behavior,
  persistence schema, canonical trace, or event schema.
* Style-plan generation happens only after `coordinate_player_turn` has
  returned a non-stale result; an unavailable gateway must still yield
  deterministic narration.

## In scope

* Add strict style-plan/output/result contracts and a pure application service
  which serializes only `PlayerNarrationContext` to the functional gateway.
* Permit exactly two fixed template families, `direct` and `observational`, and
  the four enum sections `location`, `characters`, `objects`, and `connections`.
* Validate that a selected plan uses each eligible section exactly once: location
  and connections are always eligible; characters and objects are eligible only
  when their context tuples are nonempty. Use a deterministic direct,
  location-characters-objects-connections default plan on any failed or
  semantically invalid selection.
* Extend deterministic rendering to accept a validated plan and render all text
  from fixed templates plus existing context values. Preserve the current
  direct/default narration text exactly.
* Wire style selection into `_narration_for` after context construction, using
  the gateway already configured by `create_app`. Keep the existing fixed safe
  narration for `NarrationContextError`.
* Bump `pyproject.toml` to the next semantic minor version.
* Add focused behavioral tests for restricted serialized model context, accepted
  style use, semantic invalid-plan fallback, failed-generation fallback, exact
  section rendering, default-text compatibility, and API post-commit safe
  fallback.

## Out of scope

* Generated prose, generated names/identifiers/claims, prompt-only factual
  controls, free-form prompt inputs, streaming, or System notifications.
* Durable narrator-generation or presentation evidence, SQLite migrations,
  trace changes, inspection UI, player-page changes, and gateway/runtime
  configuration changes.
* Changing interpretation, scheduler pending-progress behavior, action
  authority, or all unrelated LLM roles.

## Expected contracts and files

* Extend `src/llm_system/narration.py` with enum style-plan contracts,
  context-dependent validation, and fixed-template render variants.
* Create `src/llm_system/application/narration_style.py` and export its public
  contracts/service through `src/llm_system/application/__init__.py` following
  the existing NPC-policy pattern.
* Update `src/llm_system/api.py` only to route the configured gateway through
  post-commit narration.
* Update `tests/test_narration.py`, `tests/test_api.py`, and add a focused
  style-service test module if that is clearer than extending the narration
  test module.

## Acceptance criteria

1. The style service sends one deterministic system instruction and canonical
   JSON of only `PlayerNarrationContext` to `FunctionalModelGateway`, requesting
   a strict output model that contains only `voice` and `section_order` enums.
2. A syntactically accepted plan is effective only when it contains the exact
   eligible section set once each. Duplicate, omitted, extra-for-context, or
   otherwise semantically invalid plans use the direct default; gateway failure
   uses the same default without provider detail.
3. The renderer emits every eligible factual group exactly once from fixed
   templates and context values. The model has no string-valued factual output
   field, and the default direct rendering retains TASK-055's exact prose.
4. Player-turn response variants that already receive narration use style
   selection only after their committed result exists. No narration-related
   failure changes the response variant, committed action result, revision,
   perception, or fixed safe context-error fallback.
5. The task creates no persistence, trace, event, response-schema, Streamlit,
   model-gateway, or scheduler change.
6. Version, focused tests, full suite, formatting, lint, type check, lock check,
   and diff check all pass.

## Required verification

* Write failing behavioral tests before implementation logic.
* `uv run pytest tests/test_narration.py tests/test_api.py`
* any new focused style-service test module
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires free-text model output,
new factual context, a public response change, durable presentation evidence,
or a change to the existing functional gateway contract.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
