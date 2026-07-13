# Codex task state

## Current objective

Complete the remaining M3 deterministic-kernel boundaries through small accepted contracts and delegated TDD tasks. TASK-027 is implemented and accepted; the next randomness boundary is a concrete seeded integer source with restorable generator state.

Repository baseline before TASK-027 implementation: commit `0702967 t27`. The accepted uncommitted implementation advances the package to `0.26.0`.

## Completed work

* TASK-023, Observe v0, is Done and committed. `src/llm_system/simulation/resolvers/observe.py::resolve_observe` reuses `project_current_perception`, rejects all absent targets uniformly, and emits zero-time `ActorObservedEvent` evidence. `dispatch_actor_action` now routes Observe.
* TASK-024, self-action event feedback, is Done and committed. `src/llm_system/simulation/perception_engine.py::FutureEventFeedbackError` and `project_self_event_feedback` validate observer then whole-batch time, map all eight event owners exhaustively, and retain exact events.
* TASK-025, scheduled-activity contracts, is Done and committed. `src/llm_system/simulation/scheduling.py` defines `EnvironmentalScheduledActivity`, `NpcScheduledActivity`, `SystemDirectorScheduledActivity`, `ScheduledActivity`, and `ScheduledActivityQueue`.
* TASK-026, deterministic selection, is Done and committed. `src/llm_system/simulation/scheduling.py::ScheduledActivitySelection` and `select_eligible_activities` partition at canonical world time, order due work, preserve pending order, and retain exact activity objects. Review corrected validation precedence and added a regression test in `tests/test_scheduled_activity_selection.py`.
* TASK-027, recorded integer draws, is Done and awaiting commit. `src/llm_system/simulation/randomness.py` defines `IntegerDrawRequest`, `IntegerDrawRecord`, `IntegerRandomSource`, `RandomSourceContractError`, and `draw_recorded_integer`; public exports and focused behavioral tests are included.
* Public exports are maintained in `src/llm_system/simulation/__init__.py`; accepted architecture and usage are reflected in `README.md`, `doc/high_level_design.md`, `doc/requirements.md`, `doc/decisions.md`, `doc/glossary.md`, and `doc/roadmap.md`.

## Decisions and rationale

* Observe v0 is deliberately thin and zero-time because richer perceptible facts, checks, and durations do not yet exist. Unknown and hidden targets share one rejection to prevent truth leakage.
* Event feedback begins with stateless self-action projection. Witness rules need unresolved pre/post-location, hearing, and event-specific semantics; the caller owns the candidate event window and delivery tracking.
* Scheduled activities are closed, one-shot eligibility records rather than executable generic payloads. Environmental, NPC, and System-director work have different downstream authorities.
* Phase priority is derived from the variant: environmental, NPC, then System director. Ordering uses `(eligible_at_seconds, phase_rank, insertion_sequence)`; UUID and storage order are not tie-breakers.
* Selection is a pure validated partition, not a claim or execution transaction. It includes overdue and exactly due work, preserves future storage order, and reuses the input queue when nothing is selected.

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

## Tests

All `247` tests pass. No known failing test, lint, formatting, typing, lock, or diff check exists.

## Blockers and unresolved questions

No current blocker.

Unresolved planned work includes a concrete seeded generator and restorable generator-state contracts; later persistence of seed and generator state; draw history and simulation-step trace integration; Speak, Take, Use, and Help mechanics; witness event feedback; authored environmental schedules and System-director hooks; activity execution/claiming/persistence/cascading semantics; and later M3.5 architecture and test-value reviews. Scheduled-activity execution should not be invented before its environmental mechanics, NPC policies, and director-hook consumers are grounded.

## Exact next action

Commit the accepted TASK-027 implementation. Then begin strategic design of the seeded integer source and restorable generator-state contracts one consequential question at a time; do not delegate until a new Ready brief is accepted and committed.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/codex-task-state.md`
3. `doc/roadmap.md` M3, M3.5, and M4 randomness follow-ups
4. `doc/requirements.md` `RANDOM-001` through `RANDOM-014`
5. `doc/decisions.md` entries “Use recorded seeded randomness only for explicit checks” and “Begin recorded randomness with one validated integer primitive”
6. `doc/high_level_design.md` sections “Simulation arbiter”, “Principal records”, and “Testing strategy”
7. `doc/glossary.md` entries “Integer draw record”, “Integer draw request”, “Integer random source”, and “Simulation arbiter”
8. `src/llm_system/simulation/randomness.py`
9. `tests/test_recorded_random_draws.py`
