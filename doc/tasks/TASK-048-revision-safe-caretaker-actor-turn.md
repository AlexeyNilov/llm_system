# TASK-048: Run one revision-safe caretaker actor turn

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-041 and TASK-037

## Objective

An application caller can request one Greybridge caretaker decision and receive
either a durably completed NPC actor-action step or an honest stale-decision
result. The policy receives only its bounded context; the existing arbiter path
remains sole authority for canonical effects.

This is the first actor-runtime execution seam, not scheduled activity
execution. It gives the later scheduler one concrete, revision-safe NPC turn
operation without inventing activity claim, recurrence, or retry semantics.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: “Actor runtime”, “Action proposal”, “Action proposal submission”, “Decision context”, and “Decision policy”
* `doc/requirements.md`: `NPC-008` through `NPC-012`, `POLICY-007` through `POLICY-010`, and `STEP-001` through `STEP-010`
* `doc/decisions.md`: “Start actor policies with one pure caretaker decision” and “Start the actor runtime with one revision-safe caretaker turn”
* `doc/high_level_design.md`: “Actor runtime” and “Clock and scheduler”
* `src/llm_system/application/npc_decision.py`, `src/llm_system/application/actor_action_step.py`, and `src/llm_system/application/player_turn_coordinator.py`
* `tests/test_caretaker_policy.py`, `tests/test_actor_action_step.py`, and `tests/test_player_turn_coordinator.py`

Do not read README, the domain guide, roadmap, ideas, reviews, completed task
briefs, architect continuation state, or planning-chat history.

## Context budget

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | 430 |
| Role guide | Implementation procedure | `doc/agent_roles/implementer.md` | 620 |
| Task brief | Execution contract | This file | 1,090 |
| Vocabulary | Stable boundary names | Five named glossary entries | 180 |
| Requirements | Behavior and authority | Named `NPC`, `POLICY`, and `STEP` IDs | 660 |
| Decision and design | Accepted scope and component split | Two named decisions; two named sections | 720 |
| Initial source/tests | Existing policy and coordinator contracts | Six named files | Source exploration |
| **Total before source exploration** |  |  | **3,700** |

## Fixed assumptions

* The only supported actor is authored NPC `bridge-caretaker` with the matching
  `caretaker-rule-policy`; do not create a policy registry or execute the
  courier.
* Build `NpcDecisionContext` from the exact validated packages and the
  caretaker's current perception; do not add memories, beliefs, plans that
  mutate, or canonical-state fields.
* Run the pure policy outside a SQLite write unit of work. Recheck world ID and
  revision before creating proposal, step, outcome, or event identities.
* Reuse `execute_actor_action_step_in_unit` for authorization, dispatch,
  commitment, perception, trace append, and persistence. The new coordinator
  owns one commit around that existing helper.
* Preserve the scheduled queue exactly. Do not select, claim, consume, add,
  reschedule, or trace scheduled activities.

## In scope

* A strict typed completed-or-stale result and one application coordinator for
  the named caretaker.
* Bounded context assembly, policy invocation, revision recheck, trusted NPC
  provenance, deterministic injectable identity assignment, and atomic action
  completion.
* Focused behavioral tests, package export updates, and a project version bump
  to `0.46.0`.

## Out of scope

* Scheduled activity execution, environment mechanics, System director work,
  LLM courier policy, generic policy dispatch, memories, beliefs, narration,
  HTTP/UI, persistence schema changes, and package-content changes.
* New dependencies or environment configuration.
* Governance-document changes other than this task’s status and handoff report.

## Expected contracts and files

* New `src/llm_system/application/npc_turn_coordinator.py` (or a comparably
  narrow application module), exported through `llm_system.application`.
* Existing `NpcDecisionContext`, caretaker policy, actor-action in-unit helper,
  SQLite store/unit of work, package definitions, perception projection, and
  actor-action traces remain the authority boundaries.
* New focused `tests/test_npc_turn_coordinator.py`; update package exports and
  `pyproject.toml` version only as necessary.

## Acceptance criteria

1. A valid current caretaker turn builds an actor-matching bounded context,
   invokes the existing caretaker policy, constructs matching NPC provenance,
   and returns only after one durable action-step commit; its proposal and
   completion evidence match the existing action path (`NPC-008`, `NPC-011`).
2. An unsupported/missing/non-NPC/mismatched-policy request fails before policy
   invocation, trusted identity assignment, or persistence writes (`NPC-009`).
3. A revision change after context/policy evaluation returns a typed stale
   result with no new trusted identities or writes (`NPC-010`).
4. The operation leaves scheduled queue content unchanged and never invokes an
   LLM or scheduled selection (`NPC-012`).
5. Tests cover completion, invalid actor/policy, stale no-write behavior,
   bounded context, provenance, atomicity, and unchanged scheduled queue.

## Required verification

* Write failing behavioral tests before implementation logic.
* `uv run pytest tests/test_npc_turn_coordinator.py tests/test_caretaker_policy.py tests/test_actor_action_step.py`
* `make format && make lint && make mypy && make check`
* `uv lock --check && git diff --check`

## Stop conditions

Stop and report a design gap if the work needs scheduled-activity lifecycle
semantics, a generic policy registry, LLM behavior, new persistence data, or a
public HTTP/UI contract.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending; list the documentation extracts and initially named
source or test files actually consulted. Do not list every transitive
implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
