# TASK-042: Add the local functional model gateway

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-001A evidence and Python/httpx2 foundation

## Objective

Provide one synchronous, fakeable application boundary for local OpenAI-compatible functional LLM calls. It must reproduce the measured Gemma request settings, strictly validate only `message.content` into a caller-supplied Pydantic model, make at most one schema-guided repair, and return inspectable typed evidence without taking role-specific or simulation-authoritative action.

This task implements shared functional structured-output transport only. Player interpretation, courier behavior, narrator prose, trace persistence, and safe-failure mapping remain later consumers.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: “Context envelope”, “Functional LLM role”, “Model gateway”, “Simulation arbiter”, “Simulation-step trace”, and “Structured output”
* `doc/requirements.md`: `LLM-001`, `LLM-003` through `LLM-017`
* `doc/decisions.md`: “Require structured functional LLM outputs with bounded repair”, “Disable Gemma thinking for functional LLM roles”, and “Build the first local gateway around functional structured output”
* `doc/high_level_design.md`: “Model gateway” and the functional-failure paragraph under “Simulation-step flow”
* `doc/experiments/structured_output_preflight.md`: “Thinking-disabled comparison (TASK-001A)” and “Recommendation for the later model gateway” only
* Initial source entrypoints: `src/llm_system/player_api.py`, `src/llm_system/application/__init__.py`, and `src/llm_system/simulation/_types.py`
* Initial test entrypoints: the HTTP client and ownership tests in `tests/test_player_page.py` and strict-output fixture shapes in the named experiment extracts

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, or planning-chat history. Do not contact a live model endpoint. Trace only task-local source and tests after reading the selections above.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 430 |
| Role guide | Implementation procedure | `doc/agent_roles/implementer.md` | 850 |
| Task brief | Execution contract | This file | 2,200 |
| Vocabulary | Stable provider and authority terms | Six named glossary entries | 330 |
| Requirements | Accepted request, validation, repair, and failure behavior | Named LLM requirements | 760 |
| Decisions and architecture | Fixed boundary and rationale | Three decisions plus named HLD extracts | 1,450 |
| Experiment evidence | Measured provider-specific behavior | Two bounded report sections | 1,100 |
| **Total before source exploration** |  |  | **7,120** |

## Fixed assumptions

* Use the existing synchronous `httpx2` dependency directly. Do not add the OpenAI SDK, an async layer, retry library, configuration library, or prompt framework.
* Add an application module, preferably `src/llm_system/application/model_gateway.py`, containing strict immutable contracts and `HttpLocalModelGateway`.
* `ModelMessage` contains exactly `role: Literal["system", "user", "assistant"]` and non-blank `content`.
* Public gateway construction accepts explicit `base_url`, non-blank `model`, positive `timeout_seconds`, positive integer `max_tokens`, and optionally one injected `httpx2.Client` or `httpx2.BaseTransport`. Supplying both client and transport is a caller error. No environment variables or machine paths are read here.
* Expose a structural `FunctionalModelGateway` protocol so later role services can use deterministic fakes without importing the HTTP implementation.
* `generate_functional` accepts a non-empty immutable tuple of `ModelMessage` plus `output_model: type[OutputT]`, where `OutputT` is a Pydantic `BaseModel`, and returns a typed `FunctionalGenerationResult[OutputT]`.
* The gateway prepends one deterministic system message containing the compact JSON Schema from `output_model.model_json_schema()`. Caller message order and objects remain unchanged.
* Every POST goes to `{base_url without trailing slash}/v1/chat/completions` with timeout and a JSON body containing exactly `model`, `temperature: 0`, `max_tokens`, `messages`, `response_format: {"type":"json_object"}`, and `chat_template_kwargs: {"enable_thinking":false}`.
* A provider success wrapper must contain exactly one choice with a string `finish_reason` and a message object. Extra provider wrapper/message fields may be ignored. Only `message.content` is a candidate; `reasoning_content` is never read or copied into candidate output.
* Acceptance requires HTTP 200, `finish_reason == "stop"`, non-blank string content, and `output_model.model_validate_json(content, strict=True)` success.
* Invalid functional output means blank/missing content, non-`stop` finish, invalid JSON, or strict Pydantic validation failure. It produces normalized non-blank validation errors and exactly one repair POST.
* The repair uses the identical schema instruction, original caller messages, model settings, and endpoint. It deterministically includes the failed content (including explicit absence) and normalized validation errors in an appended repair instruction. It does not mine or partially reuse invalid fields.
* Transport exceptions, non-200 statuses, and malformed provider wrappers return failure without repair. Provider body and exception text must not become content or validation evidence.
* `FunctionalGenerationAttempt` records exact candidate `content`, `finish_reason`, a typed failure kind or `None`, and immutable normalized validation errors. `FunctionalGenerationResult` records `accepted` or `failed`, a typed value only when accepted, the initial attempt, and at most one repair attempt; validate internal coherence.
* Use a small closed failure-kind vocabulary covering transport unavailable, service/HTTP error, malformed response, and invalid output. Exact member names are implementation-level but must be stable and tested.
* `close()` closes only an internally created client. An injected client remains usable after gateway close.
* Do not measure latency in this task: deterministic attempt ordering and evidence exist now, while a clock/latency contract belongs with later trace integration.

