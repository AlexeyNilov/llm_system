# Roadmap

## Purpose

Show the current delivery sequence, deferred scope, and readiness for delegation. Completed task details belong in `doc/tasks/` and Git history rather than this forward-looking index. Only work with a Ready task brief may be delegated.

## Current position

| Milestone | Status | Outcome |
| --- | --- | --- |
| M0: Planning and delegation foundation | Done | Accepted architecture, requirements, terminology, scenario concept, and agent workflow |
| M1: Feasibility and project foundation | Done | Measured local-model behavior, Python 3.12 project, and executable quality gates |
| M2: Packages and domain contracts | Done | Strict versioned YAML packages load into validated typed definitions |
| M3: Deterministic simulation kernel | Done | Pure Python validates worlds and deterministically resolves the supported minimal action set without an LLM or database |
| M3.5: Review before persistence | Done | Accepted the kernel boundary and carried transaction ownership into M4 |
| M3.6: Documentation and context architecture | Done | Separated human orientation from canonical contracts and routed bounded agent context by responsibility |
| M4: Persistence and application boundary | Current | Persist one world and advance it through one atomic application-owned step |

Completed task contracts and verification evidence remain under [`tasks/`](tasks/).

## Deferred from M3

These are not prerequisites for M3.5 or the initial persistence boundary:

* Help resolution, until a concrete minimal Help mechanic is accepted;
* additional event-witness filtering beyond the implemented self, addressed-speech, speech-overhearing, and Take-witness paths; and
* a concrete random generator, until an accepted random-check mechanic and persistence boundary provide a real consumer.

The application must keep unavailable behavior explicit. Greybridge is not yet a complete playable scenario: its flood, NPC and System activity execution, Help, progression, and some presentation paths remain later work.

## M3.5: Integrated architecture and test-value review

**Outcome:** One independent, read-only review determines whether the current kernel is safe to persist and identifies changes that should happen before M4.

| Planned task | Status | Depends on | Outcome |
| --- | --- | --- | --- |
| [TASK-035](tasks/TASK-035-review-kernel-before-persistence.md): integrated architecture, documentation-IA, and test-value review | Done | Completed M3 kernel | Accepted the kernel as ready for M4; carry full-chain testing into the real coordinator boundary, preserve one transaction owner, and keep documentation/test cleanup non-blocking. |

## M4: Persistence and application boundary

**Outcome:** One world survives restart and advances through an atomic FastAPI turn operation.

| Planned task | Depends on |
| --- | --- |
| [TASK-036](tasks/TASK-036-sqlite-world-and-event-persistence.md): SQLite world and canonical-event persistence | Ready; depends on completed M3.5 review and M3.6 context-routing rules |
| Atomic simulation-step coordinator, transaction, scheduled-activity execution, and trace | SQLite repositories and deterministic scheduling contracts |
| World creation, resume, and reset | Packages and repositories |
| FastAPI turn boundary | Atomic simulation step |
| Deterministic Streamlit player page | FastAPI turn boundary |

The first M4 task brief is the pilot for the M3.6 context rules. It must record its pre-code documentation budget, exclude human-orientation and historical artifacts by default, and provide context-used evidence in its handoff. Review should adjust the soft budget only from measured task evidence.

## M5: Actor policies and local LLM integration

**Outcome:** The caretaker and memory-free courier act through the same validated action-proposal boundary.

| Planned task | Depends on |
| --- | --- |
| Rule-driven caretaker policy | Actor runtime contracts and Greybridge package |
| Local model gateway | Structured-output preflight and Python foundation |
| Player input interpreter | Local model gateway and action contracts |
| Memory-free LLM courier policy | Local model gateway and actor runtime |
| Narrator | Perception snapshots and local model gateway |

## M6: System direction and progression

**Outcome:** Event-driven creative direction and player-visible mechanics complete the LitRPG loop.

| Planned task | Depends on |
| --- | --- |
| System director hooks and action proposals | Simulation-step coordinator and local model gateway |
| System interface notifications | Canonical events and player page |
| Concrete seeded random source and persisted generator state | SQLite repositories and accepted Fieldcraft check contract |
| Fieldcraft check and progression | Rule pack and concrete seeded random source |
| Complete Greybridge content and branches | Stable mechanics and package schemas |

## M7: Inspection and vertical-slice acceptance

**Outcome:** Developers can inspect causal traces and the complete scenario passes end-to-end acceptance.

| Planned task | Depends on |
| --- | --- |
| Read-only inspection API projection | Simulation-step traces |
| Streamlit inspection page | Inspection projection |
| Canonical-state versus perception comparison | Perception snapshots and inspection page |
| End-to-end Greybridge acceptance | Complete initial vertical-slice features |

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

1. confirm upstream dependencies and accepted requirements;
2. resolve architecture-sensitive choices in `decisions.md`;
3. route only the necessary glossary, design, source, and test context;
4. remove choices that would change public behavior or data meaning; and
5. define verifiable acceptance criteria and stop conditions.

Prefer just-in-time briefs. Detailed future briefs become stale and recreate context pollution.
