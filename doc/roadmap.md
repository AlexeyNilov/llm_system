# Roadmap

## Purpose

Show the current delivery sequence, deferred scope, and readiness for delegation. Completed task outcomes remain summarized here and detailed history remains in Git. `doc/tasks/` contains only active work contracts and the reusable template. Only work with a Ready task brief may be delegated.

## Current position

| Milestone | Status | Outcome |
| --- | --- | --- |
| M0: Planning and delegation foundation | Done | Accepted architecture, requirements, terminology, scenario concept, and agent workflow |
| M1: Feasibility and project foundation | Done | Measured local-model behavior, Python 3.12 project, and executable quality gates |
| M2: Packages and domain contracts | Done | Strict versioned YAML packages load into validated typed definitions |
| M3: Deterministic simulation kernel | Done | Pure Python validates worlds and deterministically resolves the supported minimal action set without an LLM or database |
| M3.5: Review before persistence | Done | Accepted the kernel boundary and carried transaction ownership into M4 |
| M3.6: Documentation and context architecture | Done | Separated human orientation from canonical contracts and routed bounded agent context by responsibility |
| M4: Persistence and application boundary | Done | Persist one world and advance it through one atomic application-owned step |
| M5: Actor policies and local LLM integration | Current | Run deterministic and LLM-assisted actors through the shared proposal boundary |

Completed task outcomes remain in this roadmap; task contracts and detailed verification remain recoverable from Git history.

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
| TASK-035: integrated architecture, documentation-IA, and test-value review | Done | Completed M3 kernel | Accepted the kernel as ready for M4; carry full-chain testing into the real coordinator boundary, preserve one transaction owner, and keep documentation/test cleanup non-blocking. |

## M4: Persistence and application boundary

**Outcome:** One world survives restart and advances through an atomic FastAPI turn operation.

| Planned task | Depends on |
| --- | --- |
| TASK-036: SQLite world and canonical-event persistence | Done; depended on completed M3.5 review and M3.6 context-routing rules |
| TASK-037: atomic actor-action coordinator and minimal durable trace | Done; composed the deterministic authority chain and atomically committed SQLite V2 world, event, and completed-trace history |
| Scheduled-activity execution through the atomic coordinator | Deferred beyond M4; waits for accepted environmental, NPC-policy, and System-director execution semantics |
| TASK-038: deterministic world creation, exact-package resume, and destructive development reset | Done; derives and validates revision-0 state, resumes only recorded package versions, and atomically replaces the complete development timeline |
| TASK-039: minimal FastAPI lifecycle and structured player-turn boundary | Done; server-owns trusted identities and provenance, exposes only player-safe results, and preserves lifecycle/turn atomicity |
| TASK-040: deterministic structured-action Streamlit player page | Done; thin HTTP client with all typed proposal forms, validated committed-result presentation, and session-only history |

The first M4 task brief is the pilot for the M3.6 context rules. It must record its pre-code documentation budget, exclude human-orientation and historical artifacts by default, and provide context-used evidence in its handoff. Review should adjust the soft budget only from measured task evidence.

M4 is complete. The singleton world survives restart, advances atomically through FastAPI, and is exercisable through the deterministic Streamlit player page. Deferred scheduled execution does not block this milestone because its activity variants still lack accepted execution semantics.

## M5: Actor policies and local LLM integration

**Outcome:** The caretaker and memory-free courier act through the same validated action-proposal boundary.

| Planned task | Depends on |
| --- | --- |
| TASK-041: rule-driven caretaker policy | Done; strict bounded NPC context plus a pure deterministic seek, take, return, reinforce, or Wait proposal policy at version `0.40.0` |
| TASK-042: local functional model gateway | Done; synchronous fakeable `httpx2` boundary with thinking disabled, strict content-only validation, one repair, and typed attempt evidence at version `0.41.0` |
| TASK-043: player input interpreter | Done; bounded text-plus-perception interpretation into thought, one executable proposal, or safe clarification with generation evidence at version `0.42.0` |
| Durable player-input step traces | Player interpreter, SQLite trace persistence, and accepted action/non-action completion semantics |
| Free-form player turn API | Durable player-input step traces, player interpreter, current perception, and atomic actor-action coordinator |
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
