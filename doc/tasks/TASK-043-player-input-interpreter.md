# TASK-043: Add the player input interpreter

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-042, current perception contracts, and actor-action proposal contracts

## Objective

Add one application service that interprets non-blank free-form player text against only the player's current perception. It returns either an explicit private thought with at most one supported existing action proposal, or a safe clarification, while preserving the model-generation evidence and creating no trusted authority or simulation effects.

This task proves the role-specific functional consumer behind the gateway. HTTP and Streamlit text integration, submission creation, action execution, and narration remain later tasks.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: “Action proposal”, “Context envelope”, “Functional LLM role”, “Model gateway”, “Perception snapshot”, “Player”, “Structured output”, and “Simulation arbiter”
* `doc/requirements.md`: `TIME-003`, `PLAY-001`, `PLAY-002`, `PLAY-005`, `PLAY-008` through `PLAY-012`, `ACTION-014` through `ACTION-022`, `PERCEPTION-006`, `PERCEPTION-007`, `LLM-001`, `LLM-003`, `LLM-004`, `LLM-007` through `LLM-009`, and `LLM-015` through `LLM-017`
* `doc/decisions.md`: “Build an open simulation with a lightweight game layer”, “Use an explicit cognition and action loop”, “Separate proposal payloads from trusted submission metadata”, and “Interpret one player input without creating authority”
* `doc/high_level_design.md`: “Player input interpreter”, “Context envelopes”, and steps 1 through 3 of “Simulation-step flow”
* Initial source entrypoints: `src/llm_system/application/model_gateway.py`, `src/llm_system/application/__init__.py`, `src/llm_system/simulation/actions.py`, and `src/llm_system/simulation/perception.py`
* Initial test entrypoints: `tests/test_model_gateway.py`, `tests/test_actions.py`, and `tests/test_perception_contracts.py`

Do not read README, the domain guide, roadmap, ideas, reviews, experiments, completed task briefs, architect continuation state, API/UI code, package content, or planning-chat history. Do not contact a live model endpoint. Trace only task-local source and tests after reading the selections above.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 430 |
| Role guide | Implementation procedure | `doc/agent_roles/implementer.md` | 850 |
| Task brief | Execution contract | This file | 2,050 |
| Vocabulary | Stable interpretation and authority terms | Eight named glossary entries | 390 |
| Requirements | Accepted input, output, proposal, perception, and failure behavior | Named requirements | 1,000 |
| Decisions and architecture | Fixed boundary and rationale | Four decisions plus named HLD extracts | 1,550 |
| **Total before source exploration** |  |  | **6,270** |

## Fixed assumptions

* Add an application module, preferably `src/llm_system/application/player_interpreter.py`, containing strict immutable output and result contracts plus one pure orchestration service over an injected `FunctionalModelGateway`.
* Define a public proposal subset containing exactly the existing `ObserveActionProposal`, `MoveActionProposal`, `SpeakActionProposal`, `TakeActionProposal`, `UseActionProposal`, and `WaitActionProposal`, discriminated by `operation`. Do not copy their fields. `HelpActionProposal` is excluded because its resolver is unavailable.
* `PlayerInterpreterOutput` contains exactly four required fields: `result_type: Literal["interpreted", "clarification"]`, `private_thought: NonBlankText | None`, `proposal: InterpretedPlayerProposal | None`, and `clarification: NonBlankText | None`.
* Output coherence is exact: `interpreted` requires at least `private_thought` or `proposal` and forbids `clarification`; `clarification` requires `clarification` and forbids thought and proposal. Missing nullable fields remain structurally invalid rather than receiving defaults.
* Speech is represented only by `SpeakActionProposal` in the one proposal slot. One input cannot produce separate speech and another action.
* `PlayerInterpretationResult` contains exactly the original non-blank `player_text`, exact `PerceptionSnapshot`, final `PlayerInterpreterOutput`, and `FunctionalGenerationResult[PlayerInterpreterOutput]` evidence.
* Result coherence is exact: an accepted generation must contain a value equal to the final output; a failed generation must contain no value and the final output must be the application-owned fallback clarification specified below.
* Expose `interpret_player_input(gateway, *, player_text, perception) -> PlayerInterpretationResult`. Reject blank player text before calling the gateway.
* The service sends exactly two caller messages to the gateway: one deterministic system instruction and one user message containing deterministic compact JSON with keys `player_input` and `current_perception`. Serialize the snapshot with `model_dump(mode="json")`, sorted keys, and compact separators. Pass `PlayerInterpreterOutput` as the output model.
* The system instruction must state that the model: extracts only explicitly expressed private thought and attempted action; may return at most one proposal; uses only IDs present in current perception; uses only the six schema-supported operations; represents speech through Speak; requests clarification for ambiguity, missing required arguments, or unsupported mechanics; does not invent motives, hidden facts, mechanics, identities, success, outcomes, or narration; and returns no trusted metadata.
* On accepted generation, preserve the model value exactly, including an accepted model-produced clarification.
* On any failed generation disposition, return exactly `PlayerInterpreterOutput(result_type="clarification", private_thought=None, proposal=None, clarification="I couldn't interpret that safely. Please clarify your intended thought or action.")`. Preserve the failed generation evidence unchanged and expose no provider detail through the clarification.
* The service receives no world, packages, prior messages, memory, identities, clocks, repositories, or API objects. It does not validate proposal actionability; the arbiter remains authoritative.

