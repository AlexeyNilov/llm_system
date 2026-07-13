# Codex task state

## Current objective

Complete the remaining M3 deterministic-kernel boundaries through small accepted contracts and delegated TDD tasks. TASK-031 now defines the Ready immediate Take-witness feedback boundary; implementation has not been delegated.

Verified repository baseline before TASK-031 planning: commit `f041275 t30`, package version `0.29.0`, branch `main` ahead of `origin/main` by four commits, and a clean worktree.

## Completed work

* TASK-023, Observe v0, is Done and committed. `src/llm_system/simulation/resolvers/observe.py::resolve_observe` reuses current-state perception and emits zero-time observation evidence.
* TASK-024, self-action event feedback, is Done and committed. `src/llm_system/simulation/perception_engine.py::project_self_event_feedback` projects exact actor-owned events.
* TASK-025 and TASK-026, scheduled-activity contracts and deterministic eligibility selection, are Done and committed in `src/llm_system/simulation/scheduling.py`.
* TASK-027, recorded integer draws, is Done and committed in `src/llm_system/simulation/randomness.py`; a concrete generator remains deferred.
* TASK-028, Speak v0, and TASK-029, addressed-speech recipient feedback, are Done and committed. Speech records addressed co-located evidence and its exact committed recipient receives that event through perception.
* TASK-030, Take v0, is Done and committed at `f041275`. `src/llm_system/simulation/resolvers/take.py::resolve_take` performs zero-time canonical co-located acquisition, emits the exact placement change and object-taken event, and dispatch routes Take while Use and Help remain unavailable.
* TASK-031 planning adds accepted immediate Take-witness requirements, decision, vocabulary, high-level design, a Ready roadmap entry, and `doc/tasks/TASK-031-take-witness-feedback.md`. These planning changes are currently uncommitted and contain no production implementation.

## Decisions and rationale

* Take-witness feedback is immediate only: every candidate event must occur at the supplied world's exact current simulation time. Applying current observer locations to historical events would rewrite history.
* Observer validation comes first; the first past or future candidate event then raises new `WitnessEventTimeMismatchError` before filtering.
* A witness must differ from the taking actor and have a current canonical location equal to the event's exact previous `ObjectAtLocation` placement.
* The committed previous placement establishes event location. Current object possession, authored initial placement, and current-state perception are not rechecked.
* Projection preserves exact events, order, and duplicates. Composition, delivery tracking, reactions, memory, narration, and richer visibility remain outside TASK-031.
* TASK-031 should bump the public package version from `0.29.0` to `0.30.0`; planning alone does not change version metadata.

## Commands and verified results

* Baseline inspection: `git status --short --branch` -> clean `main`, ahead of `origin/main` by four; `git log -4 --oneline --decorate` -> HEAD `f041275 t30`.
* TASK-030 independent review previously passed the focused 31-test suite, `uv sync --locked`, `make format`, `make lint`, `make mypy`, `make test` and `make check` with `271 passed`, `uv lock --check`, installed-version check, and `git diff --check`.
* TASK-031 planning inspected current event, state, perception-engine, existing feedback, Take resolver, requirements, decisions, glossary, design, roadmap, task-template, README, and version contracts.
* TASK-031 planning verification: `make format` -> 62 files unchanged; `git diff --check` -> passed. Context-manifest decision titles and TASK-031 roadmap linkage were verified.

## Tests

The last full verified implementation baseline has `271` passing tests and no known lint, formatting, typing, lock, or diff failure. Tests have not been rerun for the current documentation-only TASK-031 planning changes.

## Blockers and unresolved questions

No current blocker. TASK-031 has no material implementation choice left open.

Remaining planned work includes Use and Help mechanics; other event-specific witness feedback; authored environmental schedules and System-director hooks; activity execution and persistence semantics; trace integration; the deferred concrete random generator; and M3.5 architecture and test-value reviews.

## Exact next action

After the user commits the accepted TASK-031 Ready brief, delegate it only on explicit request to a fresh Default implementer with no prior chat history, then independently review the result.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_workflow.md` delegation and review sections
3. `doc/tasks/TASK-031-take-witness-feedback.md`
4. `doc/requirements.md` `PERCEPTION-045` through `PERCEPTION-054`
5. `doc/decisions.md` “Project immediate co-located Take witnesses”
6. `doc/high_level_design.md` “Perception engine” and “Principal records” plus `doc/roadmap.md` M3
