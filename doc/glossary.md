# Glossary

This glossary defines the canonical domain vocabulary for documentation, requirements, prompts, schemas, code, and tests.

## Usage rules

* Prefer the exact terms below instead of introducing synonyms for the same concept.
* Add or revise a glossary entry when a design change introduces a new domain concept.
* Use lowercase **system** only for the application as a whole. Do not use bare **System** or **director** in technical writing; use **System director** or **System interface**.
* Do not use **action**, **outcome**, and **event** interchangeably.
* When a familiar word has a narrower meaning here, the glossary meaning takes precedence in project artifacts.

## Terms

### Action

The means an actor chooses to pursue an intent. Before validation and resolution, an attempted action is represented as an **action proposal**. The word action alone does not imply success.

### Action proposal

A structured, untrusted request for an actor to perform a supported operation with specific arguments. Player interpreters, NPC decision policies, and the System director may produce proposals. Only the simulation arbiter can validate and resolve them.

### Actor

An entity capable of forming or receiving an intent and submitting an action proposal. The player and NPCs are actors. The System director uses the same proposal boundary but is not a character in the world.

### Actor runtime

The application component that assembles NPC decision context, invokes the configured decision policy, and manages character-internal cognition outputs. It cannot change canonical world state.

### Appraisal

A character's situation-specific interpretation, such as perceived danger, urgency, or opportunity. An appraisal is internal to that character and may be wrong.

### Belief

A mutable claim a character currently accepts with some confidence. A belief may be incomplete, uncertain, false, or inconsistent with another character's belief.

### Belief revision proposal

A structured, untrusted request from NPC sensemaking to add, reinforce, weaken, replace, retract, or express uncertainty about an NPC belief. The actor runtime validates it before changing that NPC's internal state. Belief revision is outside the initial vertical slice.

### Canonical

Authoritative for simulation truth. A statement becomes canonical only through validated package loading or an arbiter-controlled state transition. Generated prose is never canonical by itself.

### Canonical world state

The authoritative current state of the simulated world, including simulation time, locations, entities, conditions, and other rule-governed facts. In conceptual actor-loop diagrams, this is **reality**.

### Character

An actor represented inside the simulated world with a location, perceptions, memories, beliefs, and other character-specific state. The player character and NPCs are characters.

### Connection

A directed edge in the spatial graph defining one possible traversal from a source location to a destination location. Reverse travel requires a separate connection.

### Connection definition

An immutable scenario-package record containing a connection's stable identity, name, endpoints, and base traversal duration. Mutable availability and conditions belong to connection state.

### Context envelope

A role-specific, inspectable input assembled for an LLM call. It identifies the role, simulation and trace context, selected information, allowed operations, output schema, package versions, and provenance references.

### Context budget

An explicit limit and allocation controlling how much information from each source may enter a context envelope. It is configuration, not an implicit prompt-building side effect.

### Decision context

The bounded information available to an NPC decision policy: identity, goals, plans, current perception, selected beliefs, and selected memories. It excludes unavailable canonical facts.

### Decision policy

An interchangeable strategy that maps NPC decision context to a structured action proposal. A policy may be rule-based, scripted, LLM-assisted, or hybrid.

### Derived index

A rebuildable projection used to accelerate retrieval. The Qdrant memory index is derived from durable episodic memory and is not authoritative storage.

### Episodic memory

A durable character-specific record of a perceived or experienced episode, including simulation time and provenance. Episodic memory records what the character experienced, not necessarily what was canonically true.

### Episodic-memory retrieval policy

The bounded selection process that combines high-salience, recent, and semantically relevant episodic memories for one NPC while enforcing ownership, deduplication, provenance, and context budgets. It is outside the initial vertical slice.

### Event

An immutable, durable record that something canonically occurred or was resolved at a simulation time. An event may cause different observations for different characters.

### Feedback

Information through which an actor may learn about consequences. Feedback is filtered through perception and may be incomplete, delayed, misleading, or absent; it is not direct access to an outcome.

### Functional LLM role

An LLM-backed component whose output may request later behavior rather than merely present confirmed information. The player input interpreter, LLM-assisted NPC decision policy, and System director are functional LLM roles and require structured output.

### Game package

A versioned, validated collection of external game definitions loaded by the simulation kernel. Rule packs and scenario packs are game packages.

### Goal

A relatively persistent desired condition that helps shape an actor's intents. Goals do not directly cause state changes.

### Intent

An actor's desired immediate change or purpose. An intent describes what the actor wants; an action proposal describes the attempted means.

