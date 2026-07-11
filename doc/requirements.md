# Requirements

## EARS (Easy Approach to Requirements Syntax)

Use the EARS structure for precise requirements:

> **While** `<optional precondition>`, **when** `<optional trigger>`, **the system shall** `<system response>`.

This helps ensure requirements are:

* Context-aware
* Trigger-based
* Action-specific

## Guidance

* Describe externally observable behavior and constraints, not implementation details.
* Give each requirement a stable identifier so designs, tests, and discussions can refer to it.
* Keep each requirement focused on one meaningful behavior.
* Add requirements only after they are accepted; keep unresolved questions outside this section.
* Update or supersede requirements explicitly instead of silently changing their meaning.

## Actual requirements

### World persistence

**WORLD-001:** The system shall operate with one persistent world and one player in the initial version.

**WORLD-002:** While a world exists, when the application restarts, the system shall restore the most recently committed canonical world state.

**WORLD-003:** When a simulation step completes successfully, the system shall persist its resulting canonical state before treating that step as complete.

**WORLD-004:** When an authorized development reset is requested, the system shall replace the current world with a known initial scenario.

**WORLD-005:** When a state transition is committed, the system shall retain an event record sufficient to inspect how the world reached its current state.

**WORLD-006:** While the application is not running, the world shall not advance automatically.

### Simulation time

**TIME-001:** The system shall represent world progression using simulation time that is independent of elapsed wall-clock time.

**TIME-002:** When an accepted player action has consequences in the world, the system shall advance simulation time by the duration assigned to that action.

**TIME-003:** When the player expresses only private thoughts, the system shall not advance simulation time.

**TIME-004:** When the player chooses to wait, the system shall advance simulation time by the requested valid duration.

**TIME-005:** When simulation time advances, the system shall resolve NPC activity and scheduled events that become eligible before presenting the resulting perceived events to the player.

**TIME-006:** While waiting for player input, the system shall not advance simulation time or run background world ticks.

### NPC autonomy

**NPC-001:** When an NPC becomes eligible to act, the system shall allow that NPC to propose an action without requiring a player interaction to trigger the proposal.

**NPC-002:** When requesting an NPC decision, the system shall provide only information available to that NPC together with relevant identity, goals, plans, and memories.

**NPC-003:** When an NPC decides what to do, the NPC decision process shall return a structured intention and shall not modify canonical world state.

**NPC-004:** When an NPC proposes an intention, the simulation shall validate and resolve it before applying any resulting state transition.

**NPC-005:** When an NPC proposes an invalid or impossible intention, the intention shall not change canonical world state.

**NPC-006:** The system shall allow eligible NPCs to act regardless of whether the player can currently observe them.

**NPC-007:** When an NPC action or its consequences are outside the player's perception, the system shall not reveal them directly to the player.

### System director and simulation authority

**AUTH-001:** The simulation arbiter shall be the only component authorized to apply transitions to canonical world state.

**AUTH-002:** When the System director creates a world-level proposal, it shall express that proposal as a structured action proposal using a supported operation.

**AUTH-003:** When the System director submits an action proposal, the simulation arbiter shall validate and resolve it before applying any resulting state transition.

**AUTH-004:** When a System director action proposal violates the loaded rules or refers to an unsupported operation, the action proposal shall not change canonical world state.

**AUTH-005:** When requesting a System director decision, the system shall provide a deliberately selected and inspectable world-level context.

**AUTH-006:** The System director shall not modify the rules used by the simulation arbiter while a simulation step is being resolved.

### Game packages

**PACK-001:** The simulation kernel shall load changeable game mechanics from a versioned rule pack.

**PACK-002:** The simulation kernel shall load initial world content from a versioned scenario pack.

**PACK-003:** Before creating or resuming a world, the system shall validate the selected rule and scenario packs and reject invalid packages without changing canonical world state.

**PACK-004:** When a world is created, the system shall record the identities and versions of the rule and scenario packs used to create it.

**PACK-005:** When a selected package is incompatible with an existing world, the system shall require an explicit world reset or migration rather than silently applying the package.

**PACK-006:** The simulation kernel shall expose only explicit, supported operations to rule and scenario packs.

**PACK-007:** Rule and scenario packages shall use YAML as their human-authored serialization format.

**PACK-008:** Each package shall declare an explicit schema version, package identifier, and package version.

**PACK-009:** Each addressable package record shall use a stable explicit identifier for cross-references.

**PACK-010:** Before package data reaches simulation logic, the system shall safely parse it and validate it into strict Pydantic models.

**PACK-011:** The package loader shall reject executable YAML constructs, invalid types, unresolved references, and unsupported operations before creating or resuming a world.

### Player experience

**PLAY-001:** The system shall allow the player to express attempted actions in free-form text.

**PLAY-002:** When the player expresses an attempted action, the system shall interpret it as a structured intention supported by the loaded rule pack or report that it cannot be performed.

