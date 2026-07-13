# Codex task state

## Current objective

Define the next M4 increment around the minimal simulation-step trace and atomic turn coordinator now that TASK-036 provides the SQLite unit of work and repositories.

## Verified baseline

* The automatic Ready-task handoff rule is committed through `10b5e25 automate ready task delegation`.
* TASK-036 is independently reviewed and accepted in the working tree but is not yet committed.
* Project and installed package version: `0.34.0`.
* `uv sync --locked`, focused persistence tests with `6` passing tests, `make check` with `329` passing tests, `uv lock --check`, and `git diff --check` pass.

## Available foundation

* Versioned rule and scenario packages load into strict definitions and pass semantic and world-readiness validation.
* Immutable canonical state, typed changes, outcomes, events, atomic in-memory commitment, authorization, and type-directed dispatch are implemented.
* Observe, Move, Speak, Take, Use, and Wait resolve deterministically; Help remains an explicit unavailable capability.
* Current-state and selected immediate event-feedback perception paths are implemented.
* Scheduled activities can be represented and deterministically partitioned; recorded integer draws have an injected boundary but no concrete generator.
* SQLite V1 strictly persists one revision-checked world snapshot, its scheduled queue, and ordered revision-linked canonical events through an explicitly committed unit of work.

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

No current blocker to the next M4 design increment.

No stable simulation-step trace contract exists yet. The next coordinator task must define only the trace evidence required by the first atomic application step rather than anticipating later LLM, memory, belief, director, or presentation fields.

Greybridge cannot yet execute its flood, NPC activities, System director hooks, Help, or progression. Persistence work must not describe the scenario as fully playable until those capabilities exist.

## Exact next action

Commit the accepted TASK-036 implementation and integration updates. Then settle the minimal trace and coordinator boundaries; once the next brief is Ready, commit and delegate it automatically.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/tasks/TASK-036-sqlite-world-and-event-persistence.md`: accepted persistence boundary
4. `src/llm_system/persistence/`: unit of work and repository APIs
5. `doc/reviews/m3-5-kernel-review.md`: KRV-001 and KRV-002
6. `doc/high_level_design.md`: turn coordinator, simulation-step sequence, and observability
7. Trace, scheduling, submission, outcome, and persistence requirements selected for the next decision
