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

A structured, untrusted request to perform one supported operation with operation-specific arguments. The proposal payload is distinct from its trusted **proposal submission**, which supplies identity and provenance. Player interpreters, NPC decision policies, and the System director may produce proposal payloads. Only the simulation arbiter can validate and resolve submitted proposals.

### Action proposal submission

A trusted application-created envelope pairing an untrusted action proposal payload with its proposal identity, source role and identity, intended actor when applicable, simulation-step context, and trace provenance. Generated output cannot supply or override this metadata.

### Actor

An entity capable of forming or receiving an intent and submitting an action proposal. The player and NPCs are actors. The System director uses the same proposal boundary but is not a character in the world.

### Actor runtime

The application component that assembles NPC decision context, invokes the configured decision policy, and manages character-internal cognition outputs. It cannot change canonical world state.

### Appraisal

A character's situation-specific interpretation, such as perceived danger, urgency, or opportunity. An appraisal is internal to that character and may be wrong.

### Archetype

A reusable rule-pack definition that supplies mechanical meaning or defaults to scenario instances. Object and character definitions reference archetypes by stable identifier rather than embedding arbitrary property dictionaries.

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

### Character archetype definition

An immutable rule-pack catalog record identifying reusable character mechanics or defaults. Content schema version 1 contains only its stable identifier and name; later schemas define actual mechanics.

### Character definition

An immutable scenario-package player or NPC record containing stable identity, archetype, and initial placement information. NPC definitions also contain motivation context and a decision-policy reference; mutable character state is separate.

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

### Decision-policy definition

An immutable rule-pack declaration of a policy's stable identity, name, and rule, LLM, or hybrid type. Executable behavior belongs to an application-owned implementation registry.

### Decision-policy reference

A structured NPC package reference naming a rule, LLM, or hybrid decision policy by stable identifier. The reference contains no executable policy logic.

### Derived index

A rebuildable projection used to accelerate retrieval. The Qdrant memory index is derived from durable episodic memory and is not authoritative storage.

### Episodic memory

A durable character-specific record of a perceived or experienced episode, including simulation time and provenance. Episodic memory records what the character experienced, not necessarily what was canonically true.

### Episodic-memory retrieval policy

The bounded selection process that combines high-salience, recent, and semantically relevant episodic memories for one NPC while enforcing ownership, deduplication, provenance, and context budgets. It is outside the initial vertical slice.

### Entity

An addressable spatial thing in the world. Objects, player characters, and NPC characters are concrete entity variants.

### Entity definition

The discriminated immutable scenario-package union of object, player-character, and NPC-character definitions.

### Event

An immutable, durable, typed record that something canonically occurred at a simulation time. Each event has stable identity, an event-type discriminator, a causation link to its originating outcome, and an operation-specific factual payload. Events do not contain narrative prose or decide who perceived them; one event may produce different observations for different characters. Canonical events provide causal history but are not the sole persistence representation of canonical world state.

### Feedback

Information through which an actor may learn about consequences. Feedback is filtered through perception and may be incomplete, delayed, misleading, or absent; it is not direct access to an outcome.

### Functional LLM role

An LLM-backed component whose output may request later behavior rather than merely present confirmed information. The player input interpreter, LLM-assisted NPC decision policy, and System director are functional LLM roles and require structured output.

### Game package

A versioned, validated collection of external game definitions loaded by the simulation kernel. Rule packs and scenario packs are game packages.

### Game-package validation issue

One strict immutable semantic defect with a stable typed code, authored-field path, and human-readable message. Independent issues are returned in deterministic order for authoring and tooling.

### Goal

A relatively persistent desired condition that helps shape an actor's intents. Goals do not directly cause state changes.

### Goal definition

An immutable NPC package record with a stable identifier and natural-language description. Authored goal order expresses initial priority.

### Intent

An actor's desired immediate change or purpose. An intent describes what the actor wants; an action proposal describes the attempted means.

### Inspection page

A separate read-only Streamlit development view over simulation-step traces, canonical state, and character perception snapshots. It is not part of the player experience and cannot edit canonical state.

### Loaded game package

A strict immutable pair of one validated concrete package manifest and its matching typed entrypoint definition. A loaded package is structurally trusted but has not necessarily passed relational, graph, dependency, or playability validation.

### Location

A structured node in the spatial graph. Connections define possible traversal between locations.

### Location definition

An immutable scenario-package record containing a location's stable identity and name. Perceptible features and mutable conditions are modeled separately rather than embedded in a free-form description.

### Narrator

The presentation component that turns the player's structured perception snapshot into prose. It may style confirmed information but cannot add canonical facts.

### NPC

A non-player character whose behavior is produced by an interchangeable decision policy and constrained by character-specific information.

### Object archetype definition

An immutable rule-pack catalog record identifying reusable object mechanics. Content schema version 1 contains only its stable identifier and name; later schemas define actual mechanics.

### Object definition

An immutable scenario-package entity record that references a rule-pack object archetype and has exactly one initial location or possessing character.

### Object placement

The single authored initial placement of an object: either directly at one location or possessed by one character. A possessed object does not also store a duplicate effective location.

### Observation

A structured item of information made available to one character by perceptual filtering. It records what that character could perceive, with relevant time, provenance, confidence, and salience.

### Outcome

The structured result of arbiter validation and resolution. A **rejected** outcome means the proposal could not be attempted and has no canonical effects or time cost. A **failed** outcome means a valid attempt did not achieve its goal and may still have rule-defined costs or events. A **succeeded** outcome means the valid attempt achieved its defined result. An outcome retains its originating proposal identity and describes proposed costs, state transitions, and events; it is distinct from both the proposal and presentation prose. Only the simulation arbiter may commit its effects.

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

### Rule-pack definition

The strict immutable typed root loaded from a rule pack's entrypoint. Content schema version 1 contains ordered object-archetype, character-archetype, and decision-policy reference catalogs.

### Scenario pack

A versioned YAML game package defining initial world content such as the location graph, characters, objects, initial beliefs, scheduled events, and scenario pressures.

### Scenario-pack definition

The strict immutable typed root loaded from a scenario pack's entrypoint. Content schema version 1 explicitly composes one spatial-graph definition and one entity-collection definition; later schemas may add other accepted scenario concepts.

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

### Validated game packages

One immutable loaded rule-and-scenario pair that has passed the defined dependency, namespace-uniqueness, reference, player-count, and directed-topology checks. It is not proof of policy implementation availability, supported mechanics, persistent-world compatibility, or general playability.

### Validated world state

An immutable pairing of one **validated game packages** value with one structurally valid runtime snapshot after relational world-state validation proves complete unique overlays and valid current references. It does not by itself prove policy implementation availability, supported mechanics, persistence compatibility, or scenario playability.

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
