# TASK-041: Add the rule-driven Greybridge caretaker policy

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-040 and accepted Greybridge package version `0.2.0`

## Objective

Expose a strict bounded NPC decision context and a pure deterministic rule policy that lets the Greybridge bridge caretaker propose its initial reinforcement-materials sequence through the existing actor-action proposal boundary without an LLM or canonical-state access.

This task establishes the policy contract and concrete first policy only. A later actor runtime will assemble contexts, select implementations, create trusted submission provenance, and schedule execution.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: “Action proposal”, “Actor runtime”, “Character decision context”, “Decision policy”, “Perception snapshot”, and “Simulation arbiter”
* `doc/requirements.md`: `NPC-002` through `NPC-005`, `LOOP-003` through `LOOP-006`, `POLICY-001` through `POLICY-010`, and `SCENARIO-003`
* `doc/decisions.md`: “Make NPC decision policies interchangeable”, “Use Storm at Greybridge as the initial scenario”, and “Start actor policies with one pure caretaker decision”
* `doc/high_level_design.md`: “Actor runtime” and “Context envelopes”
* `doc/initial_scenario.md`: “Bridge caretaker” and “Initial information boundaries”
* `game_packages/scenarios/storm-at-greybridge/0.2.0/scenario.yaml`: bridge-caretaker definition and reinforcement-materials placement
* `game_packages/rules/greybridge-rules/0.2.0/rules.yaml`: policy declaration and reinforcement mechanic
* Initial source entrypoints: `src/llm_system/game_packages/entities.py`, `src/llm_system/simulation/actions.py`, and `src/llm_system/simulation/perception.py`
* Initial test entrypoints: `tests/test_current_state_perception.py` and `tests/test_greybridge_packages.py`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, or planning-chat history. Trace only task-local source and tests after reading the selections above.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 430 |
| Role guide | Implementation procedure | `doc/agent_roles/implementer.md` | 850 |
| Task brief | Execution contract | This file | 1,650 |
| Vocabulary | Stable boundary terms | Six named glossary entries | 220 |
| Requirements | Accepted policy and authority behavior | Named requirement ranges | 430 |
| Decisions | Contract rationale and fixed choice | Three named decisions | 900 |
| Architecture and scenario | Boundary and concrete actor content | Named HLD/scenario sections | 650 |
| Package extracts | Concrete identifiers and mechanic | Two bounded YAML extracts | 300 |
| **Total before source exploration** |  |  | **5,430** |

## Fixed assumptions

* `NpcDecisionContext` is an application-side strict immutable contract with exactly: `decision_context_id: UUID`, `npc_id: AuthoredId`, `identity_summary: NonBlankText`, non-empty immutable `goals: tuple[GoalDefinition, ...]`, `current_plan: NonBlankText | None`, and `perception: PerceptionSnapshot`.
* The context rejects a perception observer different from `npc_id`. It does not validate that the supplied authored prose or goals came from a package; later context assembly owns that provenance.
* The policy accepts only `npc_id="bridge-caretaker"`; another NPC identity raises `ValueError` with a stable non-blank message because policy misrouting is an application defect, not an in-world fallback.
* The policy returns only an existing `ActorActionProposal` variant. It does not create an `ActorActionSubmission`, IDs, provenance, outcomes, events, state changes, or traces.
* Exact Greybridge IDs in this scenario-specific implementation are intentional. Do not introduce a generic rule language, registry, dependency, or YAML schema change.
* Recognized conditions use only observations in the supplied snapshot. A Move rule additionally requires its exact connection to be observed with `is_available=True`.
* The deterministic priority is:
  1. if reinforcement materials are observed as possessed by the caretaker at `greybridge-span`, propose Use on that location;
  2. if they are possessed at `greybridge-waystation` and `waystation-to-span` is observed available, propose that Move;
  3. if they are observed directly at the caretaker's current location, propose Take;
  4. if the caretaker is at `greybridge-span` without possessing them and `span-to-waystation` is observed available, propose that Move;
  5. otherwise propose Wait for exactly 60 seconds.
* Structurally valid sparse, extra, duplicated, or unexpectedly ordered observations must not crash the policy. Conditions are established by typed matching, not tuple position. If contradictory observations would make more than one rule applicable, the priority above decides.

## In scope

* Add and publicly export `NpcDecisionContext` from the application boundary.
* Add and publicly export one pure caretaker decision function with the exact behavior above.
* Add focused behavioral and validation tests, including the four active proposals, unavailable/missing-data fallback, wrong-NPC failure, context observer mismatch, immutability, no input mutation, and independence from observation order.
* Bump the project minor version for the new public application capability and update the lockfile's project version if required by the existing toolchain.
* Update this task's status and handoff report only.

## Out of scope

* Actor-runtime context assembly, policy registry or lookup, package compatibility enforcement at execution time, trusted submission creation, authorization, resolution, persistence, scheduling, chained NPC turns, or API/UI changes.
* LLM gateway, courier policy, prompts, repair, narration, memory, beliefs, mutable plan state, fact perception, or changes to game-package schemas/content.
* Changes to requirements, decisions, high-level design, roadmap, continuation state, README, domain guide, ideas, reviews, or agent governance.

## Expected contracts and files

* New application module, preferably `src/llm_system/application/npc_decision.py`:
  * `NpcDecisionContext`
  * `decide_greybridge_caretaker(context: NpcDecisionContext) -> ActorActionProposal`
* `src/llm_system/application/__init__.py`: public exports.
* `tests/test_caretaker_policy.py`: focused contract and behavior tests.
* `pyproject.toml` and `uv.lock`: version only.

## Acceptance criteria

1. `NpcDecisionContext` enforces the exact strict immutable fields, non-empty goals, and actor-matching perception required by POLICY-007 and POLICY-008.
2. The caretaker decision is pure, deterministic, makes no LLM call, accepts no world state, and returns only a proposal payload as required by POLICY-001, POLICY-002, POLICY-005, and POLICY-009.
3. Focused tests prove the ordered Use, return Move, Take, and seek Move rules using only typed observations and the exact Greybridge identifiers.
4. Missing or unavailable action evidence and unrecognized safe states produce exactly `WaitActionProposal(operation="wait", duration_seconds=60)` as required by POLICY-010.
5. The implementation rejects a non-caretaker context as a caller error and safely handles sparse, duplicated, extra, and reordered structurally valid observations.
6. Repeated calls with equal context return equal proposals without mutating or replacing the context, its goals, or its perception.
7. Existing package, perception, action, application, typing, lint, and full-suite behavior remains green.

## Required verification

* Write a failing behavioral test before implementation logic.
* `uv run pytest tests/test_caretaker_policy.py`
* `uv run pytest tests/test_current_state_perception.py tests/test_greybridge_packages.py`
* `make format`
* `make lint`
* `make mypy`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop and report a design gap if implementation requires canonical world access, a new observation or proposal variant, a package schema/content change, registry or scheduling semantics, trusted provenance construction, mutable actor state, a new dependency, or governance changes beyond this task brief.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