## In scope

* Add and publicly export the gateway protocol, HTTP implementation, messages, attempt evidence, result contract, disposition, and failure-kind types.
* Implement the exact functional request, strict content-only validation, bounded repair, and safe provider/transport failure behavior above.
* Add focused mock-transport tests proving exact request bodies and ordering, initial success, successful repair, failed repair, every non-repair failure category, strict non-coercion, reasoning-content rejection, evidence coherence, deterministic schema/repair prompts, repeatability, and client ownership.
* Bump the project minor version and update the installed-version assertion and lockfile project version.
* Update this task's status and handoff report only.

## Out of scope

* Live endpoint calls, model discovery/health checks, environment loading, credentials, authentication policy, streaming, embeddings, async/concurrent requests, automatic operational retries, circuit breakers, metrics, or latency recording.
* Player/courier/director output schemas, role prompts, role-specific safe results, narrator prose, actor runtime, action submissions, simulation execution, persistence, trace schema changes, API/UI integration, or package changes.
* Changes to requirements, decisions, glossary, high-level design, roadmap, continuation state, README, domain guide, ideas, reviews, experiments, or agent governance.

## Expected contracts and files

* `src/llm_system/application/model_gateway.py`: public contracts, protocol, and HTTP implementation.
* `src/llm_system/application/__init__.py`: public exports.
* `tests/test_model_gateway.py`: focused behavior tests using `httpx2.MockTransport`; no network.
* `tests/test_package.py`, `pyproject.toml`, and `uv.lock`: version only.

## Acceptance criteria

1. Explicit configuration and client injection satisfy LLM-010 and LLM-017 without new dependencies or implicit environment access.
2. Mock transport captures the exact LLM-011 payload, endpoint, timeout, deterministic compact schema instruction, and original caller-message order.
3. Only stopped, non-blank `message.content` that passes strict Pydantic JSON validation becomes an accepted typed value; coercible-but-wrong types fail, and `reasoning_content` is never substituted, satisfying LLM-001, LLM-009, and LLM-012.
4. Each eligible invalid-output case makes exactly one repair with unchanged context/settings plus failed content and normalized errors. A valid repair is accepted; an invalid repair returns failed with both attempts and no third call, satisfying LLM-003 and LLM-013.
5. Transport, status, and malformed-wrapper cases return typed safe failures after one call and do not expose provider/exception text as candidate content, satisfying LLM-014.
6. Result and attempt contracts reject incoherent accepted/failed combinations and preserve ordered evidence required by LLM-015.
7. The gateway never applies role fallback, builds simulation contracts, mutates/persists state, or writes traces, satisfying LLM-016.
8. Repeated calls with equal inputs and equal mock responses produce equal typed results and equal request bodies without mutating messages or output-model classes.
9. Existing application, HTTP client, package, typing, lint, and full-suite behavior remains green.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv run pytest tests/test_model_gateway.py`
* `uv run pytest tests/test_player_page.py tests/test_package.py`
* `make format`
* `make lint`
* `make mypy`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires a live service, new dependency, async/concurrency policy, credentials, provider-specific output outside `message.content`, more than one repair, role-specific fallback semantics, simulation/persistence/trace changes, public request fields beyond those fixed here, or governance changes outside this brief.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
