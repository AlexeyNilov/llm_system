# Codex task state

## Current objective

Define the first M4 persistence task: a minimal SQLite boundary for one authoritative world, without moving simulation rules into storage.

## Verified baseline

* TASK-035 reviewed commit `bc35b67 plan`; its permitted report and handoff diff is independently accepted but not yet committed.
* Project and installed package version: `0.33.0`.
* `uv sync --locked`, collection of `323` tests, `make check` with `323` passing tests, `uv lock --check`, and `git diff --check` pass.

## Available foundation

* Versioned rule and scenario packages load into strict definitions and pass semantic and world-readiness validation.
* Immutable canonical state, typed changes, outcomes, events, atomic in-memory commitment, authorization, and type-directed dispatch are implemented.
* Observe, Move, Speak, Take, Use, and Wait resolve deterministically; Help remains an explicit unavailable capability.
* Current-state and selected immediate event-feedback perception paths are implemented.
* Scheduled activities can be represented and deterministically partitioned; recorded integer draws have an injected boundary but no concrete generator.

## Accepted M3.5 findings

* The deterministic kernel is ready for M4; SQLite must persist validated domain results and must not evaluate rules.
* One application transaction must own step completion across state, events, scheduled-queue effects, authoritative character data, and trace.
* The successful authorization-to-perception Use regression belongs to the real atomic coordinator acceptance suite, not a temporary pre-coordinator test.
* README restructuring and proposed low-value-test cleanup are useful but do not block persistence.
* The independent evidence is in `doc/reviews/m3-5-kernel-review.md`; its recommendations are not automatically accepted implementation scope.

## Blockers and limitations

No current blocker to SQLite boundary design.

Greybridge cannot yet execute its flood, NPC activities, System director hooks, Help, or progression. Persistence work must not describe the scenario as fully playable until those capabilities exist.

## Exact next action

Commit the accepted TASK-035 report and integration disposition. Then specify the bounded SQLite schema/repository choices needed for TASK-036.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/reviews/m3-5-kernel-review.md`: verdict, KRV-002, and recommended M4 gate
3. `doc/roadmap.md`: M4
4. `doc/high_level_design.md`: principal records, simulation-step flow, persistence and consistency, and observability
5. `doc/requirements.md`: `WORLD-001` through `WORLD-006`, `STATE-009`, and `STORE-001` through `STORE-005`
6. `doc/decisions.md`: “Begin with one persistent world”, “Use SQLite as the initial authoritative store”, “Replace immutable world-state snapshots atomically”, and “Separate arbiter commitment from operation resolution”
