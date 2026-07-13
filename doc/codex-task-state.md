# Codex task state

## Current objective

Complete the remaining M3 deterministic-kernel boundaries through small accepted contracts and delegated TDD tasks. TASK-032 immediate third-party speech-overhearing feedback is specified and Ready for delegation.

Verified repository baseline before TASK-032 planning: commit `d5fe97a t31`, package version `0.30.0`, branch `main` ahead of `origin/main` by six commits, and a clean worktree.

## Completed work

* TASK-023, Observe v0, is Done and committed. `src/llm_system/simulation/resolvers/observe.py::resolve_observe` reuses current-state perception and emits zero-time observation evidence.
* TASK-024, self-action event feedback, is Done and committed. `src/llm_system/simulation/perception_engine.py::project_self_event_feedback` projects exact actor-owned events.
* TASK-025 and TASK-026, scheduled-activity contracts and deterministic eligibility selection, are Done and committed in `src/llm_system/simulation/scheduling.py`.
* TASK-027, recorded integer draws, is Done and committed in `src/llm_system/simulation/randomness.py`; a concrete generator remains deferred.
* TASK-028, Speak v0, and TASK-029, addressed-speech recipient feedback, are Done and committed. Speech records addressed co-located evidence and its exact committed recipient receives that event through perception.
* TASK-030, Take v0, is Done and committed at `f041275`. `src/llm_system/simulation/resolvers/take.py::resolve_take` performs zero-time canonical co-located acquisition, emits the exact placement change and object-taken event, and dispatch routes Take while Use and Help remain unavailable.
* TASK-031, immediate Take-witness feedback, is Done and committed at `d5fe97a`. `src/llm_system/simulation/perception_engine.py::project_take_witness_feedback` validates exact-current-time batches and projects exact object-taken events to eligible co-located non-actors. `WitnessEventTimeMismatchError` exposes stale or future candidate-window defects. The package version is `0.30.0`.

## Decisions and rationale

* Take-witness feedback is immediate only: every candidate event must occur at the supplied world's exact current simulation time. Applying current observer locations to historical events would rewrite history.
* Observer validation comes first; the first past or future candidate event then raises new `WitnessEventTimeMismatchError` before filtering.
* A witness must differ from the taking actor and have a current canonical location equal to the event's exact previous `ObjectAtLocation` placement.
* The committed previous placement establishes event location. Current object possession, authored initial placement, and current-state perception are not rechecked.
* Projection preserves exact events, order, and duplicates. Composition, delivery tracking, reactions, memory, narration, and richer visibility remain outside TASK-031.
* TASK-031 bumps the public package version from `0.29.0` to `0.30.0`; `uv.lock` changes only the editable root version.
* TASK-032 uses a separate speech-overhearing projection rather than a generic witness engine so speech audibility semantics remain explicit.
* It validates observer, exact-current-time batch, and every speech-event speaker in that order before observer-specific filtering. Missing speakers are malformed canonical evidence, not inaudibility.
* Only a third party at the resolved speaker's exact current location matches. Speaker and addressed recipient retain their existing distinct feedback paths.

## Commands and verified results

* Baseline inspection: `git status --short --branch` -> clean `main`, ahead of `origin/main` by four; `git log -4 --oneline --decorate` -> HEAD `f041275 t30`.
* TASK-030 independent review previously passed the focused 31-test suite, `uv sync --locked`, `make format`, `make lint`, `make mypy`, `make test` and `make check` with `271 passed`, `uv lock --check`, installed-version check, and `git diff --check`.
* TASK-031 planning inspected current event, state, perception-engine, existing feedback, Take resolver, requirements, decisions, glossary, design, roadmap, task-template, README, and version contracts.
* TASK-031 planning verification: `make format` -> 62 files unchanged; `git diff --check` -> passed. Context-manifest decision titles and TASK-031 roadmap linkage were verified.
* TASK-031 independent implementation review: focused required suite -> `26 passed`; `uv sync --locked`, `make format`, `make lint`, `make mypy`, `make test` -> `277 passed`; `make check` -> all gates and `277 passed`; `uv lock --check`, installed version `0.30.0`, and `git diff --check` -> passed.
* TASK-031 commit verification: `git status --short --branch` -> clean `main`, ahead of `origin/main` by six; `git log -3 --oneline` -> HEAD `d5fe97a t31`.

## Tests

All `277` tests pass. No known lint, formatting, typing, lock, or diff failure exists.

## Blockers and unresolved questions

No current blocker.

Remaining planned work includes Use and Help mechanics; other event-specific witness feedback; authored environmental schedules and System-director hooks; activity execution and persistence semantics; trace integration; the deferred concrete random generator; and M3.5 architecture and test-value reviews.

## Exact next action

Commit the TASK-032 planning artifacts, then delegate `doc/tasks/TASK-032-speech-overhearing-feedback.md` only after explicit user authorization.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_workflow.md` delegation and review sections
3. `doc/roadmap.md` M3 and M3.5
4. `doc/tasks/TASK-032-speech-overhearing-feedback.md`
5. The exact context manifest in that task brief