### Inspection page

A separate read-only Streamlit development view over simulation-step traces, canonical state, and character perception snapshots. It is not part of the player experience and cannot edit canonical state.

### Location

A structured node in the spatial graph. Connections define possible traversal between locations.

### Location definition

An immutable scenario-package record containing a location's stable identity and name. Perceptible features and mutable conditions are modeled separately rather than embedded in a free-form description.

### Narrator

The presentation component that turns the player's structured perception snapshot into prose. It may style confirmed information but cannot add canonical facts.

### NPC

A non-player character whose behavior is produced by an interchangeable decision policy and constrained by character-specific information.

### Observation

A structured item of information made available to one character by perceptual filtering. It records what that character could perceive, with relevant time, provenance, confidence, and salience.

### Outcome

The structured result of arbiter validation and resolution. An outcome describes success, failure, costs, state transitions, and events; it is distinct from the proposal that requested it and the prose that presents it.

### Perception engine

The deterministic component that applies spatial, sensory, environmental, capability, condition, and visibility constraints to canonical state and events.

### Perceptual filtering

The process performed by the perception engine to determine which observations are available to a particular character.

### Perception snapshot

The structured collection of observations currently available to one character. It is an actor-specific projection, not a copy of canonical world state.

### Player

The human participant who owns their own sensemaking and intent. The application interprets only what the player explicitly communicates and does not invent player motives.

### Primary persistence

The authoritative durable data store. SQLite is the primary persistence technology for the initial version.

### Reality

The canonical world state and canonical events that exist independently of any one character's knowledge. Use **canonical world state** or **canonical events** in technical contracts; reality is the conceptual term used in the actor-loop model.

### Rule

An explicit constraint or resolution instruction used by the simulation arbiter. Rules may be provided by a rule pack but operate only through kernel-supported operations.

### Rule pack

A versioned YAML game package defining changeable mechanics such as actions, abilities, durations, checks, effects, and progression.

### Scenario pack

A versioned YAML game package defining initial world content such as the location graph, characters, objects, initial beliefs, scheduled events, and scenario pressures.

### Scheduled activity

A future environmental event, NPC eligibility point, or System director hook registered for a simulation time with phase and insertion-order metadata.

### Scheduler

The deterministic component that selects and serializes eligible scheduled activities. It does not itself resolve their effects.

### Sensemaking

The character-internal process that interprets current observations using memories, beliefs, knowledge, goals, and limitations. It may update appraisals or beliefs but cannot change canonical world state.

### Simulation arbiter

The sole authority that validates proposals, applies rules, draws canonical randomness, resolves outcomes, and creates canonical state transitions and events.

### Simulation kernel

The stable Python domain core containing the simulation arbiter, time and scheduling mechanisms, perception, supported operations, and other invariants independent of a specific game package.

### Simulation step

One traceable application operation beginning with player input and ending when resulting canonical changes and actor information are committed, after which player presentation can be produced. A failed or clarification-only attempt need not advance simulation time.

### Simulation-step trace

The durable, ordered evidence linking one attempted simulation step's input, interpretation, eligibility, context manifests, proposals, validation, random draws, outcomes, state transitions, observations, and presentation artifacts.

### Simulation time

The world clock advanced by consequential actions or explicit waiting. It is independent of wall-clock time and uses integer seconds as its canonical unit.

### Spatial graph definition

The immutable ordered collection of authored location and directed-connection definitions from which initial spatial world state can be created.

### System director

The hidden LLM-assisted creative component analogous to the creative portion of a game master. It proposes supported world-level developments but cannot change canonical state or communicate mechanical facts directly to the player.

### System interface

The diegetic, player-visible LitRPG interface that presents arbiter-confirmed mechanical facts and optional objectives. It is distinct from the hidden System director.

### System notification

An arbiter-confirmed structured mechanical message presented through the System interface, such as an ability change, status effect, objective offer, or reward.

### Structured output

Generated data required to conform to an explicit strict Pydantic model before application logic can use it. Invalid structured output receives at most one repair attempt and is never partially accepted or recovered from prose.

### Turn coordinator

The application service that coordinates one simulation step across interpretation, arbitration, scheduling, actor decisions, perception, persistence, and presentation.

### Vertical slice

A minimal playable scenario that exercises the complete architecture end to end. It is not a collection of isolated component demonstrations.

### World

The persistent simulation instance, including its canonical state, history, clock, random state, and exact rule and scenario package versions.
