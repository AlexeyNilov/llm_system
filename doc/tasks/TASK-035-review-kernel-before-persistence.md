# TASK-035: Review the kernel before persistence

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Reviewer

**Agent:** Default

**Depends on:** TASK-034 and the completed M3 kernel

## Objective

Produce one independent, evidence-backed review that determines whether the current deterministic kernel is safe to place behind the planned M4 SQLite and atomic simulation-step boundaries. Trace one representative Use action through the implemented contracts, identify material architecture risks and intentional missing seams, and give a clear persistence-readiness verdict.

Use the same artifact to assess whether the documentation routes a new developer to authoritative information and whether the current tests provide useful behavioral evidence. The review diagnoses and prioritizes work; it does not implement recommendations.

## Context manifest

Read only the following project context before tracing the actual source and tests:

* `AGENTS.md`
* `doc/glossary.md`: “Action proposal”, “Actor runtime”, “Canonical world state”, “Event”, “Observation”, “Outcome”, “Perception engine”, “Primary persistence”, “Scheduled activity”, “Scheduled activity selection”, “Simulation arbiter”, “Simulation kernel”, “Simulation step”, “Simulation-step trace”, “Turn coordinator”, and “Validated world state”
* `doc/requirements.md`: `WORLD-001` through `WORLD-006`, `TIME-001` through `TIME-006`, `AUTH-001` through `AUTH-006`, `STATE-009`, `STATE-019` through `STATE-024`, `STATE-038` through `STATE-045`, `ARBITER-001` through `ARBITER-021`, `AUTHZ-001` through `AUTHZ-015`, `USE-001` through `USE-012`, `DISPATCH-001` through `DISPATCH-010`, `EVENT-001` through `EVENT-013`, `PERCEPTION-001` through `PERCEPTION-035`, `SCHEDULE-001` through `SCHEDULE-023`, `RANDOM-001` through `RANDOM-014`, `STORE-001` through `STORE-005`, `INSPECT-001` through `INSPECT-006`, and `DEV-005` through `DEV-006`
* `doc/decisions.md`: “The simulation owns truth”, “Begin with one persistent world”, “Use discrete, action-driven simulation time”, “Separate creative direction from simulation authority”, “Separate the simulation kernel from game packages”, “Use SQLite as the initial authoritative store”, “Use recorded seeded randomness only for explicit checks”, “Serialize eligible activities deterministically”, “Model runtime state as an ID-linked mutable-facts overlay”, “Replace immutable world-state snapshots atomically”, “Separate arbiter commitment from operation resolution”, “Commit outcomes into one validated-world result”, “Authorize actor submissions before operation dispatch”, “Introduce partial type-based actor-action dispatch”, “Project current state before filtering event feedback”, “Represent scheduled work as one-shot typed eligibility records”, “Partition due scheduled activities without executing them”, “Begin recorded randomness with one validated integer primitive”, “Defer a concrete random generator until its first consumer”, “Begin Use mechanics with bound boolean-world-fact effects”, and “Resolve bound Use as a deterministic authored effect”
* `doc/high_level_design.md`: “Core constraints”, “Logical architecture”, “Component responsibilities”, “Information architecture”, “Actor loop”, “Simulation-step flow”, “Persistence and consistency”, “Randomness and replay”, “Observability and evaluation”, and “Testing strategy”
* `doc/initial_scenario.md`: “Package implementation stages”, “Supported interactions”, “Architecture coverage”, and “Explicit exclusions”
* `doc/roadmap.md`: “Deferred from M3”, “M3.5: Integrated architecture and test-value review”, and “M4: Persistence and application boundary”
* `doc/ideas.md`: `IDEA-010` and `IDEA-011` only
* `README.md`, `pyproject.toml`, `Makefile`, the complete `src/llm_system/` tree, and the complete `tests/` tree

Do not read completed task briefs, planning-chat history, postponed ideas other than `IDEA-010` and `IDEA-011`, or implementation handoff justifications. Reconstruct the architecture from accepted specifications, executable code, and behavioral tests.

## Fixed assumptions

* This is an independent, read-only review. Do not modify application code, tests, packages, README, requirements, decisions, design, glossary, ideas, or roadmap.
* The only permitted content artifact is `doc/reviews/m3-5-kernel-review.md`. The task brief may change only in its Status, Owner, and Handoff report fields.
* M3 is complete for persistence review, not for full Greybridge playability. Flood behavior, NPC and System director activity execution, Help, progression, some event-witness filtering, and presentation paths remain incomplete.
* Scheduled-activity execution, the turn coordinator, atomic persistence, and simulation-step traces are planned M4 responsibilities. Their absence is not by itself a defect; review whether the existing boundaries allow them to be added without moving canonical authority or duplicating domain rules.
* Help resolution, additional witness filtering, and a concrete random generator are explicitly deferred. Do not recommend them merely to make the feature inventory look complete.
* Use is the representative action because it crosses package-defined mechanics, canonical runtime overlays, authorization, dispatch, deterministic resolution, state changes, an event, and in-memory commitment. Trace the real implemented path; do not invent a coordinator around it.
* Accepted requirements and decisions define intended behavior. Source and tests provide evidence of implemented behavior. Report contradictions rather than silently choosing one as authoritative.
* Architecture findings must concern correctness, authority, ownership, coupling, persistence safety, replay, observability, or testability. Do not present naming or stylistic preferences as persistence blockers.
* Test value is not coverage percentage. Judge whether a test would detect meaningful behavioral regressions, and identify both missing high-risk evidence and existing tests that should be consolidated or removed.
* `IDEA-010` and `IDEA-011` remain backlog ideas. Recommend documentation ownership and navigation changes, but do not promote or implement either idea.
* Do not bump the project version for this review artifact.

