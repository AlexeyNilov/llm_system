# TASK-001A: Compare structured output with thinking disabled

**Status:** Ready

**Owner:** Unassigned

**Role:** Experimenter

**Agent:** `terra_experimenter`

**Depends on:** TASK-001

## Objective

Measure whether disabling Gemma thinking at request time prevents structured-output token exhaustion and improves strict output validity for the same provisional player and NPC schemas used by TASK-001.

Update the existing preflight report with a controlled thinking-enabled versus thinking-disabled comparison and an evidence-backed gateway recommendation.

## Context manifest

Read only the following project context before inspecting the live endpoint:

* `AGENTS.md`
* `doc/tasks/TASK-001-structured-output-preflight.md`: scope, first-pass handoff, and integrator review
* `doc/experiments/structured_output_preflight.md`: complete baseline report
* `doc/glossary.md`: **Context envelope**, **Functional LLM role**, **Structured output**
* `doc/requirements.md`: `LLM-001` through `LLM-008`
* `doc/decisions.md`: **Require structured functional LLM outputs with bounded repair**
* `/home/lexa/an/git/llmops/src/llmops/use_cases/cognitive_map.py`: `LMStudioLLM.complete`, `_thinking_extra_body`, and `_get_graph_llm`

Do not read unrelated scenario, memory, belief, or idea documents.

## Fixed assumptions

* TASK-001 is the thinking-enabled baseline and its raw captures remain evidence.
* llama.cpp accepts the request extension `chat_template_kwargs: {enable_thinking: false}`; OpenAI SDK `extra_body` places it at the request top level.
* Strict validation, one repair attempt, and role-specific safe failure remain accepted architecture.
* The provisional schemas are measurement fixtures, not final application contracts.
* `reasoning_content` is diagnostic evidence, not a canonical functional output.

## In scope

* Reuse the TASK-001 player and NPC schemas, prompts, deterministic settings, and `response_format: {"type":"json_object"}`.
* Add top-level `chat_template_kwargs: {"enable_thinking": false}` to each comparison request.
* Run at least five thinking-disabled trials for each provisional schema.
* Capture `finish_reason`, `message.content`, `message.reasoning_content`, completion-token usage, latency, and strict validation results.
* Repeat the schema-guided repair case once with thinking disabled.
* Probe one previously accepted `json_schema` request form with thinking disabled to determine whether thinking was masking any usable server-enforced behavior; do not broaden into prompt optimization.
* Preserve TASK-001 results and add a clearly labeled comparison section to `doc/experiments/structured_output_preflight.md`.
* Revise only the report's final gateway recommendation as required by the combined evidence.

## Out of scope

* Application code, final Pydantic models, model-gateway implementation, or server configuration changes.
* Larger token budgets as a substitute for controlling thinking.
* Parsing `reasoning_content` as the functional output.
* Narration, memory, beliefs, Qdrant, scenario behavior, or prompt optimization.
* Changes to governance documents, roadmap, agent configuration, TASK-001 contract text, or unrelated files.

## Expected contracts and files

Expected update:

* `doc/experiments/structured_output_preflight.md`
* this task brief's Status, Owner, and Handoff report fields only

Temporary captures may be written under `/tmp` and must not contain credentials. Do not modify other repository files.

## Acceptance criteria

1. Five thinking-disabled player trials and five thinking-disabled NPC trials report strict-valid counts.
2. The report compares content length, reasoning-content length, completion tokens, finish reasons, and latency with the TASK-001 baseline.
3. The report states whether the thinking-disable flag reliably moves usable output into `message.content` for both fixtures.
4. One thinking-disabled repair trial is captured and validated.
5. One thinking-disabled `json_schema` request is captured without claiming enforcement beyond its evidence.
6. Exact sanitized request forms and representative raw response wrappers are included or referenced.
7. The final recommendation distinguishes request-time thinking control, syntactic JSON assistance, strict Pydantic validation, repair, and safe failure.
8. No application, server, governance, or custom-agent configuration changes are made.

If the endpoint is unavailable, record exact checks and the minimal condition needed to resume. Do not invent comparison results.

## Required verification

* Validate all new captures with a temporary standard-library or existing-environment script.
* Confirm only the report and permitted task-brief fields changed using baseline-aware `git status --short` and targeted diff inspection.
* Run `git diff --check`.

Project quality Make targets do not yet exist and are not required for this evidence-only follow-up.

## Stop conditions

Stop and report a design gap if the request-time flag is rejected, meaningful comparison requires changing server configuration, or the endpoint behavior cannot be distinguished from a task-runner sandbox restriction after a scoped retry.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
