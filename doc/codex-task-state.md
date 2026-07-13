# Codex task state

## Current objective

Define the first M4 persistence task using the new bounded-context template: a minimal SQLite boundary for one authoritative world, without moving simulation rules into storage.

## Verified baseline

* TASK-035 reviewed commit `bc35b67 plan`; its permitted report and handoff diff plus the direct M3.6 documentation changes are not yet committed.
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

## Completed M3.6 changes

* README is a concise human landing page rather than a duplicate M3 contract reference.
* `doc/domain_guide.md` explains stable conceptual relationships without owning normative behavior.
* Canonical responsibilities remain with glossary, requirements, decisions, high-level design, and executable evidence.
* Future Ready briefs use an 8,000-word soft pre-code documentation budget, exact extracts, default context exclusions, and a context-used handoff record.
* Completed tasks and reviews remain inspectable history but are not default implementation context.

## Blockers and limitations

No current blocker to SQLite boundary design.

Greybridge cannot yet execute its flood, NPC activities, System director hooks, Help, or progression. Persistence work must not describe the scenario as fully playable until those capabilities exist.

## Exact next action

Commit the accepted TASK-035 and M3.6 documentation changes. Then specify the bounded SQLite schema and repository choices for the first M4 task using the revised template.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_workflow.md`: task briefs, context routing, and context budget
3. `doc/tasks/TASK_TEMPLATE.md`
4. `doc/reviews/m3-5-kernel-review.md`: KRV-002 and recommended M4 gate
5. `doc/roadmap.md`: M4
6. Persistence sections and decisions selected by the future task's context manifest
