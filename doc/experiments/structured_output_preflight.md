# Structured-output preflight

**Date:** 2026-07-11
**Task:** TASK-001  
**Service:** local `llama-server` at `http://127.0.0.1:12345`  
**Model:** `gemma-4-12b`

## Scope and method

This is an empirical preflight, not an application contract. The two schemas below
are deliberately provisional. They were validated by the temporary standard-library
script `/tmp/structured_output_preflight.py`; its validator rejects missing required
keys, additional object keys, wrong primitive types, and disallowed `operation`
values. Raw captures are in `/tmp/structured_output_preflight/*.json` for this local
session; the exact request template, model-visible content, finish reason, latency,
and validation result are recorded below. No credentials were sent.

All trial requests used `temperature: 0`, `seed: 17`, and `max_tokens: 600`. The
same request was repeated five times per shape. `seed` was accepted by the service,
but these results demonstrate that it did **not** make the player trial repeatable.

### Provisional schemas

Player interpretation:

```json
{"type":"object","additionalProperties":false,"required":["thought","speech","action_proposal"],"properties":{"thought":{"type":"string"},"speech":{"type":"string"},"action_proposal":{"anyOf":[{"type":"null"},{"type":"object","additionalProperties":false,"required":["intent","operation","arguments"],"properties":{"intent":{"type":"string"},"operation":{"type":"string","enum":["move","inspect","speak"]},"arguments":{"type":"object","additionalProperties":false,"required":["target"],"properties":{"target":{"type":"string"}}}}}]}}}
```

NPC proposal:

```json
{"type":"object","additionalProperties":false,"required":["intent","operation","arguments"],"properties":{"intent":{"type":"string"},"operation":{"type":"string","enum":["move","inspect","speak","wait"]},"arguments":{"type":"object","additionalProperties":false,"required":["target"],"properties":{"target":{"type":"string"}}}}}
```

### Reached routes and model discovery

```text
$ curl -sS --connect-timeout 3 -w '\nHTTP_STATUS:%{http_code} TOTAL_SECONDS:%{time_total}\n' http://127.0.0.1:12345/v1/models
{"models":[{"name":"gemma-4-12b",...,"capabilities":["completion"]}],"object":"list","data":[{"id":"gemma-4-12b",...,"owned_by":"llamacpp",...}]}
HTTP_STATUS:200 TOTAL_SECONDS:0.000230

$ curl -sS --connect-timeout 3 -w '\nHTTP_STATUS:%{http_code} TOTAL_SECONDS:%{time_total}\n' http://127.0.0.1:12345/health
{"status":"ok"}
HTTP_STATUS:200 TOTAL_SECONDS:0.000122
```

`POST /v1/chat/completions` also returned HTTP 200 for every capture below. The
service returned 404 for `/v1/openapi.json`, `/openapi.json`, and `/docs`; it did
not expose a discoverable OpenAPI description.

## Exact request forms

The trial payload was exactly this shape, with the appropriate compact schema above
substituted for `<SCHEMA>` and the noted user text. No headers other than
`Content-Type: application/json` were sent.

```json
{"model":"gemma-4-12b","temperature":0,"seed":17,"max_tokens":600,"messages":[{"role":"system","content":"Return ONLY a JSON object that conforms exactly to this schema: <SCHEMA>"},{"role":"user","content":"<USER_TEXT>"}],"response_format":{"type":"json_object"}}
```

Player `USER_TEXT`: `Interpret: I quietly say hello, then move to the bridge.`  
NPC `USER_TEXT`: `NPC decision: inspect the unstable bridge before moving.`

For prompt-only controls, the payload was identical except that `response_format`
was omitted. A separate request used `response_format` with
`{"type":"json_schema","json_schema":{"name":"player_interpretation","strict":true,"schema":<PLAYER_SCHEMA>}}`;
it returned HTTP 200 but `finish_reason: "length"` and empty `content` after 160
tokens of reasoning. The alternative documented-looking form
`{"type":"json_object","schema":<PLAYER_SCHEMA>}` behaved identically. Neither
test demonstrates server-side JSON Schema enforcement.

## Trial evidence

The `raw content` cells are the captured unmodified
`choices[0].message.content` strings. An empty string is shown as `""`. The server
wrapper for all rows was `{"choices":[{"finish_reason":...,"message":{"content":...}}],"model":"gemma-4-12b",...,"timings":...}`; full wrapper captures remain in the
temporary paths named above.

