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

### System direction and simulation authority

**AUTH-001:** The simulation arbiter shall be the only component authorized to apply transitions to canonical world state.

**AUTH-002:** When the System director creates a world-level proposal, it shall express that proposal using a structured intention or event type.

**AUTH-003:** When the System director submits a proposal, the simulation arbiter shall validate and resolve it before applying any resulting state transition.

**AUTH-004:** When a System director proposal violates the loaded rules or refers to an unsupported operation, the proposal shall not change canonical world state.

**AUTH-005:** When requesting a System director decision, the system shall provide a deliberately selected and inspectable world-level context.

**AUTH-006:** The System director shall not modify the rules used by the simulation arbiter while a simulation step is being resolved.

### Game packages

**PACK-001:** The simulation kernel shall load changeable game mechanics from a versioned rule pack.

**PACK-002:** The simulation kernel shall load initial world content from a versioned scenario pack.

**PACK-003:** Before creating or resuming a world, the system shall validate the selected rule and scenario packs and reject invalid packages without changing canonical world state.

**PACK-004:** When a world is created, the system shall record the identities and versions of the rule and scenario packs used to create it.

**PACK-005:** When a selected package is incompatible with an existing world, the system shall require an explicit world reset or migration rather than silently applying the package.

**PACK-006:** The simulation kernel shall expose only explicit, supported operations to rule and scenario packs.
