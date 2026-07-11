# Decisions

## Why record decisions

Write down key development decisions while the context is fresh. A short note today can save hours later by explaining what was chosen, what was rejected, and why the trade-off made sense at the time.

## Guidance

Use a lightweight Architecture Decision Record (ADR) style:

* Record decisions that affect architecture, data flow, public APIs, dependencies, deployment, security, or long-term maintenance.
* Write the decision when it is made, not after the context has faded.
* Prefer short entries that explain the context, decision, alternatives, and consequences.
* Include enough reasoning for a future maintainer to understand the trade-off.
* Do not document every small implementation detail; focus on choices that would be costly or confusing to rediscover.
* Update or supersede earlier decisions instead of silently rewriting history.

## Entry template

```markdown
### YYYY-MM-DD: Decision title

**Status:** Proposed | Accepted | Superseded

**Context:** What problem, constraint, or trade-off led to this decision?

**Decision:** What was chosen?

**Alternatives considered:** What other options were rejected, and why?

**Consequences:** What becomes easier, harder, riskier, or more constrained?
```

## Actual decisions

### 2026-07-11: The simulation owns truth

**Status:** Accepted

**Context:** LLMs will help describe the world, interpret player input, propose NPC actions, and generate events. If those LLMs can independently change reality, the world will become contradictory and difficult to inspect or test.

**Decision:** Canonical world state and resolved outcomes belong to the simulation. LLMs may interpret state, propose intentions, and narrate outcomes, but they may not directly establish or modify canonical facts. Proposed actions and events must pass through simulation rules before they take effect.

**Alternatives considered:** Treat an LLM conversation or generated narrative as the world state. This is simpler initially, but makes consistency, persistence, validation, and debugging unreliable.

**Consequences:** World state and events must have structured representations. The application must separate perception, intention, validation, state transition, and narration. LLM output must be treated as untrusted proposals, and deterministic tests can verify the simulation independently of generated prose.

### 2026-07-11: Agents receive bounded context

**Status:** Accepted

**Context:** The intended experience is a persistent, inspectable simulation whose participants act from limited knowledge. Giving every LLM the complete world state would undermine believable perception and make prompts harder to reason about.

**Decision:** Each LLM-assisted participant receives a role-specific context assembled from its perception, relevant knowledge, goals, and memories. The player receives a personal narrative derived only from events and state they can perceive.

**Alternatives considered:** Give every participant the full simulation state. This reduces context-assembly work, but permits impossible knowledge, weakens agent identity, increases prompt size, and obscures information flow.

**Consequences:** Information architecture and context engineering are first-class parts of the design. Context sources, selection rules, provenance, and visibility boundaries must be explicit and inspectable. Different roles will require different context views over the same canonical state.

### 2026-07-11: Defer GraphRAG for the first NPC implementation

**Status:** Accepted

**Context:** NPCs need identity, goals, relationships, knowledge, and memory, but the retrieval questions and graph traversal patterns are not yet known. Introducing GraphRAG now would add architectural complexity before its value can be demonstrated.

**Decision:** Begin with structured NPC profiles and simple episodic memory retrieval. Add graph-based retrieval only after concrete use cases show that relationships or multi-hop knowledge cannot be represented or retrieved adequately by the simpler design.

**Alternatives considered:** Build NPC knowledge around GraphRAG from the start. This offers richer relationships in principle, but risks optimizing infrastructure before validating NPC behavior.

**Consequences:** The initial NPC design remains smaller and easier to test. Data boundaries should still allow a later graph representation, but no speculative graph abstraction or dependency will be introduced.

### 2026-07-11: Begin with one persistent world

**Status:** Accepted

**Context:** Persistence is necessary for a coherent ongoing simulation, but multiple worlds, save slots, branching timelines, and offline progression would add lifecycle complexity before the core simulation is validated.

**Decision:** The initial version has one player in one continuously saved world. Completed simulation steps persist their resulting state and event history. Application restarts resume that world, a development operation can reset it to a known scenario, and the world does not advance while the application is stopped.

