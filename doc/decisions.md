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

**Decision:** The LLM-assisted System director acts as the creative part of a game master and proposes world-level developments using structured operations. A deterministic simulation arbiter owns rule enforcement and canonical state, and validates and resolves every director proposal before it can take effect. Director context is broad but deliberately selected and inspectable.

**Alternatives considered:** Let the System director directly narrate changes into existence or act as both creative agent and final authority. This is flexible, but makes outcomes inconsistent, difficult to test, and difficult to distinguish from hallucination.

**Consequences:** Creative direction and mechanical authority can be evaluated independently. Player, NPC, and System proposals share a validation boundary. The rules may be loaded or changed through an explicit lifecycle, but the director cannot rewrite them while resolving play.

### 2026-07-11: Separate the simulation kernel from game packages

**Status:** Accepted

**Context:** Rules and scenarios should be easy to change and may eventually be generated from source material. Encoding all game-specific mechanics and content in the application would couple experimentation to core code changes. Making every behavior declarative, however, would require building a general-purpose rule language.

**Decision:** Keep simulation invariants in a stable Python kernel. Load changeable mechanics from versioned rule packs and initial world content from versioned scenario packs. Packages use explicit operations supported by the kernel and are validated before use. Each persistent world records its package identities and versions. Incompatible package changes require an explicit reset or migration.

**Alternatives considered:** Hard-code each game's rules and scenario in the application, or build a universal rule language before implementing the core simulation. Hard-coding impedes experimentation; a universal language would dominate the project before its required semantics are known.

**Consequences:** Common mechanics and content can change independently of the kernel, while state-transition invariants remain testable in Python. Some unusual mechanics may later need explicit Python extension points. Package schemas, validation, compatibility rules, and provenance become important parts of the information architecture.
