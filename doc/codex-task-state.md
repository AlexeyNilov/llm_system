# Codex task state

## Current objective

Commit and delegate Ready TASK-036: V1 SQLite bootstrap, an explicitly committed unit of work, a strict stored-world record containing package ownership, `WorldState`, and `ScheduledActivityQueue`, a singleton revision-checked world repository, and ordered revision-linked canonical-event persistence.

## Verified baseline

* TASK-035 and the complete M3.6 documentation/context restructuring are committed through `b8f1384 simplify rules`.
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
* Root agent instructions now contain only universal rules and route work to one architect, implementer, or reviewer guide.
* Ready task briefs explicitly name and budget one responsibility-specific role guide.

## Blockers and limitations

No current blocker to SQLite boundary design.

TASK-036 deliberately excludes simulation-step trace persistence because no stable trace contract exists yet. It also excludes package resolution, world initialization/reset orchestration, the turn coordinator, memories, beliefs, and API behavior.

Greybridge cannot yet execute its flood, NPC activities, System director hooks, Help, or progression. Persistence work must not describe the scenario as fully playable until those capabilities exist.

## Exact next action

Apply the automatic Ready-task handoff: commit any remaining task-owned planning artifact, delegate TASK-036 immediately to a fresh coding subagent, wait for its handoff, and independently review the result.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/agent_workflow.md`: task briefs, context routing, and context budget
4. `doc/tasks/TASK_TEMPLATE.md`
5. `doc/reviews/m3-5-kernel-review.md`: KRV-002 and recommended M4 gate
6. `doc/roadmap.md`: M4
7. Persistence sections and decisions selected by the future task's context manifest