| Capture | Mode | Finish | Latency | Raw content | Strict validation |
| --- | --- | --- | ---: | --- | --- |
| 01 | player + `json_object` | stop | 7.335 s | `{"thought":"The user wants to perform two actions: speaking 'hello' and moving to the bridge. I will start by performing the first action, which is speaking 'hello'.","speech":"Hello.","action_proposal":{"intent":"greet","operation":"speak","arguments":{"target":"hello"}}}` | valid |
| 02 | player + `json_object` | length | 9.054 s | `""` | invalid: content is not JSON |
| 03 | player + `json_object` | length | 9.047 s | `""` | invalid: content is not JSON |
| 04 | player + `json_object` | length | 8.897 s | `""` | invalid: content is not JSON |
| 05 | player + `json_object` | length | 8.906 s | `""` | invalid: content is not JSON |
| 06 | NPC + `json_object` | stop | 5.003 s | `{"intent":"inspect_bridge","operation":"inspect","arguments":{"target":"unstable bridge"}}` | valid |
| 07 | NPC + `json_object` | stop | 4.976 s | same as 06 | valid |
| 08 | NPC + `json_object` | stop | 4.859 s | same as 06 | valid |
| 09 | NPC + `json_object` | stop | 4.874 s | same as 06 | valid |
| 10 | NPC + `json_object` | stop | 4.865 s | same as 06 | valid |
| 11 | player, prompt only | stop | 7.391 s | ````json\n{...valid player object...}\n```` | invalid: code fence prevents JSON decoding |
| 12 | NPC, prompt only | stop | 4.983 s | ````json\n{"intent":"inspect_bridge","operation":"inspect","arguments":{"target":"unstable bridge"}}\n```` | invalid: code fence prevents JSON decoding |

Counts: player with `json_object` **1/5** valid; NPC with `json_object` **5/5**
valid; prompt-only controls **0/1** valid for each shape.

`json_object` therefore appears to constrain the top-level response to a JSON
object when a final answer is produced (it removed the prompt-only Markdown fences),
but it does not guarantee an answer exists or validate the object against the
provisional schema. The deliberately invalid JSON-object request below confirms the
latter point.

```text
request user text: Return exactly this invalid object: {"intent": 7, "operation": "fly", "arguments": {}}
raw content: {"intent": 7, "operation": "fly", "arguments": {}}
finish_reason: stop; latency: 2.416 s
validator errors:
- $.intent: expected string
- $.operation: expected one of ['move', 'inspect', 'speak', 'wait']
- $.arguments: missing required key target
```

## One schema-guided repair

Using the invalid output and all three exact validation errors above, the repair
system message appended:

```text
Your previous output failed validation with these exact errors: ["$.intent: expected string", "$.operation: expected one of ['move', 'inspect', 'speak', 'wait']", "$.arguments: missing required key target"]. Return a replacement only; preserve the same intended task.
```

It retained the NPC schema and `response_format: {"type":"json_object"}`. The
request user text was again `NPC decision: inspect the unstable bridge before
moving.` The raw response content was:

```json
{"intent":"inspect_bridge","operation":"inspect","arguments":{"target":"unstable bridge"}}
```

It finished with `stop` in **5.354 s** and passed all strict checks (**1/1**).
This is evidence that one repair can work for this simple case, not evidence that it
is reliable enough to remove the one-attempt bound or role-specific safe failure.

## Thinking-disabled comparison (TASK-001A)

**Date:** 2026-07-11
**Comparison condition:** identical model, schemas, prompts, `temperature: 0`,
`seed: 17`, `max_tokens: 600`, and `response_format: {"type":"json_object"}` as
the TASK-001 rows above, with this one top-level request addition:

```json
{"chat_template_kwargs":{"enable_thinking":false}}
```

The exact sanitized payload for a normal trial was therefore:

```json
{"model":"gemma-4-12b","temperature":0,"seed":17,"max_tokens":600,"messages":[{"role":"system","content":"Return ONLY a JSON object that conforms exactly to this schema: <PLAYER_OR_NPC_SCHEMA>"},{"role":"user","content":"<SAME_TASK-001_USER_TEXT>"}],"response_format":{"type":"json_object"},"chat_template_kwargs":{"enable_thinking":false}}
```

Captures and a standard-library strict validator are in
`/tmp/structured_output_thinking_disabled/` for this local session. Each capture
contains the sanitized payload, complete server wrapper, extracted `content` and
`reasoning_content`, usage, latency, and validator errors. The validator used the
same fixture rules as TASK-001: it rejects invalid JSON, missing required keys,
additional object keys, wrong primitive types, and operations outside the schema
enum.

### Trial results

