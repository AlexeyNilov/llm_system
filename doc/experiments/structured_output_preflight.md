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

## Recommendation for the later model gateway

Use `/v1/chat/completions` with the discovered model identifier and request
`response_format: {"type":"json_object"}` as a syntactic assist only. Keep strict
Pydantic validation as the authority boundary and retain the accepted single
schema-guided repair attempt and role-specific safe disposition. Treat an empty
`content`, `finish_reason: "length"`, JSON parse failure, or schema failure as one
failed functional output; do not parse `reasoning_content` or generated prose.

Do not depend on the tested `json_schema` request forms for schema enforcement: this
server accepted them but did not yield usable proof of enforcement. The gateway
should record request settings, response content, finish reason, validation errors,
repair output, final disposition, and latency in the step trace as required by
LLM-008. Set a gateway timeout and a response-token budget that accounts for this
model's hidden reasoning; the player failure mode here consumed all 600 completion
tokens before emitting `content`.
