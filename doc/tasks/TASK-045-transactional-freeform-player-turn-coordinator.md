# TASK-045: Coordinate a transactional free-form player turn

**Status:** Ready

**Owner:** Unassigned

**Role:** Implementer

**Role guide:** `doc/agent_roles/implementer.md`

**Agent:** `implementer`

**Depends on:** TASK-037, TASK-043, and TASK-044

## Objective

Add one application service that turns free-form player input into one durable, revision-correct completion: thought-only, clarification, or a resolved actor action linked atomically to its interpretation trace.

It is the authority-safe seam between interpretation and a later HTTP endpoint. It must not add HTTP, Streamlit, provider runtime configuration, narration, or actor scheduling.

## Context manifest

Read only:

* `AGENTS.md`
* `doc/agent_roles/implementer.md`
* `doc/glossary.md`: “Action proposal submission”, “Functional LLM role”, “Perception snapshot”, “Player-input trace”, “Simulation arbiter”, “Simulation step”, and “Simulation-step trace”
* `doc/requirements.md`: `PLAY-008` through `PLAY-013`, `LLM-001` through `LLM-008`, `STORE-006` through `STORE-016`, and `STEP-001` through `STEP-015`
* `doc/decisions.md`: “Compose the first coordinator before scheduled execution”, “Persist the minimal completed actor-action trace”, “Interpret one player input without creating authority”, “Persist player interpretation in a linked input trace”, and “Coordinate a player turn around model latency and one commit”
* Initial source: `application/actor_action_step.py`, `application/player_interpreter.py`, `persistence/sqlite.py`, `persistence/records.py`, `player_input_traces.py`, and `application/__init__.py`
* Initial tests: `test_actor_action_step.py`, `test_player_interpreter.py`, and `test_player_input_traces.py`

Do not read planning history, API/UI code, README, package content, or completed task briefs. Do not contact a live model.

## Context budget

| Context | Approximate words |
| --- | ---: |
| Repository rules and implementer guide | 1,300 |
| This brief | 1,600 |
| Named glossary, requirements, and decisions | 2,500 |
| **Total before source exploration** | **5,400** |

## Fixed assumptions

* Add `coordinate_player_turn(store, packages, gateway, *, player_text, player_id, identity_factory)` and strict immutable public result variants for `thought_only`, `clarification`, `action_completed`, and `stale`. Exact module naming may follow existing application conventions.
* The coordinator must load/validate the stored singleton and derive `project_current_perception` for `player_id` before invoking `interpret_player_input`. It records that stored world identity and revision as the observed version, then closes the unit of work before the gateway call.
* Reopen one unit after interpretation. It must require the same world identity and revision before any write. A mismatch returns the typed `stale` result, assigns no identity, and writes nothing.
* For no-action output, assign exactly one player-input UUID, construct the matching `PlayerInputStepTrace`, append it at equal observed/resulting revision, commit, and return only after durable success.
* For proposal output, assign IDs in this exact order: player-input, proposal, simulation-step, decision-context, outcome, event. Construct a `PlayerInterpreterActionSource` with fixed trusted interpreter ID `freeform-player-turn`, then one `ActorActionSubmission` for `player_id`.
* Extract a narrow helper from `execute_actor_action_step` that accepts an already-active `SQLiteUnitOfWork` and performs the same compatibility, validation, authorization, dispatch, commitment, world replacement, event append, and completed actor-action trace append without committing. Preserve `execute_actor_action_step` as its public self-committing wrapper.
* The proposal path calls that helper and appends the action-linked player-input trace in the same unit before one commit. It returns only player-safe committed fields already present in `CompletedActorActionStep` plus the exact private thought when supplied; raw generation evidence remains trace-only.
* Clarification includes both an accepted model clarification and the interpreter's fixed gateway-failure clarification. It is durable at the unchanged revision and must not expose provider failure details.
* On package, validation, authorization, dispatch, persistence, or trace failure, return no completed result and rely on unit-of-work rollback. Do not transform these operational failures into a clarification.
* Bump version `0.43.0` to `0.44.0`, update the installed-version test and lockfile; no new dependency.

## In scope

* The coordinator/result contracts, narrow actor-action no-commit composition helper, exports, and deterministic-fake tests.
* Tests for exact bounded perception/gateway routing, thought and clarification durable completion, gateway fallback durability, action atomicity/linkage, rejected action, stale revision without writes or identities, rollback, and preservation of existing self-committing coordinator behavior.
* Version files and this brief's status/handoff only.

## Out of scope

* API routes/models, Streamlit chat, server/local model environment configuration, live model calls, narration, scheduler/NPC/System execution, retrying stale input, conversation history, memory, beliefs, inspection UI, or changing existing trace schemas.
* Governance changes other than this task brief.

## Acceptance criteria

1. No SQLite write transaction remains open during gateway invocation; the interpreter receives only one current player perception and exact player text.
2. Thought-only, accepted clarification, and gateway-fallback clarification each append exactly one no-action input trace at the same revision and return only after commit.
3. An action appends its actor trace, canonical events, world replacement, and action-linked input trace in one unit of work. Rejected outcomes remain durable completed action results.
4. A changed world identity or revision after interpretation yields typed stale completion with no generated IDs and no durable writes.
5. Existing `execute_actor_action_step` behavior stays compatible; no generated output or caller supplies trusted metadata.
6. Raw prompt/generation/provider information stays out of public coordinator results while exact evidence is retained in the input trace.
7. Version is `0.44.0`; focused and full checks pass without a live model.

## Required verification

* Write failing behavioral tests before implementation logic.
* `uv run pytest tests/test_player_turn_coordinator.py`
* `uv run pytest tests/test_actor_action_step.py tests/test_player_input_traces.py tests/test_player_interpreter.py tests/test_model_gateway.py`
* `make format`
* `make lint`
* `make mypy`
* `make check`
* `uv lock --check`
* `git diff --check`

## Stop conditions

Stop for an unaccepted API/UI contract, runtime provider configuration, stale retry rule, package/state leak, extra player action, schema migration, new dependency, or general transaction framework.

## Handoff report

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Context used:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