**Alternatives considered:** Support multiple saves or worlds from the beginning, or treat each application session as a disposable world. Multiple saves add premature management complexity; disposable sessions work against persistence and long-running consequences.

**Consequences:** Persistence can use a simple single-world lifecycle while retaining an inspectable history. Multiple saves, branching, multiplayer, and offline simulation remain outside the initial scope, but can be reconsidered after the core loop works.

### 2026-07-11: Use discrete, action-driven simulation time

**Status:** Accepted

**Context:** Real-time progression would couple world behavior to server uptime, player response speed, and local LLM latency. A rigid round structure would be reproducible, but would assign artificial equal turns to activities with different durations.

**Decision:** World time advances in discrete increments caused by consequential player actions or an explicit wait. Actions have simulation durations. Private thoughts do not advance time. After time advances, the simulation resolves eligible NPC activity and scheduled events before narrating what the player can perceive. No background world ticks run while awaiting player input.

**Alternatives considered:** Advance continuously with wall-clock time, or use fixed rounds in which every participant receives one turn. Continuous time complicates reproducibility and operation; fixed rounds poorly represent actions with different durations.

**Consequences:** Event ordering can be deterministic and inspected independently of LLM response latency. The simulation will need a clock, action durations, and scheduling rules. A later real-time mode could drive the same clock, but is not part of the initial version.

### 2026-07-11: Give NPCs bounded proactive autonomy

**Status:** Accepted

**Context:** Purely reactive NPCs would behave like dialogue interfaces rather than inhabitants of a persistent world. Unrestricted autonomous LLM loops, however, would be expensive, difficult to reproduce, and able to contradict canonical state.

**Decision:** NPCs may proactively propose actions when the simulation scheduler determines they are eligible. Each decision uses bounded NPC-specific context and produces a structured intention. The simulation validates and resolves that intention; the NPC cannot mutate world state directly. NPC activity does not depend on being observed by the player.

**Alternatives considered:** Make NPCs react only to player interactions, or allow NPC agents to run continuously and execute their own changes. Reactive NPCs cannot sustain an independent world; unrestricted loops weaken consistency and control.

**Consequences:** NPCs can pursue goals and cause off-screen consequences while remaining subject to world rules. Decision context, proposed intentions, validation results, and resolved events can be inspected separately. Detailed LLM decisions should be reserved for active NPCs, while distant or inactive NPCs may later use coarser schedules and plans.

### 2026-07-11: Separate creative direction from simulation authority

**Status:** Accepted

**Context:** A traditional game master combines creative direction, rule interpretation, and authority over the game world. Giving all three responsibilities to an LLM would allow creative output to silently override rules and canonical state.

**Decision:** The LLM-assisted System director acts as the creative part of a game master and proposes world-level developments using structured operations. A deterministic simulation arbiter owns rule enforcement and canonical state, and validates and resolves every System director action proposal before it can take effect. System director context is broad but deliberately selected and inspectable.

**Alternatives considered:** Let the System director directly narrate changes into existence or act as both creative agent and final authority. This is flexible, but makes outcomes inconsistent, difficult to test, and difficult to distinguish from hallucination.

**Consequences:** Creative direction and mechanical authority can be evaluated independently. Player, NPC, and System director action proposals share a validation boundary. The rules may be loaded or changed through an explicit lifecycle, but the System director cannot rewrite them while resolving play.

### 2026-07-11: Separate the simulation kernel from game packages

**Status:** Accepted

**Context:** Rules and scenarios should be easy to change and may eventually be generated from source material. Encoding all game-specific mechanics and content in the application would couple experimentation to core code changes. Making every behavior declarative, however, would require building a general-purpose rule language.

**Decision:** Keep simulation invariants in a stable Python kernel. Load changeable mechanics from versioned rule packs and initial world content from versioned scenario packs. Packages use explicit operations supported by the kernel and are validated before use. Each persistent world records its package identities and versions. Incompatible package changes require an explicit reset or migration.

**Alternatives considered:** Hard-code each game's rules and scenario in the application, or build a universal rule language before implementing the core simulation. Hard-coding impedes experimentation; a universal language would dominate the project before its required semantics are known.