**PLAY-003:** The system shall not require the player to follow a predetermined sequence of scenario events.

**PLAY-004:** When the System interface presents an objective or opportunity proposed by the System director, the player shall remain free to pursue, ignore, or oppose it subject to world consequences.

**PLAY-005:** The system shall resolve player intentions using the loaded mechanics and canonical world state before narrating their outcomes.

**PLAY-006:** When a scenario-level conflict succeeds or fails, the world shall remain capable of continuing unless a rule explicitly ends the simulation.

**PLAY-007:** The initial vertical slice shall include at least one player-visible progression event governed by the loaded rule pack.

### Player-visible System interface

**UI-001:** The system shall keep the internal System director hidden from the player.

**UI-002:** When the simulation arbiter produces a player-visible mechanical fact, the System interface shall present that fact to the player as an in-world notification.

**UI-003:** The System interface shall not present an ability change, status effect, reward, or other mechanical outcome unless it is present in arbiter-confirmed state or events.

**UI-004:** When an LLM styles a System notification, it shall preserve the notification's arbiter-confirmed factual payload.

**UI-005:** The narrator shall describe perceived world events separately from player-visible System notifications.

**UI-006:** When the System interface presents an optional objective, it shall not treat that objective as accepted without a player decision.

### Spatial world model

**SPACE-001:** The system shall represent traversable world topology as a graph of structured locations and explicit connections.

**SPACE-002:** The system shall record the canonical location of each spatial character and object.

**SPACE-003:** When a character attempts to move, the simulation shall permit movement only through a connection whose requirements are satisfied.

**SPACE-004:** The system shall derive character perception deterministically from canonical location, connection, entity, environmental, and visibility state.

**SPACE-005:** When requesting a world description from the narrator, the system shall provide only the perception snapshot available to the observing character.

**SPACE-006:** The narrator shall not add locations, connections, characters, objects, or spatial relationships that are absent from the supplied perception snapshot.

**SPACE-007:** The initial spatial model shall use coarse within-location relationships rather than requiring exact geometric coordinates.

### Character knowledge and memory

**KNOW-001:** The system shall keep canonical world state separate from each character's perceptions, memories, and beliefs.

**KNOW-002:** When a character perceives an event or state, the system shall record an observation containing the perceived information, simulation time, source, and relevant confidence or salience metadata.

**KNOW-003:** The system shall preserve episodic memory records in durable primary storage independently of any vector retrieval index.

**KNOW-004:** The system shall allow a character's beliefs to be incomplete, uncertain, or inconsistent with canonical world state.

**KNOW-005:** When assembling character decision context, the system shall select from that character's current perception, identity, goals, plans, beliefs, and episodic memories without exposing unavailable canonical facts.

**KNOW-006:** When a vector index is unavailable or rebuilt, durable character memory records shall remain intact.

### Episodic-memory retrieval

**MEMORY-001:** When assembling NPC decision context with memory enabled, the system shall apply a bounded retrieval policy rather than include all episodic memories.

**MEMORY-002:** The memory-enabled decision context shall prioritize configured high-salience memories, recent memories, and semantically relevant memories within a hard context budget.

**MEMORY-003:** The memory retrieval policy shall deduplicate selected memories and preserve each included memory's stable identifier and provenance.

**MEMORY-004:** Semantic memory retrieval shall search only memories available to the NPC whose context is being assembled.

**MEMORY-005:** When Qdrant is unavailable, context assembly shall fall back to recent and high-salience memories without losing durable episodic memory records.

**MEMORY-006:** Memory context limits and source allocations shall be explicit configuration rather than hidden prompt behavior.

### Belief revision

**BELIEF-001:** When NPC sensemaking proposes a belief change, it shall express the change as a structured belief revision proposal rather than writing belief state directly.

**BELIEF-002:** A belief revision proposal shall identify its NPC owner, requested operation, affected belief, confidence, and available observations, memories, or beliefs used as its basis.

**BELIEF-003:** Before applying a belief revision proposal, the actor runtime shall validate ownership, referenced information, supported operations, and confidence bounds.

**BELIEF-004:** An accepted belief revision shall change only the owning NPC's internal belief state and shall not change canonical world state.

**BELIEF-005:** The system shall retain belief revision history, including the proposal basis and validation result.

**BELIEF-006:** The system shall support deterministic and LLM-assisted belief revision through the same structured boundary.

**BELIEF-007:** The system shall not infer or revise player beliefs automatically.

### Actor cognition and action loop

**LOOP-001:** When canonical state or events may be observable by a character, the system shall apply that character's perceptual constraints before producing observations.

**LOOP-002:** When an NPC performs sensemaking, the system shall limit its inputs to current observations and character-available identity, goals, plans, beliefs, and memories.

**LOOP-003:** NPC sensemaking shall produce character-internal appraisal or belief changes and shall not modify canonical world state.

**LOOP-004:** When an NPC selects an intent, its decision process shall express any attempted means as a structured action proposal.

