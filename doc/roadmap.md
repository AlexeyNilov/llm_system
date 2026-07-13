# Roadmap

## Purpose

Sequence the initial vertical slice by dependency and control when work is ready for delegation. A roadmap item is not a task contract. Only items with a Ready task brief may be assigned to an implementation agent.

## Milestones

### M0: Planning and delegation foundation

**Outcome:** Accepted architecture, requirements, terminology, initial scenario, agent workflow, and task template exist in the repository.

**Status:** Done

### M1: Feasibility and project foundation

**Outcome:** Local model constraints are measured and the Python project has executable quality gates.

| Task | Status | Dependency | Outcome |
| --- | --- | --- | --- |
| [`TASK-001`](tasks/TASK-001-structured-output-preflight.md) | Done | None | Thinking-enabled structured-output baseline |
| [`TASK-001A`](tasks/TASK-001A-disable-thinking-comparison.md) | Done | TASK-001 | Controlled request-time thinking-disable comparison |
| [`TASK-002`](tasks/TASK-002-python-project-scaffold.md) | Done | None | Reproducible Python package and executable quality gates |

### M2: Packages and domain contracts

**Outcome:** Strict YAML package loading produces trusted typed domain models.

| Task | Status | Depends on |
| --- | --- | --- |
| [`TASK-003`](tasks/TASK-003-game-package-manifests.md): Rule and scenario package manifests | Done | TASK-002 |
| [`TASK-004`](tasks/TASK-004-spatial-definitions.md): Location, connection, and spatial-graph definitions | Done | TASK-003 |
| [`TASK-005`](tasks/TASK-005-entity-definitions.md): Object, player-character, NPC-character, and entity-collection definitions | Done | TASK-004 |
| [`TASK-006`](tasks/TASK-006-rule-pack-definition.md): Rule-pack archetype and policy reference catalogs | Done | TASK-005 |
| [`TASK-007`](tasks/TASK-007-scenario-pack-definition.md): Scenario-pack entrypoint root definition | Done | TASK-006 |
| [`TASK-008`](tasks/TASK-008-typed-game-package-loading.md): Typed rule and scenario entrypoint loading | Done | TASK-007 |
| [`TASK-009`](tasks/TASK-009-game-package-semantic-validation.md): Cross-reference and graph validation | Done | TASK-008 |
| [`TASK-010`](tasks/TASK-010-greybridge-package-foundation.md): Minimal Greybridge rule and scenario package skeletons | Done | TASK-009 |

### M3: Deterministic simulation kernel

**Outcome:** Pure Python logic resolves supported actions without an LLM or database.

| Planned task | Status | Depends on |
| --- | --- | --- |
| [`TASK-011`](tasks/TASK-011-actor-action-proposal-contracts.md): Actor action proposal and trusted submission contracts | Done | M2 domain models |
| [`TASK-012`](tasks/TASK-012-runtime-state-contracts.md): Canonical runtime-state structural contracts | Done | TASK-011, M2 domain models |
| [`TASK-013`](tasks/TASK-013-world-state-validation.md): World-state relational validation | Done | TASK-012, TASK-009 |
| [`TASK-014`](tasks/TASK-014-state-change-event-contracts.md): State-change and canonical-event contracts | Done | TASK-011, TASK-013 |
| [`TASK-015`](tasks/TASK-015-outcome-contracts.md): Outcome contracts and context-free consistency | Done | TASK-014 |
| [`TASK-016`](tasks/TASK-016-outcome-commitment-core.md): Arbiter outcome-commitment core | Done | TASK-013, TASK-015 |
| [`TASK-017`](tasks/TASK-017-actor-action-authorization.md): Actor-action submission authorization | Done | TASK-011, TASK-013 |
| [`TASK-018`](tasks/TASK-018-wait-resolver.md): Deterministic Wait resolver | Done | TASK-014 through TASK-017 |
| [`TASK-019`](tasks/TASK-019-move-resolver.md): Deterministic Move resolver | Done | TASK-013 through TASK-018 |
| [`TASK-020`](tasks/TASK-020-actor-action-dispatch.md): Actor-action operation dispatch | Done | TASK-017, TASK-018, TASK-019 |
| [`TASK-023`](tasks/TASK-023-observe-resolver.md): Deterministic Observe v0 resolver | Done | TASK-017, TASK-020, TASK-022 |
| [`TASK-028`](tasks/TASK-028-speak-resolver.md): Deterministic co-located Speak v0 resolver | Done | TASK-017, TASK-020 |
| [`TASK-030`](tasks/TASK-030-take-resolver.md): Deterministic co-located Take v0 resolver | Ready | TASK-013 through TASK-020 |
| Remaining Use and Help resolvers | Planned | Authorization plus accepted per-operation mechanics |
| [`TASK-027`](tasks/TASK-027-recorded-integer-draw-boundary.md): Recorded integer-draw contracts and injected source boundary | Done | Simulation arbiter |
| [`TASK-025`](tasks/TASK-025-scheduled-activity-contracts.md): Scheduled-activity and queue contracts | Done | M3 domain models |
| [`TASK-026`](tasks/TASK-026-scheduled-activity-selection.md): Deterministic eligibility selection and ordering | Done | TASK-025, TASK-013 |
| [`TASK-021`](tasks/TASK-021-perception-contracts.md): Observation and perception-snapshot contracts | Done | TASK-012, TASK-014 |
| [`TASK-022`](tasks/TASK-022-current-state-perception.md): Deterministic current-state perception projection | Done | TASK-013, TASK-021 |
| [`TASK-024`](tasks/TASK-024-self-event-feedback.md): Stateless self-action event feedback | Done | TASK-014, TASK-021, TASK-022 |
| [`TASK-029`](tasks/TASK-029-addressed-speech-feedback.md): Addressed-speech recipient feedback | Done | TASK-024, TASK-028 |
| Remaining witness event-feedback filtering | Planned | Addressed-speech feedback and accepted event-specific visibility semantics |

