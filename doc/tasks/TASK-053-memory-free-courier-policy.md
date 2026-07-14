# TASK-053: Produce bounded LLM courier proposals

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-042 and TASK-048

## Objective

Implement the authored Greybridge courier's memory-free LLM policy as a pure, fakeable decision producer. It returns one supported structured action proposal with generation evidence, or its safe deterministic Wait fallback.

## Context manifest

Read only `AGENTS.md`; `doc/agent_roles/implementer.md`; glossary entries “Action proposal”, “Functional generation”, “NPC decision context”, and “Perception snapshot”; requirements `NPC-013`--`NPC-015` and `LLM-001`--`LLM-017`; decision “Make the initial courier policy memory-free and generation-evidenced”; `npc_decision.py`, `player_interpreter.py`, `functional_generation.py`, `simulation/actions.py`, and their policy/gateway tests. Exclude scheduler execution, player turn, API/UI, persistence, narrator, inspection, scenario editing, and completed task artifacts.

## Context budget

| Context | Why required | Approximate words |
| --- | --- | ---: |
| Repository and implementation rules | Execution boundary | 2,000 |
| NPC and functional-output contracts | Information and fallback boundary | 1,700 |
| Decision and glossary extracts | Vocabulary and accepted direction | 900 |
| **Total before source exploration** |  | **4,600** |

## Fixed assumptions

* Support only `injured-courier` with its authored `courier-llm-policy`.
* The policy receives only `NpcDecisionContext` plus an injected functional gateway. It uses the current context exactly once and retains returned functional-generation evidence.
* Model output supports exactly one of Observe, Move, Speak, Take, Use, or Wait; Help remains unavailable. Failed generation returns Wait for 60 seconds.
* This task is a pure policy only: it creates neither trusted metadata nor a scheduled occurrence, and executes nothing.

## In scope

* Strict courier output/result contracts, deterministic bounded prompt/context, gateway invocation, accepted-proposal path, and deterministic fallback.
* High-signal policy tests with a fake gateway, including context boundary, output strictness, failure fallback, and immutability/no-mutation behavior.
* Version bump to `0.51.0`.

## Out of scope

* Courier activity materialization or execution, generic policy registry, persistence or traces, memories, beliefs, prompt history, narration, API/UI, configuration changes, new dependencies, and scenario/package edits.

## Acceptance criteria

1. Matching courier context alone produces a deterministic gateway request limited to identity, goals, current plan, and exact perception.
2. A strict accepted output yields one supported proposal with exact ordered generation evidence. Failed generation yields Wait 60 with no provider detail or prose extraction.
3. Contracts reject Help, malformed/extra output, wrong courier identity, and another actor's perception. Equal calls do not mutate their context.
4. The policy performs no submission, execution, state/time/persistence, scheduling, or HTTP/UI action.

## Required verification

* Write failing behavioral tests before implementation logic.
* `uv run pytest tests/test_courier_policy.py tests/test_model_gateway.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Stop conditions

Stop and report a design gap if courier execution, scheduled activity mutation, persisted traces, memory/history, a generic policy registry, prompt access to canonical state, an API/UI route, or a new dependency is required.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