**Consequences:** Common mechanics and content can change independently of the kernel, while state-transition invariants remain testable in Python. Some unusual mechanics may later need explicit Python extension points. Package schemas, validation, compatibility rules, and provenance become important parts of the information architecture.

### 2026-07-11: Build an open simulation with a lightweight game layer

**Status:** Accepted

**Context:** A fixed plot or command menu would make behavior easier to constrain, but would undermine experimentation and autonomous consequences. A completely unstructured conversational sandbox would offer freedom without legible mechanics, stakes, or a recognizably LitRPG experience.

**Decision:** The player interacts through free-form intentions in an open simulation. Scenario packs provide situations, pressures, and opportunities rather than mandatory plots. Rule packs provide lightweight, visible mechanics such as abilities, resources, action resolution, and progression. The System director may propose objectives for presentation by the System interface, but the player can ignore or oppose them and experience the resulting consequences.

**Alternatives considered:** Build a scripted game with a prescribed story, or build a mechanics-free narrative sandbox. The scripted approach limits emergence; the sandbox makes outcomes difficult to understand and weakens the role of the player-visible System interface.

**Consequences:** The intention interpreter must map open-ended input onto supported operations without inventing mechanics. Local conflicts can succeed or fail while the persistent world continues. The initial vertical slice must demonstrate both meaningful freedom and at least one visible progression event.

### 2026-07-11: Separate the hidden System director from the visible System interface

**Status:** Accepted

**Context:** LitRPG conventions benefit from a System interface that communicates abilities, status, progression, and objectives to the player. If the creative System director speaks directly, however, generated language could be mistaken for an authoritative mechanical outcome.

**Decision:** The System director remains an internal creative agent. A separate diegetic System interface presents player-visible mechanical facts confirmed by the simulation arbiter. An LLM may style those notifications but cannot change their factual payload. The narrator remains responsible for perceived world events.

**Alternatives considered:** Hide all mechanics behind narration, or allow the System director to address the player directly. Hidden mechanics weaken the LitRPG experience; direct director speech conflates creative proposals with canonical facts.

**Consequences:** System notifications need structured factual payloads distinct from their presentation. Mechanical communication can be tested without testing generated prose. Objectives offered through the interface remain optional until accepted by the player.

### 2026-07-11: Model space as a location graph with deterministic perception

**Status:** Accepted

**Context:** The simulation needs movement, visibility, travel time, barriers, and descriptions of a character's surroundings. Letting an LLM invent space on demand would undermine canonical truth, while exact continuous geometry would add pathfinding and measurement complexity unnecessary for the initial experience.

**Decision:** Represent world topology as structured location nodes connected by explicit traversal edges. Characters and objects have canonical locations. A deterministic perception component derives what an observer can detect from world state, and the narrator turns only that perception snapshot into prose. Within-location positioning initially uses coarse relationships rather than exact coordinates.

**Alternatives considered:** Use an LLM-generated map implicit in narrative history, or begin with a coordinate grid or continuous geometry. Narrative maps are inconsistent; geometric maps introduce complexity before the simulation requires precise distance.

**Consequences:** Scenario maps can be validated using graph properties such as reachability and connectivity. Connections can carry direction, duration, requirements, and state. Optional coordinates may later support visual presentation or import workflows without becoming the initial source of mechanical truth.

### 2026-07-11: Separate truth, perception, memory, and belief

**Status:** Accepted

**Context:** NPCs need to remember, infer, misunderstand, learn, and potentially be deceived without changing what is canonically true. Treating retrieved text as truth would collapse those distinctions and leak unavailable information into decisions.

**Decision:** Maintain separate representations for canonical world state, current character perception, durable episodic memories, and mutable beliefs. Character decision context combines only character-available information with identity, goals, and plans. Vector search may select relevant memories, but its index is derived and rebuildable rather than authoritative.

**Alternatives considered:** Give NPCs canonical state directly, or treat a vector database as the canonical memory store. Direct access creates impossible knowledge; vector retrieval does not provide an adequate durable or auditable source of truth.