## In scope

* Add and publicly export the supported interpreter proposal subset, `PlayerInterpreterOutput`, `PlayerInterpretationResult`, and `interpret_player_input`.
* Add focused deterministic-fake tests for exact prompt/context routing, thought-only interpretation, each of the six proposal variants including speech, thought plus one proposal, accepted model clarification, gateway-failure fallback, strict output/result coherence, missing/extra fields, Help exclusion, blank input, input/perception preservation, repeatability, and absence of mutation.
* Bump the project minor version and update the installed-version assertion and lockfile project version.
* Update this task's status and handoff report only.

## Out of scope

* Live model calls, provider transport changes, prompt tuning from empirical trials, authored-name enrichment, unrestricted package data, world state, prior conversation, memory, beliefs, player motive inference, or multiple proposals.
* API endpoints, Streamlit changes, trusted UUID/source/submission construction, authorization, resolution, time advancement, scheduling, persistence, trace schema/storage, narration, or System notifications.
* Help interpretation until a concrete resolver exists.
* Changes to requirements, decisions, glossary, high-level design, roadmap, continuation state, README, domain guide, ideas, reviews, experiments, packages, or agent governance.

## Expected contracts and files

* `src/llm_system/application/player_interpreter.py`: proposal subset, strict contracts, prompt construction, and service.
* `src/llm_system/application/__init__.py`: public exports.
* `tests/test_player_interpreter.py`: focused behavior tests with a deterministic gateway fake.
* `tests/test_package.py`, `pyproject.toml`, and `uv.lock`: version only.

## Acceptance criteria

1. The output schema and validators enforce PLAY-009 and the exact interpreted-versus-clarification invariants without defaults, unknown fields, coercion, or Help.
2. The gateway receives only the exact deterministic system instruction, compact player-input/current-perception JSON, and output model; no world, packages, history, trusted identities, or other actor information crosses the boundary, satisfying PLAY-008.
3. Accepted thought-only, speech, and each other supported proposal fixture returns the exact typed model value and generation evidence without claiming action success, satisfying PLAY-001, PLAY-002, PLAY-010, and ACTION-014.
4. Ambiguous or unsupported model output may return a schema-valid clarification with no proposal. Any failed gateway result maps to the exact fixed safe clarification while preserving evidence, satisfying PLAY-011 and LLM-004.
5. The result preserves exact input and perception and creates no identities, submission, execution, time, mutation, persistence, trace write, or narration, satisfying PLAY-012.
6. Blank player text fails before gateway invocation. Equal inputs and equal fake results produce equal outputs and messages without mutating or replacing input contracts.
7. Existing model-gateway, action, perception, application, typing, lint, and full-suite behavior remains green.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv run pytest tests/test_player_interpreter.py`
* `uv run pytest tests/test_model_gateway.py tests/test_actions.py tests/test_perception_contracts.py`
* `make format`
* `make lint`
* `make mypy`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires canonical world or package access, prior conversation, target actionability decisions, Help support, multiple proposals, trusted identities, API/UI/persistence/trace changes, live model access, gateway changes, a new dependency, or governance changes outside this brief.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
