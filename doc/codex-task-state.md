# Codex task state

## Current objective

Complete the remaining M3 deterministic-kernel boundaries through small accepted contracts and delegated TDD tasks. TASK-028 now defines deterministic co-located Speak v0 resolution and is Ready for implementation after its planning artifacts are committed.

Repository baseline: commit `d239bc9 t27`, package version `0.26.0`.

## Completed work

* TASK-023, Observe v0, is Done and committed. `src/llm_system/simulation/resolvers/observe.py::resolve_observe` reuses `project_current_perception`, rejects all absent targets uniformly, and emits zero-time `ActorObservedEvent` evidence. `dispatch_actor_action` now routes Observe.
* TASK-024, self-action event feedback, is Done and committed. `src/llm_system/simulation/perception_engine.py::FutureEventFeedbackError` and `project_self_event_feedback` validate observer then whole-batch time, map all eight event owners exhaustively, and retain exact events.
* TASK-025, scheduled-activity contracts, is Done and committed. `src/llm_system/simulation/scheduling.py` defines `EnvironmentalScheduledActivity`, `NpcScheduledActivity`, `SystemDirectorScheduledActivity`, `ScheduledActivity`, and `ScheduledActivityQueue`.
* TASK-026, deterministic selection, is Done and committed. `src/llm_system/simulation/scheduling.py::ScheduledActivitySelection` and `select_eligible_activities` partition at canonical world time, order due work, preserve pending order, and retain exact activity objects. Review corrected validation precedence and added a regression test in `tests/test_scheduled_activity_selection.py`.
* TASK-027, recorded integer draws, is Done and committed. `src/llm_system/simulation/randomness.py` defines `IntegerDrawRequest`, `IntegerDrawRecord`, `IntegerRandomSource`, `RandomSourceContractError`, and `draw_recorded_integer`; public exports and focused behavioral tests are included.
* TASK-028 planning is complete and Ready but not implemented. Its accepted boundary is zero-time speech addressed to another co-located character, with uniform non-audible rejection and no recipient feedback or response behavior.
* Public exports are maintained in `src/llm_system/simulation/__init__.py`; accepted architecture and usage are reflected in `README.md`, `doc/high_level_design.md`, `doc/requirements.md`, `doc/decisions.md`, `doc/glossary.md`, and `doc/roadmap.md`.

## Decisions and rationale

* Observe v0 is deliberately thin and zero-time because richer perceptible facts, checks, and durations do not yet exist. Unknown and hidden targets share one rejection to prevent truth leakage.
* Event feedback begins with stateless self-action projection. Witness rules need unresolved pre/post-location, hearing, and event-specific semantics; the caller owns the candidate event window and delivery tracking.
* Scheduled activities are closed, one-shot eligibility records rather than executable generic payloads. Environmental, NPC, and System-director work have different downstream authorities.
* Phase priority is derived from the variant: environmental, NPC, then System director. Ordering uses `(eligible_at_seconds, phase_rank, insertion_sequence)`; UUID and storage order are not tie-breakers.
* Selection is a pure validated partition, not a claim or execution transaction. It includes overdue and exactly due work, preserves future storage order, and reuses the input queue when nothing is selected.
* A concrete seeded generator is deferred until the first accepted random-check consumer and persistence boundary exist. Scripted injected sources are sufficient for the current deterministic kernel.
* Speak v0 uses canonical co-location for audibility without treating visual perception as hearing. Successful delivery records an event but does not claim comprehension or recipient reaction.

## Commands and verified results

* TASK-026 focused and adjacent review: `uv run pytest tests/test_scheduled_activity_selection.py tests/test_scheduled_activity_contracts.py tests/test_world_state_validation.py tests/test_package.py -q` -> `41 passed`.
* `make format` -> 55 files unchanged.
* `make lint` -> passed.
* `make mypy` -> no issues in 55 source files.
* `make test` -> `235 passed`.
* `make check` -> format, lint, mypy, and `235 passed`.
* `uv sync --locked`, `uv lock --check`, and `git diff --check` -> passed.
* Lockfile review -> only root package version `0.24.0` to `0.25.0` for TASK-026.
* `git status --short` at commit `785d254` -> clean before this file was added.
* TASK-027 review -> focused `19 passed`; `make format`, `make lint`, `make mypy`, `uv sync --locked`, and `uv lock --check` passed; `make check` passed all gates with `247 passed`; `git diff --check` passed.
* TASK-028 planning review -> `git diff --check` passed; no production code or package metadata changed, so tests were not rerun.

## Tests

The last full-suite verification passed all `247` tests. No production code changed during TASK-028 planning, so the suite was not rerun. No known failing test, lint, formatting, typing, lock, or diff check exists.

## Blockers and unresolved questions

No current blocker.

Unresolved planned work includes TASK-028 implementation; addressed-speech recipient feedback; Take, Use, and Help mechanics; remaining witness event feedback; authored environmental schedules and System-director hooks; activity execution/claiming/persistence/cascading semantics; later draw history and simulation-step trace integration; a concrete seeded generator plus persisted state when the first random mechanic exists; and M3.5 architecture and test-value reviews. Scheduled-activity execution should not be invented before its environmental mechanics, NPC policies, and director-hook consumers are grounded.

## Exact next action

Review and commit the Ready TASK-028 planning artifacts. After that, delegate `doc/tasks/TASK-028-speak-resolver.md` only when explicitly requested; implementation and independent review remain separate workflow steps.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/codex-task-state.md`
3. `doc/roadmap.md` M3 and M3.5
4. `doc/tasks/TASK-028-speak-resolver.md`
5. The exact context manifest in TASK-028; do not load unrelated planning documents during delegated implementation
