# TASK-001: Measure local structured-output behavior

**Status:** Ready

**Owner:** Unassigned

**Role:** Experimenter

**Agent:** `terra_experimenter`

**Depends on:** None

## Objective

Produce reproducible evidence about the local Gemma service's ability to return strict functional LLM outputs and respond to one schema-guided repair attempt. The result will constrain the later model-gateway implementation; it must not implement that gateway.

## Context manifest

Read only the following project context before inspecting the live local endpoint:

* `AGENTS.md`
* `README.md`: **Local LLM setup**
* `doc/glossary.md`: **Action proposal**, **Context envelope**, **Functional LLM role**, **Structured output**
* `doc/requirements.md`: `LLM-001` through `LLM-008`
* `doc/decisions.md`: **Require structured functional LLM outputs with bounded repair**
* `doc/high_level_design.md`: **Model gateway**, **Simulation-step flow**

Do not read `doc/ideas.md`, scenario content, memory design, or unrelated decisions.

## Fixed assumptions

* The LLM service is expected at `http://127.0.0.1:12345` and uses an OpenAI-compatible llama-server interface.
* Functional outputs will ultimately be validated by strict Pydantic models.
* Functional roles receive one repair attempt, then fail safely.
* This experiment may use provisional small JSON schemas; it does not define final application models.
* No model output is canonical world state.

## In scope

* Discover the live model identifier and supported OpenAI-compatible request routes.
* Test whether the server natively enforces JSON object or JSON-schema output, and distinguish that from prompt-only compliance.
* Exercise two provisional output shapes:
  * a player interpretation separating thought, speech, and one optional action proposal;
  * an NPC action proposal containing intent, supported operation, and arguments.
* Run at least five trials per shape with deterministic request settings where supported.
* Exercise one repair prompt using explicit validation errors and the same schema.
* Record exact sanitized requests, raw responses, latency observations, validation outcomes, and failure modes.
* Produce `doc/experiments/structured_output_preflight.md` with an evidence-backed recommendation for the later model gateway.

## Out of scope

* Application code, Pydantic domain models, or model-gateway implementation.
* Prompt optimization beyond what is required to measure basic compliance and repair.
* Narration quality, NPC personality, memory, beliefs, Qdrant, or scenario content.
* Changes to `AGENTS.md`, requirements, decisions, glossary, high-level design, or roadmap.
* Changes to this task brief outside its Status, Owner, and Handoff report fields.
* New dependencies.

## Expected contracts and files

Expected new file:

* `doc/experiments/structured_output_preflight.md`

Expected update:

* this task brief's Status, Owner, and Handoff report fields only.

Do not modify other repository files. Temporary request and response artifacts may be written under `/tmp` and must not contain credentials.

## Acceptance criteria

1. The report identifies the exact reachable route and model identifier, or records precise evidence that the service is unavailable.
2. The report distinguishes server-enforced structured output from prompt-only JSON behavior.
3. Trial results show valid-output counts for both provisional schemas.
4. The report shows whether one validation-error repair prompt returns a conforming output.
5. Every conclusion cites a captured request and response or an exact command result.
6. The report recommends a model-gateway strategy without changing accepted architecture.
7. No secrets, unrelated files, or application code are added.

If the service is unavailable, satisfy the task by recording the checks performed, exact failure evidence, and the minimal condition needed to resume. Do not invent results.

## Required verification

* Validate captured JSON with a temporary standard-library or existing-environment script; do not add a dependency.
* Confirm only the evidence report and permitted task-brief fields changed using `git status --short` and targeted inspection.
* Run `git diff --check`.

The project quality Make targets do not yet exist and are not required for this evidence-only task.

## Stop conditions

Stop and report a design gap if meaningful measurement requires changing server configuration, installing software, selecting final application schemas, or changing an accepted LLM-output requirement.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
