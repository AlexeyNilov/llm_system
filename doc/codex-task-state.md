# Codex task state

## Current objective

Complete the remaining M3 deterministic-kernel operations through small accepted contracts and delegated TDD tasks. TASK-030 now defines the Ready Take v0 resolver boundary; implementation has not been delegated.

Verified repository baseline before TASK-030 planning: commit `0a3beb0 t29`, package version `0.28.0`, branch `main` ahead of `origin/main` by two commits, and a clean worktree.

## Completed work

* TASK-023, Observe v0, is Done and committed. `src/llm_system/simulation/resolvers/observe.py::resolve_observe` reuses current-state perception and emits zero-time observation evidence.
* TASK-024, self-action event feedback, is Done and committed. `src/llm_system/simulation/perception_engine.py::project_self_event_feedback` projects exact actor-owned events.
* TASK-025 and TASK-026, scheduled-activity contracts and deterministic eligibility selection, are Done and committed in `src/llm_system/simulation/scheduling.py`.
* TASK-027, recorded integer draws, is Done and committed in `src/llm_system/simulation/randomness.py`; a concrete generator remains deferred.
* TASK-028, Speak v0, is Done and committed. `src/llm_system/simulation/resolvers/speak.py::resolve_speak` records zero-time addressed co-located speech.
* TASK-029, addressed-speech recipient feedback, is Done and committed at `0a3beb0`. `src/llm_system/simulation/perception_engine.py::project_addressed_speech_feedback` preserves exact committed speech events for their recipients.
* TASK-030 planning adds accepted Take v0 requirements, decision, vocabulary, high-level design, a Ready roadmap entry, and `doc/tasks/TASK-030-take-resolver.md`. These planning changes are currently uncommitted and contain no production implementation.

## Decisions and rationale

* Take v0 accessibility is canonical-state actionability, not perception: the object must have an exact `ObjectAtLocation` placement matching the actor's current location.
* Unknown, remote, possessed, and wrong-namespace targets reject uniformly as `object-not-accessible` to avoid truth disclosure.
* Success is zero-time `object-taken`, with one exact `ObjectPlacementChanged` to actor possession and one exact `ObjectTakenEvent`; there is no failed branch.
* Transfer, theft, consent, carrying limits, object-specific rules, witness feedback, NPC reaction, and presentation remain outside TASK-030.
* TASK-030 should bump the public package version from `0.28.0` to `0.29.0`; planning alone does not change version metadata.

## Commands and verified results

* Baseline inspection: `git status --short --branch` -> clean `main`, ahead of `origin/main` by two; `git log -4 --oneline --decorate` -> HEAD `0a3beb0 t29`.
* TASK-029 implementation review previously passed its focused 18-test suite, `uv sync --locked`, `make format`, `make lint`, `make mypy`, `make check` with `260 passed`, `uv lock --check`, and `git diff --check`.
* TASK-030 planning inspected current resolver, dispatch, state, state-change, event, outcome, commitment, workflow, task-template, requirements, decisions, glossary, design, roadmap, README, and version contracts.
* TASK-030 planning verification: `make format` -> 60 files unchanged; `git diff --check` -> passed. Context-manifest decision titles were verified against the current decision headings.

## Tests

The last full verified implementation baseline has `260` passing tests and no known lint, formatting, typing, lock, or diff failure. Tests have not been rerun for the current documentation-only TASK-030 planning changes.

## Blockers and unresolved questions

No current blocker. TASK-030 has no material implementation choice left open.

Remaining planned work includes Use and Help mechanics; remaining witness event feedback; authored environmental schedules and System-director hooks; activity execution and persistence semantics; trace integration; the deferred concrete random generator; and M3.5 architecture and test-value reviews.

## Exact next action

After the user commits the accepted TASK-030 Ready brief, delegate it only on explicit request to a fresh Default implementer with no prior chat history, then independently review the result.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_workflow.md` delegation and review sections
3. `doc/tasks/TASK-030-take-resolver.md`
4. `doc/requirements.md` `TAKE-001` through `TAKE-012` and `DISPATCH-001` through `DISPATCH-010`
5. `doc/decisions.md` “Resolve Take v0 as direct co-located acquisition”
6. `doc/high_level_design.md` “Principal records” and `doc/roadmap.md` M3