**LOOP-005:** When an actor submits an action proposal, the simulation arbiter shall validate and resolve it into an outcome before applying canonical state transitions or events.

**LOOP-006:** When an outcome produces information available to a character, that information shall re-enter the character loop through perceptual filtering rather than direct access to canonical outcome data.

**LOOP-007:** The system shall leave player sensemaking and intent under human control and shall not infer them as canonical facts beyond what the player explicitly expresses.

### NPC decision policies

**POLICY-001:** The system shall support interchangeable NPC decision policies that accept bounded character decision context and return a structured action proposal.

**POLICY-002:** The system shall support NPC decisions produced by deterministic rules without requiring an LLM call.

**POLICY-003:** The system shall support NPC decisions produced by an LLM within the same proposal and validation boundary as rule-based decisions.

**POLICY-004:** The system shall allow an NPC decision policy to combine explicit behavioral constraints with LLM-assisted choice.

**POLICY-005:** No NPC decision policy shall modify canonical world state directly.

**POLICY-006:** The system shall allow individual NPC configuration to override behavioral defaults inherited from an archetype.

### Initial vertical slice

**SLICE-001:** The initial playable scenario shall contain three connected locations, one player, one rule-driven NPC, and one LLM-assisted NPC.

**SLICE-002:** The initial playable scenario shall include one scheduled environmental event and at least one hidden fact available to different characters through different observations.

**SLICE-003:** The initial playable scenario shall allow the System interface to present at least one optional objective.

**SLICE-004:** The initial playable scenario shall support observing, moving, speaking, taking an object, using an object, helping a character, and waiting.

**SLICE-005:** The initial playable scenario shall include at least one rule-governed skill check and one player-visible progression event.

**SLICE-006:** The initial playable scenario shall preserve canonical state and event history across an application restart.

**SLICE-007:** Combat mechanics shall remain outside the initial vertical slice.

**SLICE-008:** Mutable NPC belief state and belief revision shall remain outside the initial vertical slice.

**SLICE-009:** Episodic memory retrieval and Qdrant integration shall remain outside the initial vertical slice.

**SLICE-010:** The initial vertical slice shall not provide prior conversation history to an NPC as an undeclared substitute for episodic memory.

### Primary persistence

**STORE-001:** The initial version shall persist authoritative world and character data in SQLite.

**STORE-002:** When a simulation step completes, the system shall commit its canonical state transitions and events atomically before reporting completion.

**STORE-003:** The SQLite store shall preserve world metadata, simulation time, canonical entities and locations, committed events, character memories and beliefs, and simulation-step traces across application restarts.

**STORE-004:** When an authoritative SQLite transaction fails, the system shall not report the associated simulation step as completed.

**STORE-005:** Qdrant shall remain a derived retrieval index and shall not be required to recover authoritative world or character history.

### Outcome randomness

**RANDOM-001:** The simulation shall resolve outcomes deterministically unless a loaded rule explicitly requires a random check.

**RANDOM-002:** The simulation arbiter shall be the only component authorized to draw randomness used by canonical outcome resolution.

**RANDOM-003:** The system shall persist the world random seed and generator state required for continued reproducible resolution.

**RANDOM-004:** When the arbiter draws a random value, the resulting event history shall record the draw's purpose, parameters, and result.

**RANDOM-005:** LLM components shall not generate or replace canonical random results.

**RANDOM-006:** The arbiter shall accept an injected random source so tests can exercise specified outcomes without depending on a pseudorandom implementation sequence.

### Activity scheduling

**SCHEDULE-001:** The scheduler shall order eligible activities by simulation time, explicit phase priority, and stable insertion sequence.

**SCHEDULE-002:** For activities due at the same simulation time, the default phase order shall be scheduled environmental events, NPC activities, and System director hooks.

**SCHEDULE-003:** The system shall resolve the triggering player action before processing activities made eligible by that action's time advancement.

**SCHEDULE-004:** The scheduler shall submit eligible activities to the simulation arbiter serially and shall not permit simultaneous canonical state mutation.

**SCHEDULE-005:** The system shall record scheduling and ordering metadata in the simulation-step trace.

**SCHEDULE-006:** Given the same committed state and scheduled activities, the scheduler shall produce the same activity order.

### System director eligibility

**DIRECTOR-001:** The system shall invoke the System director only when an explicit configured hook becomes eligible.

**DIRECTOR-002:** Rule or scenario packages shall be able to configure System director hooks for world creation, matching canonical events, scenario milestones, or elapsed simulation-time intervals.

**DIRECTOR-003:** A System director hook shall declare limits that prevent invocation more frequently than its configured minimum simulation-time interval or maximum count.

**DIRECTOR-004:** When no System director hook is eligible, the system shall not invoke the System director.

**DIRECTOR-005:** When a System director hook becomes eligible, the simulation-step trace shall record the hook identifier and eligibility reason.

**DIRECTOR-006:** System director eligibility shall not bypass simulation arbiter validation of any resulting action proposal.