## In scope

* Record the reviewed Git revision, project version, verification baseline, and review method.
* Trace a concrete successful Greybridge Use from proposal and trusted submission metadata through authorization, dispatch, resolution, outcome, commitment, canonical state/event evidence, and available perception projection.
* For every trace stage, identify its implemented symbol, inputs, outputs, authority, mutation behavior, test evidence, and relationship to the future transaction boundary. Mark planned or absent stages explicitly.
* Review canonical authority, validation boundaries, state ownership, package/runtime separation, identity generation, outcome commitment, event history, deterministic scheduling, randomness recording, perception separation, and likely repository seams.
* Assess whether M4 can atomically persist one completed simulation step without making SQLite a domain-rule authority or allowing presentation to observe partial state.
* Audit README and documentation navigation against `IDEA-010` and `IDEA-011`, including source-of-truth ownership, duplication risk, missing conceptual guidance, and an incremental documentation recommendation.
* Map high-risk requirements in this task's context to concrete tests. Identify strong tests, missing behavioral evidence, redundant cases, implementation-coupled assertions, and low-diagnostic-value tests.
* Produce severity-ranked, evidence-backed findings and distinguish work required before M4 from work that can occur during M4 or remain deferred.

## Out of scope

* Any implementation, refactoring, schema design, migration, repository interface, test change, package-content change, or documentation rewrite other than the review report.
* Designing the complete turn coordinator, SQLite schema, API, Streamlit UI, NPC policies, System director, or complete Greybridge scenario.
* Reopening accepted product decisions without concrete contradictory evidence.
* Adding generic abstractions, speculative extension points, or recommendations based only on future scale.
* Measuring or optimizing performance.
* Running local LLMs or external services.
* Updating governance documents or marking this task Done.

## Expected contracts and files

Create exactly one review artifact at `doc/reviews/m3-5-kernel-review.md`. It must contain:

1. **Verdict:** `Ready for M4`, `Ready for M4 with prerequisites`, or `Not ready for M4`, followed by concise evidence.
2. **Baseline and method:** reviewed revision, commands, limitations, and how evidence was selected.
3. **Representative Use trace:** a stage table covering proposal, submission, authorization, dispatch, resolution, outcome, commitment, event/state evidence, perception, and the planned persistence/trace boundary.
4. **Boundary assessment:** authority, ownership, data flow, atomicity, replay, and persistence-seam analysis.
5. **Findings:** stable IDs, severity, concrete file/symbol or requirement/test evidence, impact, recommendation, and timing (`before M4`, `during M4`, or `defer`). Include an explicit “no findings” statement for any reviewed category without findings.
6. **Test-value assessment:** requirement-to-test evidence, high-signal strengths, missing high-risk cases, and named consolidation/removal candidates with rationale. Do not propose removal merely because cases look similar.
7. **Documentation-IA assessment:** current source-of-truth map, navigation and duplication problems, and the smallest useful treatment of `IDEA-010` and `IDEA-011`.
8. **Recommended gate:** the minimal accepted work, if any, required before the first M4 persistence task.

The report must distinguish verified facts, inferences, and recommendations. Every blocking or high-severity finding must cite concrete repository evidence and a violated or endangered accepted contract.

## Acceptance criteria

1. The report gives one unambiguous persistence-readiness verdict and does not equate incomplete vertical-slice features with kernel unsafety.
2. The Use trace covers the actual implemented symbols and clearly identifies where the current code ends and planned M4 coordination begins.
3. The boundary assessment explains who may propose, validate, resolve, commit, persist, perceive, and present information, and flags any competing authority with evidence.
4. Persistence analysis addresses atomic state/event/trace storage, failure behavior, immutable replacement, transaction ownership, deterministic scheduling, and recorded randomness without prematurely designing SQLite tables.
5. Findings are severity-ranked, evidence-backed, actionable, and classified by timing; preferences and speculative scaling concerns are not blockers.
6. Test analysis maps the highest-risk reviewed contracts to actual tests and includes both missing-test recommendations and justified consolidation/removal candidates, or an evidence-backed statement that none were found.
7. Documentation analysis evaluates both `IDEA-010` and `IDEA-011` while preserving existing authoritative-document ownership and avoiding a second source of truth.
8. The recommended gate is small enough to preserve forward progress and explicitly lists which findings, if any, must become tasks before SQLite design.
9. No application, test, package, dependency, version, or governance artifact changes are made outside the permitted task status/handoff fields and review report.

## Required verification

* Record `git status --short --branch`, `git rev-parse HEAD`, and the project version before reviewing.
* Run `uv sync --locked`.
* Run `uv run pytest --collect-only -q` and use the inventory as evidence, not as a coverage metric.
* Run `make check`.
* Run `uv lock --check`.
* Run focused tests needed to verify any claimed high-severity or blocking concern.
* Run repository searches or small read-only probes needed to substantiate the trace and test-value findings; record material commands and results in the report.
* Run `git diff --check`.
* Confirm the final diff contains only `doc/reviews/m3-5-kernel-review.md` and permitted Status, Owner, and Handoff report changes in this task brief.

Do not run `make format`: this review may not rewrite existing source files. If a required baseline command fails, distinguish a pre-existing failure from a review-artifact problem and report it exactly.

## Stop conditions

Stop and report a blocker if the assigned checkout does not contain this Ready task, the starting worktree contains unrelated changes, required accepted context contradicts itself so materially that a verdict would be misleading, or verification cannot run without an external service contrary to `DEV-006`.

Do not stop merely because a planned M4 component is absent. Record evidence limitations and classify uncertainty honestly.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