### M3.5: Architecture review before persistence

**Outcome:** An independent, read-only review confirms that the completed deterministic-kernel contracts are ready to become persistent and application-facing boundaries.

| Planned task | Depends on | Outcome |
| --- | --- | --- |
| Architecture boundary review | M3 deterministic kernel | Trace a representative player turn; check authority, data ownership, requirement coverage, and testability; assess the documentation information architecture described by IDEA-010 and IDEA-011; record evidence, design gaps, and promotion recommendations for the architect or integrator to resolve before M4. |
| Test-suite value review | M3 deterministic kernel | Map requirements and deterministic-kernel contracts to behavioral tests; identify missing high-risk coverage, redundant or implementation-coupled tests, and tests with low diagnostic value; record evidence-backed recommendations for additions, consolidation, or removal before M4. |

### M4: Persistence and application boundary

**Outcome:** One world survives restart and advances through an atomic FastAPI turn operation.

| Planned task | Depends on |
| --- | --- |
| SQLite schema and repositories | M3 domain contracts, M3.5 architecture review |
| Atomic simulation-step transaction and trace | SQLite repositories, scheduler |
| World creation, resume, and reset | Packages, repositories |
| FastAPI turn boundary | Atomic simulation step |
| Deterministic Streamlit player page | FastAPI turn boundary |

### M5: Actor policies and local LLM integration

**Outcome:** The caretaker and memory-free courier act through the same validated action-proposal boundary.

| Planned task | Depends on |
| --- | --- |
| Rule-driven caretaker policy | Actor runtime contracts, Greybridge package |
| Local model gateway | TASK-001A, TASK-002 |
| Player input interpreter | Local model gateway, action contracts |
| Memory-free LLM courier policy | Local model gateway, actor runtime |
| Narrator | Perception snapshots, local model gateway |

### M6: System direction and progression

**Outcome:** Event-driven creative direction and player-visible mechanics complete the LitRPG loop.

| Planned task | Depends on |
| --- | --- |
| System director hooks and action proposals | Scheduler, local model gateway |
| System interface notifications | Canonical events, Streamlit player page |
| Concrete seeded random source and persisted generator state | TASK-027, SQLite repositories, accepted Fieldcraft check contract |
| Fieldcraft check and progression | Rule pack, concrete seeded random source |
| Complete Greybridge content and branches | Stable mechanics and package schemas |

### M7: Inspection and vertical-slice acceptance

**Outcome:** Developers can inspect causal traces and the complete scenario passes end-to-end acceptance.

| Planned task | Depends on |
| --- | --- |
| Read-only inspection API projection | Simulation-step traces |
| Streamlit inspection page | Inspection projection |
| Canonical-state versus perception comparison | Perception snapshots, inspection page |
| End-to-end Greybridge acceptance | M1 through M7 features |

## Post-slice work

Do not promote these items until the initial vertical slice is accepted:

* episodic memory and Qdrant retrieval;
* mutable beliefs and belief revision;
* GraphRAG;
* combat;
* generated game packages or maps;
* richer world lifecycles; and
* experiential decision-making evaluation.

See [`ideas.md`](ideas.md) for postponed possibilities and their revisit conditions.

## Readiness rules

Before creating a Ready task brief:

1. identify upstream task dependencies;
2. confirm required behavior already exists in `requirements.md`;
3. confirm architecture-sensitive choices exist in `decisions.md`;
4. identify exact glossary terms and design sections;
5. remove unresolved implementation choices that would change public contracts or data meaning; and
6. write verifiable acceptance criteria and stop conditions.

Prefer just-in-time task briefs. Detailed briefs written far ahead of their dependencies become stale and recreate the same context-pollution problem this workflow is intended to solve.