**Consequences:** NPCs can hold false or uncertain beliefs while the simulation remains consistent. Observations and memories need provenance and simulation-time metadata. Primary persistence owns memory records, while Qdrant can be used as an optional retrieval projection.

### 2026-07-11: Use an explicit cognition and action loop

**Status:** Accepted

**Context:** Actors need a consistent path from world events to perception, interpretation, choice, action, consequence, and learning. Without explicit boundaries, canonical facts can leak into character reasoning and generated intentions can be mistaken for completed actions.

**Decision:** Model NPC behavior as canonical reality, perceptual filtering, observation and memory, sensemaking, intent, structured action proposal, arbiter resolution, outcome, and renewed perceptual filtering. Feedback is actor-specific evidence about an outcome and does not bypass perception. For the player, the human owns sensemaking and intent; the application interprets only explicitly supplied thoughts and attempted actions.

**Alternatives considered:** Use a single LLM call from world state directly to narrative and state changes, or give actors direct outcome feedback. A single call collapses responsibilities; direct feedback gives actors knowledge they may not possess.

**Consequences:** Each stage has explicit inputs and outputs and can be tested or inspected independently. Character traits and limitations can affect the appropriate stage. Player motives must not be silently invented by the application.

### 2026-07-11: Make NPC decision policies interchangeable

**Status:** Accepted

**Context:** Not every actor benefits from open-ended LLM reasoning. Simple creatures, routine behaviors, and strong archetypes can be represented more coherently and cheaply with limited action sets, priorities, schedules, or deterministic rules.

**Decision:** NPC decision-making uses a common contract from bounded decision context to structured action proposal. An NPC may use a rule-based, scripted, LLM-assisted, or hybrid policy. Prefer rule-based behavior when it adequately represents the actor. Archetypes provide defaults that individual NPC definitions may override. Every policy remains subject to arbiter validation and cannot modify canonical state.

**Alternatives considered:** Use an LLM for every NPC, or hard-code one global behavior system. Universal LLM use adds latency and weakens predictability; one fixed behavior system cannot represent both simple and socially complex actors well.

**Consequences:** LLM calls can be reserved for decisions that require richer interpretation. Different policies can be compared under the same inputs and tested against the same output contract. Behavioral simplicity is modeled through actual constraints rather than prompts asking a model to reason poorly.

### 2026-07-11: Validate the architecture with a non-combat vertical slice

**Status:** Accepted

**Context:** The first playable scenario must exercise the architectural boundaries without requiring a large game-mechanics subsystem. Combat would introduce targeting, range, health, damage, equipment, incapacitation, death, and balance before the core actor loop is validated.

**Decision:** Build a compact non-combat scenario with three connected locations, one player, one rule-driven NPC, one LLM-assisted NPC, a scheduled environmental event, incomplete or mistaken knowledge, an optional objective, basic world interactions, a skill check, visible progression, and restart persistence.

**Alternatives considered:** Begin with combat, or build isolated technical components without a playable scenario. Combat expands scope sharply; disconnected components do not validate their integration into a coherent experience.

**Consequences:** The vertical slice can test every major information and authority boundary with limited mechanics. Combat remains a future rule-pack extension rather than a kernel concern.

### 2026-07-11: Use SQLite as the initial authoritative store

**Status:** Accepted

**Context:** The initial deployment is local, single-player, and single-world, but requires transactional persistence, restart recovery, event history, character memory, and inspectable traces. A separate database service would add operations without addressing a current concurrency or scale requirement.

**Decision:** Use SQLite as the authoritative store for initial world and character data. Commit completed simulation steps atomically. Treat Qdrant as a rebuildable retrieval projection over durable memory data rather than an authoritative store.

**Alternatives considered:** Begin with PostgreSQL, use Qdrant as the primary memory store, or persist ad hoc JSON files. PostgreSQL is premature operational complexity; Qdrant is not the canonical record; multiple JSON files make transactional consistency and querying harder.