| Fixture and condition | Strict valid | Content length (characters) | Reasoning-content length (characters) | Completion tokens | Finish reasons | Latency |
| --- | --- | --- | --- | --- | --- | --- |
| Player, TASK-001 thinking enabled (5) | 1/5 | 320, 0, 0, 0, 0 | 1,647, 2,374, 2,374, 2,374, 2,374 | 524, 600, 600, 600, 600 | 1 `stop`, 4 `length` | 7.335, 9.054, 9.047, 8.897, 8.906 s |
| Player, thinking disabled (5) | **5/5** | 299 each | 0 each (field absent) | 97 each | 5 `stop` | 1.508, 1.161, 1.156, 1.156, 1.155 s |
| NPC, TASK-001 thinking enabled (5) | 5/5 | 112 each | 1,435 each | 453 each | 5 `stop` | 5.003, 4.976, 4.859, 4.874, 4.865 s |
| NPC, thinking disabled (5) | **5/5** | 112 each | 0 each (field absent) | 46 each | 5 `stop` | 0.722, 0.510, 0.515, 0.512, 0.516 s |

With thinking disabled, usable strict-valid output appeared in `message.content`
in **5/5 player** and **5/5 NPC** trials. In these controlled samples the flag
reliably moved the usable output into `content`; it also removed the response
field `reasoning_content`. It is evidence for this server/model/fixture combination,
not a general guarantee for future prompts or models.

Representative raw response wrapper (disabled player trial 01, omitted only
server-generated IDs/timings for readability; the complete wrapper is
`/tmp/structured_output_thinking_disabled/player_01.json`):

```json
{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"{\n  \"thought\": \"The user wants me to perform two actions: speak a greeting quietly and then move to the bridge. I will start by speaking.\",\n  \"speech\": \"Hello.\",\n  \"action_proposal\": {\n    \"intent\": \"move_to_location\",\n    \"operation\": \"move\",\n    \"arguments\": {\n      \"target\": \"bridge\"\n    }\n  }\n}"}}],"model":"gemma-4-12b","usage":{"completion_tokens":97,"prompt_tokens":157,"total_tokens":254}}
```

The corresponding full wrapper has no `message.reasoning_content`. By contrast,
the TASK-001 player capture 02 had `finish_reason: "length"`, empty `content`,
2,374 reasoning-content characters, and 600 completion tokens.

### Thinking-disabled repair

The TASK-001 NPC repair prompt was repeated once with the same explicit validation
errors and the same disabled-thinking payload. It returned:

```json
{"intent":"examine_environment","operation":"inspect","arguments":{"target":"unstable bridge"}}
```

It finished `stop` in 0.746 s, used 46 completion tokens, had no
`reasoning_content`, and passed strict validation (**1/1**). Full request and raw
wrapper: `/tmp/structured_output_thinking_disabled/npc_repair.json`. This remains
evidence that one repair can succeed for the fixture, not evidence to relax the
one-attempt bound.

### Thinking-disabled `json_schema` probe

The previously accepted TASK-001 player `json_schema` form was repeated with
thinking disabled:

```json
{"response_format":{"type":"json_schema","json_schema":{"name":"player_interpretation","strict":true,"schema":<PLAYER_SCHEMA>}},"chat_template_kwargs":{"enable_thinking":false}}
```

It returned HTTP 200 with `finish_reason: "stop"`, the same 299-character
strict-valid player object, no reasoning content, 97 completion tokens, and
1.236 s latency. Full request and wrapper:
`/tmp/structured_output_thinking_disabled/player_json_schema.json`. This single
conforming response shows that the request form remains usable when thinking is
disabled; it does **not** demonstrate server-enforced JSON Schema validation. The
prompt itself supplied the schema and no deliberately invalid schema-enforcement
case was repeated under this condition.

## Recommendation for the later model gateway

For this local Gemma service, make request-time thinking control
`chat_template_kwargs: {"enable_thinking": false}` part of functional-role calls:
it prevented the observed hidden-reasoning token exhaustion and produced usable
`content` for both fixtures. Continue to request
`response_format: {"type":"json_object"}` only as syntactic JSON assistance; do
not depend on either tested `json_schema` form for enforcement. Strict Pydantic
validation remains the authority boundary. On any empty content, non-`stop`
finish, JSON parse failure, or schema failure, perform the accepted one
schema-guided repair with the same context envelope and validation errors, then use
the role-specific safe failure on a second invalid result. Never treat
`reasoning_content` as functional output.

The gateway should retain request settings, response content, finish reason,
validation errors, repair output, final disposition, and latency in the step trace
as required by LLM-008. Its timeout and response-token policy should be based on
the disabled-thinking condition for functional calls while preserving safe failure
when the model or server does not honor that request extension.
