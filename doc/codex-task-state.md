# Codex task state

## Current objective

Prepare one integrated, read-only M3.5 review of the deterministic kernel before designing SQLite persistence. The review will cover architecture boundaries, a representative player-action flow, documentation information architecture, and test-suite value.

## Verified baseline

* HEAD is `758bbdc t34` on clean `main`, ahead of `origin/main` by two commits.
* Project and installed package version: `0.33.0`.
* TASK-034 is committed and Done.
* At the accepted TASK-034 review baseline, focused tests passed `36`, the full suite and `make check` passed `323`, and formatting, Ruff, mypy, lock, metadata, Greybridge-content, and diff checks passed.

## Available foundation

* Versioned rule and scenario packages load into strict definitions and pass semantic and world-readiness validation.
* Immutable canonical state, typed changes, outcomes, events, atomic in-memory commitment, authorization, and type-directed dispatch are implemented.
* Observe, Move, Speak, Take, Use, and Wait resolve deterministically; Help remains an explicit unavailable capability.
* Current-state and selected immediate event-feedback perception paths are implemented.
* Scheduled activities can be represented and deterministically partitioned; recorded integer draws have an injected boundary but no concrete generator.

## Accepted transition

* M3 is complete for the purpose of reviewing and designing persistence; it is not the complete Greybridge vertical slice.
* Help and additional witness filtering are deferred.
* Concrete randomness remains deferred until a real check and persistence consumer exist.
* Scheduled-activity execution and simulation-step trace coordination move into the M4 atomic-step boundary; they must not be implied by the current selection-only scheduler.
* M3.5 combines architecture, documentation-IA, and test-value review into one evidence artifact to reduce ceremony and context duplication.

## Blockers and limitations

No current blocker.

Greybridge cannot yet execute its flood, NPC activities, System director hooks, Help, or progression. Persistence work must not describe the scenario as fully playable until those capabilities exist.

## Exact next action

Specify the single M3.5 read-only review task and its evidence artifact. Do not delegate until its Ready brief is accepted and committed.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_workflow.md` review and task-brief sections
3. `doc/roadmap.md` M3.5 and M4
4. `doc/ideas.md` IDEA-010 and IDEA-011
5. `doc/high_level_design.md` simulation-step flow, persistence, observability, and testing strategy
6. Relevant persistence, scheduling, trace, and inspection requirements and decisions named by the future brief