**Consequences:** Local setup and inspection remain simple while the simulation gains transactional guarantees. Persistence access must remain behind repository boundaries so a later concurrency requirement can justify a different database without changing domain logic.

### 2026-07-11: Author game packages in YAML and validate with Pydantic

**Status:** Accepted

**Context:** Rule and scenario packages must be comfortable to hand-author, inspect, diff, and eventually generate, while the simulation kernel requires strict typed inputs. JSON is verbose for substantial scenario content, and raw YAML mappings are too permissive to form a runtime boundary.

**Decision:** Use YAML as the package authoring format. Safely parse package files and validate them into strict Pydantic models before simulation logic can access them. Require explicit schema versions, package identities and versions, stable record identifiers, valid cross-references, and supported operations. Do not permit executable YAML constructs.

**Alternatives considered:** Use JSON, TOML, or unvalidated YAML dictionaries at runtime. JSON is less author-friendly for narrative content; TOML is awkward for deeply nested world data; raw dictionaries allow ambiguous types and delayed failures.

**Consequences:** Authors and future generation tools get readable source files, while the kernel receives typed trusted models. Package validation becomes an early implementation boundary and requires high-signal schema and reference tests.

### 2026-07-11: Use recorded seeded randomness only for explicit checks

**Status:** Accepted

**Context:** Uncertainty can make checks and consequences interesting, but uncontrolled randomness makes failures difficult to reproduce and lets generated narration obscure why an outcome occurred.

**Decision:** Resolve outcomes deterministically unless a rule explicitly requests a random check. The simulation arbiter owns a seeded pseudorandom source, persists its state, and records the purpose, parameters, and result of every canonical draw. LLMs cannot supply random outcomes. The arbiter accepts an injected random source for tests.

**Alternatives considered:** Make all outcomes deterministic, use unrecorded process randomness, or let an LLM choose uncertain results. Fully deterministic play reduces uncertainty; unrecorded and LLM-selected outcomes cannot be reliably replayed or audited.

**Consequences:** Canonical outcomes can be explained and reproduced. Unit tests can force boundary results through an injected source, while seeded integration tests can verify longer stable flows without coupling every unit test to one pseudorandom algorithm.

### 2026-07-11: Serialize eligible activities deterministically

**Status:** Accepted

**Context:** Multiple environmental events, NPCs, and System director hooks may become eligible when one player action advances simulation time. True simultaneous mutation would require conflict-resolution semantics and make causal ordering harder to inspect.

**Decision:** Resolve scheduled activities serially in a deterministic queue ordered by simulation time, phase priority, and stable insertion sequence. At the same time, scheduled environmental events precede NPC activity, which precedes System director hooks. The triggering player action resolves before the activities made eligible by its time advancement. Record ordering metadata in the step trace.

**Alternatives considered:** Allow concurrent state mutation, or rely on incidental database or collection ordering. Concurrency creates avoidable conflicts; incidental ordering is not reproducible or meaningful.

**Consequences:** Each activity sees a defined committed predecessor state, and causal chains can be replayed. The initial model does not provide true simultaneity; a future rule set requiring simultaneous declarations would need an explicit proposal-batch and conflict-resolution design.

### 2026-07-11: Maintain a canonical domain glossary

**Status:** Accepted

**Context:** The architecture uses familiar terms with narrow meanings, including System director, System interface, intent, action proposal, outcome, event, perception, observation, memory, and belief. Without explicit definitions, documentation, prompts, schemas, code, and tests can silently use incompatible concepts.

**Decision:** Maintain `doc/glossary.md` as the canonical domain vocabulary. Project artifacts use its terms consistently and update it when accepted design introduces or changes a concept. Avoid ambiguous bare terms such as System and director in technical writing.

**Alternatives considered:** Rely on conversational context or define terms independently in each document. Conversation context is temporary; local definitions drift and make cross-component contracts harder to understand.

**Consequences:** Naming becomes part of the information architecture and can guide schemas, interfaces, prompts, and tests. Glossary changes require attention because they may signal a domain-model or public-contract change rather than a prose edit.
