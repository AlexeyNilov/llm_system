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
| World-readiness validation | Planned | TASK-012, M2 package validation |
| Outcome, state-change, and canonical-event contracts | Planned | TASK-011, world-readiness validation |
| Simulation arbiter and supported operations | Planned | Action, runtime-state, outcome, state-change, and event contracts |
| Recorded random source | Planned | Simulation arbiter |
| Simulation clock and deterministic scheduler | Planned | Event contracts |
| Deterministic perception engine | Planned | Location graph and events |

### M4: Persistence and application boundary

**Outcome:** One world survives restart and advances through an atomic FastAPI turn operation.

| Planned task | Depends on |
| --- | --- |
| SQLite schema and repositories | M3 domain contracts |
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
| Fieldcraft check and progression | Rule pack, recorded randomness |
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
