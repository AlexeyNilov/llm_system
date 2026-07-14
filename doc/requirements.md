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

**NPC-008:** The initial actor-turn coordinator shall construct one bounded `NpcDecisionContext` for an explicitly requested authored NPC from that NPC's package identity summary, goals, current plan, and current actor-specific perception. It shall not pass canonical world state, another actor's private information, memories, beliefs, or trusted submission metadata to the decision policy.

**NPC-009:** The first executable actor turn shall support only the authored Greybridge caretaker's matching rule policy. A missing, non-NPC, mismatched, or otherwise unsupported NPC/policy request shall fail without invoking a policy, creating trusted action metadata, or changing persistence.

**NPC-010:** The actor-turn coordinator shall obtain the policy proposal outside a SQLite write unit of work, then recheck the exact world identity and revision before creating trusted action metadata or writing. If the world changed, it shall return a typed stale-decision result and leave world, event, and trace history unchanged.

**NPC-011:** For an unchanged world revision, the actor-turn coordinator shall application-assign proposal, simulation-step, decision-context, outcome, and event identities; create the matching `NpcPolicyActionSource`; and invoke the existing actor-action coordinator path in one unit of work. It shall return completion only after the action step commits.

**NPC-012:** The initial actor-turn coordinator shall not select, claim, consume, add, reschedule, or persist scheduled activities; invoke an LLM; retrieve or revise memories or beliefs; expose HTTP/UI behavior; or narrate outcomes.

**NPC-013:** The initial memory-free courier policy shall accept only one matching `NpcDecisionContext` and an injected `FunctionalModelGateway`. Its model context shall contain only the courier identity summary, goals, current plan, and exact courier perception; it shall not include canonical world state, other actors' private information, memory, prior conversation, trusted metadata, outcomes, or narration.

**NPC-014:** The courier policy shall request one strict proposal from the supported Observe, Move, Speak, Take, Use, or Wait proposal union. A valid accepted output is returned with its ordered functional-generation evidence; any failed generation maps to an application-owned 60-second Wait proposal without accepting generated prose or provider detail.

**NPC-015:** The courier policy shall be pure: it shall not assign runtime identities, create submissions, resolve actions, advance time, mutate or persist state, schedule work, or expose HTTP/UI behavior. Its result shall remain sufficient for a later application coordinator to retain the functional-generation evidence alongside a trusted action step.

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

**PACK-011:** The package loading and validation pipeline shall reject executable YAML constructs, invalid types, unresolved references, and unsupported operations before creating or resuming a world.

**PACK-012:** Each rule and scenario package manifest shall declare `schema_version`, `package_id`, `package_version`, `package_type`, `title`, and one YAML `entrypoint` using the strict initial manifest schema.

**PACK-013:** The initial manifest schema shall accept only schema version `1`, lowercase kebab-case package identifiers, stable `MAJOR.MINOR.PATCH` package versions, and package types `rule` or `scenario`.

**PACK-014:** Each scenario package manifest shall identify exactly one required rule pack by exact package identifier and package version, while a rule package manifest shall not declare a scenario or rule dependency.

**PACK-015:** The system shall discover authored game packages under `game_packages/rules/<package-id>/<package-version>/` or `game_packages/scenarios/<package-id>/<package-version>/`, and the package directory kind, identifier, and version shall match its manifest.

**PACK-016:** Before returning a loaded game package, the package loader shall confirm that its entrypoint is a relative YAML file contained within the package directory and that the resolved entrypoint exists as a regular file.

**PACK-017:** When a package manifest or entrypoint is missing, malformed, invalid, inconsistent with its directory, or unsafe, the package loader shall reject the package through one application-owned game-package loading error without returning a partial manifest, raw package data, or validation-library exception.

**PACK-018:** The package loader shall use the validated manifest package type as the sole selector for parsing the entrypoint into `RulePackDefinition` or `ScenarioPackDefinition`, without inferring package type from content keys.

**PACK-019:** A successfully loaded game package shall be a strict immutable typed pair of its concrete rule or scenario manifest and matching content definition; loading one scenario package shall preserve but not resolve its exact required-rule-pack reference.

### Game-package semantic validation

**PACK-020:** Given one loaded rule package and one loaded scenario package, semantic validation shall either return one strict immutable `ValidatedGamePackages` pair or raise one `GamePackageValidationError` without mutating either input.

**PACK-021:** A game-package validation error shall contain an immutable deterministic ordered collection of strict structured issues, each with a typed stable code, an authored-field path, and a human-readable message; validation shall aggregate independent issues rather than fail on the first defect.

**PACK-022:** Identifier uniqueness shall be enforced within semantic namespaces: locations, connections, all entity variants together, boolean world facts, object-use bindings, each rule-pack catalog separately, and NPC goals within their owning NPC. Reusing one identifier across distinct typed namespaces shall remain valid.

**PACK-023:** Validation shall require the scenario's exact rule-package pin to match the supplied rule manifest and shall resolve connection endpoints, initial locations, object placements, archetypes, and NPC policy references against their typed target namespaces. Possession targets shall be characters, NPC policy types shall match their resolved definitions, and exactly one player shall exist.

**PACK-024:** Graph validation shall reject self-loop connections and shall require every authored location to be reachable from the one player's initial location by following directed connections. It shall not require reverse reachability, and parallel directed connections with distinct IDs shall remain valid.

**PACK-025:** Validation shall report independent root defects while skipping dependent conclusions whose premises are invalid. A mismatched rule-package pin shall suppress scenario-to-rule reference checks, and invalid or ambiguous graph prerequisites shall suppress reachability rather than produce cascading issues.

**PACK-026:** `ValidatedGamePackages` shall prove only the dependency, uniqueness, reference, player-count, and topology checks defined for this boundary. It shall not by itself prove policy implementation availability, supported operations, compatibility with persistent state, playability, or readiness for world creation.

**PACK-027:** Object-use mechanic definitions shall resolve their object-archetype references within the paired rule package; scenario object-use bindings shall resolve their mechanic, concrete object, target location, and boolean-world-fact references in their typed namespaces.

**PACK-028:** A scenario object-use binding's concrete object shall use the object archetype required by its resolved mechanic, and semantic validation shall reject more than one binding for the same concrete object and target location so runtime resolution remains deterministic.

### Rule-pack content definitions

**RULE-001:** A rule-pack entrypoint shall validate into a strict immutable root definition with content `schema_version: 1` and ordered object-archetype, character-archetype, decision-policy, and object-use-mechanic catalogs.

**RULE-002:** Every object and character archetype definition shall contain exactly a stable lowercase kebab-case identifier and non-blank human-readable name in content schema version 1.

**RULE-003:** Every decision-policy definition shall contain exactly a stable identifier, non-blank name, and policy type `rule`, `llm`, or `hybrid`.

**RULE-004:** Rule-pack content definitions shall preserve authored catalog order while exposing immutable collections, and each catalog may be empty at the structural-model boundary; the object-use-mechanic catalog shall default to empty for backward-compatible schema-version-1 packages.

**RULE-005:** Before rule-pack content is accepted for world creation, semantic package validation shall reject duplicate identifiers within each catalog. Before an NPC decision policy is executed, the application shall require the referenced policy to have a compatible application-owned implementation; world creation shall not require future actor-policy implementations merely to materialize package-authored initial state.

**RULE-006:** Rule-pack content schema version 1 shall not include executable code, generic property dictionaries, arbitrary tags, abilities, skills, open-ended effects, policy settings, or implicit behavioral defaults.

**RULE-007:** The initial `ObjectUseMechanicDefinition` shall contain a stable identifier, non-blank name, required object-archetype identifier, `target_type="location"`, strictly positive integer duration seconds, and the closed effect discriminator `effect_type="set_boolean_world_fact"`.

**RULE-008:** Object-use mechanics shall describe reusable typed resolution constraints but shall not reference scenario-specific object, location, or world-fact identifiers or contain callbacks, expressions, arbitrary parameters, randomness, consumption, progression, or presentation data.

### Scenario mechanic bindings

**SCHEMA-001:** Content schema version 1 shall support an ordered immutable boolean-world-fact catalog and object-use-binding catalog on `ScenarioPackDefinition`, both defaulting to empty for backward-compatible packages.

**SCHEMA-002:** A `BooleanWorldFactDefinition` shall contain exactly a stable identifier, non-blank name, and strict boolean initial value.

**SCHEMA-003:** An `ObjectUseBindingDefinition` shall contain exactly a stable identifier, rule-pack mechanic identifier, concrete object identifier, target location identifier, boolean-world-fact identifier, and strict boolean target value.

**SCHEMA-004:** Scenario bindings shall instantiate accepted rule mechanics through typed references and shall not contain executable code, generic effect payloads, conditions, formulas, random checks, consumption behavior, or narrative text.

### Player experience

**PLAY-001:** The system shall allow the player to express attempted actions in free-form text.

**PLAY-002:** When the player expresses an attempted action, the system shall interpret it as a structured intention supported by the loaded rule pack or report that it cannot be performed.

**PLAY-003:** The system shall not require the player to follow a predetermined sequence of scenario events.

**PLAY-004:** When the System interface presents an objective or opportunity proposed by the System director, the player shall remain free to pursue, ignore, or oppose it subject to world consequences.

**PLAY-005:** The system shall resolve player intentions using the loaded mechanics and canonical world state before narrating their outcomes.

**PLAY-006:** When a scenario-level conflict succeeds or fails, the world shall remain capable of continuing unless a rule explicitly ends the simulation.

**PLAY-007:** The initial vertical slice shall include at least one player-visible progression event governed by the loaded rule pack.

**PLAY-008:** The initial player interpreter shall accept one non-blank free-form player input together with only the player's current `PerceptionSnapshot`; it shall not receive canonical world state, another actor's private information, trusted submission metadata, or prior conversation history.

**PLAY-009:** Functional player interpretation output shall be one strict immutable record that is either `interpreted`, containing an optional non-blank explicit private thought and at most one supported actor-action proposal with at least one present, or `clarification`, containing only one non-blank clarification message.

**PLAY-010:** Initial interpreted proposals shall use the existing Observe, Move, Speak, Take, Use, or Wait proposal contracts. Speech shall be represented by `SpeakActionProposal`; Help shall remain unavailable to free-form interpretation until its resolver exists.

**PLAY-011:** An accepted model-produced clarification shall be returned without an action proposal. Any failed model-gateway result shall map to one fixed application-owned clarification without accepting invalid output or exposing provider failure detail.

**PLAY-012:** The player-interpreter service shall preserve the exact player input, perception snapshot, functional-generation evidence, and final interpreted-or-clarification result without creating trusted identities, submitting or resolving an action, advancing time, mutating state, persisting data, or narrating an outcome.

**PLAY-013:** The later player-turn coordinator shall retain one durable player-input trace for every completed free-form player input. A trace shall preserve the exact interpreter result, including functional-generation evidence, and classify the completion as thought-only, clarification, or action-linked; thought-only and clarification completions shall not advance canonical world revision.

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

**SPACE-008:** Scenario packages shall represent stable authored topology using immutable location, connection, and spatial-graph definitions that remain separate from mutable runtime location and connection state.

**SPACE-009:** Each location definition shall contain a stable lowercase kebab-case identifier and a non-blank human-readable name, without embedding free-form perceptual facts or mutable state.

**SPACE-010:** Each connection definition shall represent one directed edge with a stable identifier, non-blank name, source location identifier, destination location identifier, and base traversal duration.

**SPACE-011:** Simulation durations shall use non-negative integer seconds as the canonical unit, and each traversable connection's base traversal duration shall be strictly positive.

**SPACE-012:** A spatial-graph definition shall preserve authored location and connection order while exposing immutable collections to downstream code.

**SPACE-013:** The initial spatial-definition schema shall not include coordinates, implicit bidirectional expansion, connection requirements, availability, damage, visibility, or other mutable runtime state.

**SPACE-014:** Before a spatial graph becomes canonical world state, graph validation shall reject duplicate location or connection identifiers, missing connection endpoints, and self-loop connections; parallel directed connections with distinct identifiers may remain valid.

### Entity and character definitions

**ENTITY-001:** Scenario packages shall represent each addressable spatial thing as an immutable entity definition discriminated as an object, player character, or NPC character.

**ENTITY-002:** Every entity definition shall have a stable lowercase kebab-case identifier and non-blank name, while concrete entity variants shall forbid fields owned by another variant.

**ENTITY-003:** Every object definition shall reference one rule-pack object archetype and declare exactly one initial placement: directly at a location or possessed by a character.

**ENTITY-004:** Every player and NPC character definition shall reference one rule-pack character archetype and declare one initial location.

**ENTITY-005:** A player character definition shall not contain NPC identity, motivation, plan, or decision-policy fields.

**ENTITY-006:** Every NPC character definition shall contain a non-blank identity summary, at least one ordered immutable goal, an optional non-blank initial plan, and a decision-policy reference whose type is `rule`, `llm`, or `hybrid`.

**ENTITY-007:** An entity-collection definition shall preserve authored entity order while exposing an immutable collection to downstream code.

**ENTITY-008:** Before entity definitions become canonical world state, validation shall reject duplicate entity identifiers, duplicate goal identifiers within one NPC, a player count other than one, missing or non-character possession targets, missing initial locations, unresolved archetypes, and unresolved or incompatible NPC policy references. Reference validity shall not depend on authored record order.

**ENTITY-009:** The initial entity-definition schema shall not include nested containers, unplaced objects, quantities, mutable inventory or condition state, free-form perceptual descriptions, executable policy logic, or generic property dictionaries.

### Canonical runtime state

**STATE-001:** The simulation kernel shall represent mutable canonical world facts in explicit runtime-state contracts separate from immutable rule-pack and scenario-pack definitions.

**STATE-002:** Before resolving the initial supported operations, canonical runtime state shall provide the current simulation time, character locations, object placement or possession, and connection availability required for deterministic validation and resolution.

**STATE-003:** Runtime-state contracts shall introduce new rule-governed facts only after their semantics are accepted; the first extension is an identifier-linked strict boolean world fact rather than a Greybridge-specific field or arbitrary fact dictionary.

**STATE-004:** Canonical runtime state shall be represented as an immutable validated snapshot, and simulation resolution shall not mutate its input snapshot in place.

**STATE-005:** When the simulation arbiter commits a non-rejected outcome, it shall apply all typed state changes to produce one replacement snapshot; a rejected outcome shall return the original snapshot unchanged.

**STATE-006:** Persistence shall later commit the replacement canonical snapshot, canonical events, and simulation-step trace atomically.

**STATE-007:** Canonical runtime state shall contain only changing facts linked by stable identifiers to immutable validated package definitions and shall not duplicate authored names, topology, traversal durations, archetypes, goals, or other definition-owned data.

**STATE-008:** Before resolving an operation, the simulation kernel shall receive both the validated game-package definitions and the canonical runtime-state snapshot required to interpret its identifier-linked overlays.

**STATE-009:** World persistence identity and recorded package-version ownership shall belong to the later persistent world-record boundary rather than the pure M3 runtime-state snapshot.

**STATE-010:** A world-ready runtime snapshot shall contain exactly one character-state record for every authored character, one object-state record for every authored object, one connection-state record for every authored connection, and one boolean-world-fact state for every authored boolean world fact.

**STATE-011:** World-readiness validation shall reject duplicate runtime identifiers, missing runtime records, runtime records without matching definitions, and invalid runtime references.

**STATE-012:** Structural runtime-state model construction shall remain separate from world-readiness validation and shall not require package lookup.

**STATE-013:** Resolution shall not infer current availability, location, or possession from a missing runtime-state record or fall back to an entity's initial package placement after world creation.

**STATE-014:** `WorldState` shall expose character, object, connection, and boolean-world-fact state as immutable ordered tuples; initial world creation shall preserve authored order, but semantic validity and resolution shall not depend on runtime record order.

**STATE-015:** Public runtime-state contracts shall not expose mutable dictionaries as canonical collections; consumers may derive temporary identifier indexes without making them part of canonical state.

**STATE-016:** `CharacterState` shall contain exactly an authored character identifier and its current location identifier.

**STATE-017:** `ObjectState` shall contain exactly an authored object identifier and one discriminated current placement that is either a location or one possessing character, never both or neither.

**STATE-018:** `ConnectionState` shall contain exactly an authored connection identifier and one explicit strict boolean availability value.

**STATE-045:** `BooleanWorldFactState` shall contain exactly an authored boolean-world-fact identifier and one explicit strict boolean current value.

**STATE-019:** `WorldState` shall contain a non-negative integer `simulation_time_seconds` and the ordered immutable character, object, connection, and boolean-world-fact state tuples; the fact tuple shall default to empty for worlds whose scenario defines no facts.

**STATE-020:** Runtime-state contracts shall not represent unplaced, destroyed, consumed, hidden, quantified, conditioned, or nested objects, and shall not represent character or connection conditions beyond the accepted minimal fields; boolean world facts shall not become an arbitrary value or metadata store.

**STATE-021:** Successful relational world-state validation shall return an immutable `ValidatedWorldState` pairing exactly one `ValidatedGamePackages` value with exactly one `WorldState` snapshot.

**STATE-022:** `ValidatedWorldState` shall guarantee complete and unique character, object, connection, and boolean-world-fact overlays; matching runtime and authored definition identities; and valid current location and character-possessor references.

**STATE-023:** The simulation arbiter shall accept a `ValidatedWorldState` rather than an unvalidated runtime snapshot and package pair.

**STATE-024:** `ValidatedWorldState` shall not imply decision-policy implementation availability, supported rule mechanics, persistence compatibility, or scenario playability.

**STATE-025:** Failed relational world-state validation shall raise one application-owned error containing deterministic structured issues and shall not return a partial validated wrapper.

**STATE-026:** World-state validation shall use separate `WorldStateValidationIssueCode`, `WorldStateValidationIssue`, and `WorldStateValidationError` contracts rather than package-authoring validation issue types.

**STATE-027:** Initial world-state validation issue codes shall be exactly `duplicate-state-id`, `missing-state`, `unexpected-state`, and `unknown-runtime-reference`.

**STATE-028:** Every world-state validation issue shall contain its stable code, deterministic runtime-state path, and non-blank human-readable message.

**STATE-029:** World-state validation shall aggregate independent root defects while suppressing dependent reference conclusions when a runtime record cannot be identified uniquely and authoritatively.

**STATE-030:** World-state validation shall process character, object, connection, and boolean-world-fact overlay namespaces in that order, then validate current runtime references from uniquely identified expected records.

**STATE-031:** Within an overlay namespace, duplicate issues shall follow first-duplicate encounter order, missing-state issues shall follow authored definition order, and unexpected-state issues shall follow runtime tuple order.

**STATE-032:** Runtime-reference issues shall follow character then object runtime tuple order and shall be checked only for records whose own identifiers are expected and unique.

**STATE-033:** A current character or object location shall reference an authored location, and a current object possessor shall reference an authored character.

**STATE-034:** A valid authored possessor whose character-state overlay is missing shall produce the applicable `missing-state` issue and shall not also produce `unknown-runtime-reference` for the possession reference.

**STATE-035:** World-state validation issue paths shall describe fields in the supplied runtime snapshot using collection names, zero-based tuple indexes, and field names, such as `characters[0].location_id` or `objects[1].placement.character_id`.

**STATE-036:** A missing-state issue shall use the affected runtime collection path because no runtime tuple position exists, and its message shall identify the missing authored identifier.

**STATE-037:** The public validation operation shall have the contract `validate_world_state(packages: ValidatedGamePackages, state: WorldState) -> ValidatedWorldState`.

**STATE-038:** A resolved change to canonical runtime state shall be represented as one member of a closed discriminated union of typed state-change contracts.

**STATE-039:** State-change variants shall be character location change, object placement change, connection availability change, boolean-world-fact change, and simulation-time change.

**STATE-040:** Every state change shall contain the affected runtime identity together with explicit before and after values, and structural validation shall reject equal before and after values.

**STATE-041:** A simulation-time change shall contain non-negative integer before and after seconds and shall require the after value to be strictly greater than the before value.

**STATE-042:** State changes shall describe exact immutable-snapshot deltas and shall remain distinct from canonical events, which describe facts that occurred.

**STATE-043:** `BooleanWorldFactChanged` shall identify one authored fact, carry distinct strict boolean `from_value` and `to_value`, and use discriminator `boolean_world_fact`.

**STATE-044:** Outcome commitment shall validate a boolean-world-fact change against the complete runtime fact overlay, report unknown targets and before-value mismatches through existing commitment issue codes, and replace only the matching fact at its existing tuple position.

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

#### Action proposals and outcomes

**ACTION-001:** The simulation kernel shall represent action proposals as a closed discriminated union of strict operation-specific contracts rather than as an operation name paired with an arbitrary argument mapping.

**ACTION-002:** Each supported operation shall define its own typed argument contract, and the simulation arbiter shall reject proposals that do not conform to one supported proposal variant.

**ACTION-003:** A trusted actor-action proposal submission shall identify the actor intended to perform the operation.

**ACTION-004:** World-action proposals shall use a separate typed proposal family and shall not represent the System director as a character or actor.

**ACTION-005:** Rule packs may configure kernel-supported operations and their resolution rules but shall not introduce a new operation without a corresponding kernel contract and resolver.

**ACTION-006:** Every resolved action proposal shall produce exactly one structured outcome with a status of `rejected`, `failed`, or `succeeded` and a stable machine-readable reason code.

**ACTION-007:** A rejected outcome shall represent a proposal that could not be attempted and shall have no canonical state transition, canonical event, cost, or simulation-time advancement.

**ACTION-008:** A failed outcome shall represent a valid attempted action that did not achieve its defined goal and may include rule-defined costs, simulation-time advancement, state transitions, or canonical events.

**ACTION-009:** A succeeded outcome shall represent a valid attempted action that achieved its defined result and may include rule-defined costs, simulation-time advancement, state transitions, or canonical events.

**ACTION-010:** Every outcome shall retain the identity of its originating action proposal, and only the simulation arbiter shall be authorized to commit the effects described by that outcome.

**ACTION-024:** Outcomes shall form a closed discriminated union of `RejectedOutcome`, `FailedOutcome`, and `SucceededOutcome` rather than one permissive record with optional effect fields.

**ACTION-025:** Every outcome variant shall contain application-assigned outcome identity, originating proposal identity, and a stable machine-readable reason code.

**ACTION-026:** `RejectedOutcome` shall omit state-change and canonical-event fields entirely, making rejected effects structurally unrepresentable.

**ACTION-027:** `FailedOutcome` and `SucceededOutcome` shall contain immutable ordered tuples of typed state changes and canonical events; either tuple may be empty.

**ACTION-028:** Outcome and state-change records shall be retained in the simulation-step trace, while canonical events shall additionally be retained as durable canonical history.

**ACTION-029:** Every outcome shall contain non-negative integer `resolved_at_seconds` representing the atomic resolution completion time.

**ACTION-030:** A rejected outcome shall use the input snapshot's current simulation time, and a failed or succeeded outcome shall use the completion time after any action-duration advancement.

**ACTION-031:** Every canonical event contained by an outcome shall use that outcome's identity as its cause and the same completion time as its occurrence time.

**ACTION-032:** When an outcome contains a simulation-time change, that change's after value shall equal the outcome completion time; when it contains no simulation-time change, the completion time shall equal the input snapshot time.

**ACTION-033:** The initial kernel shall model one atomic completion time per resolved outcome and shall represent elapsed-time-triggered scheduled activities as separate later resolutions rather than intermediate events inside the triggering outcome.

**ACTION-034:** Failed and succeeded outcome construction shall require every nested event's outcome identity and occurrence time to equal the containing outcome identity and completion time.

**ACTION-035:** Canonical event identities shall be unique within one outcome.

**ACTION-036:** One outcome shall contain at most one state change for each affected character location, object placement, or connection availability and at most one simulation-time change; sequential changes to one field shall be collapsed into one before-and-after delta.

**ACTION-037:** Outcome model construction shall not validate state-dependent facts, including whether before values match an input snapshot, references are actionable, event facts agree with operation resolution, or a proposal source is authorized.

**ACTION-038:** The simulation arbiter shall validate state-dependent outcome consistency before committing any replacement snapshot or canonical event.

**ACTION-039:** `OutcomeReasonCode` shall be a strict non-empty lowercase kebab-case value rather than a closed central enum or unconstrained string.

**ACTION-040:** Deterministic kernel or resolver code shall own and document the meanings of outcome reason codes; LLM output and package content shall not create canonical reason semantics merely by supplying a formatted value.

**ACTION-041:** Failed and succeeded outcomes shall require callers to provide both `state_changes` and `events` explicitly, even when either immutable tuple is empty; neither field shall have a default value.

**ACTION-042:** A missing valid-attempt effect field shall be structurally invalid and shall not be interpreted as an implicit empty tuple.

#### Arbiter commitment

**ARBITER-001:** The deterministic arbiter work shall separate outcome commitment, submission authorization and dispatch, and operation-specific resolution into distinct implementation boundaries.

**ARBITER-002:** The outcome commitment core shall validate and atomically apply already resolved typed outcomes without inventing operation semantics or invoking an LLM.

**ARBITER-003:** An operation resolver shall not be implemented until its actionability, duration, failure, state-change, and event semantics are accepted and testable.

**ARBITER-004:** The initial kernel shall not introduce temporary defaults or generic rule dictionaries to approximate underspecified Observe, Speak, Take, Use, or Help mechanics.

**ARBITER-005:** The public commitment operation shall have the contract `commit_outcome(world: ValidatedWorldState, outcome: Outcome) -> OutcomeCommitResult`.

**ARBITER-006:** `OutcomeCommitResult` shall be a strict immutable record containing exactly the committed outcome and resulting validated world state without duplicating canonical events outside the outcome.

**ARBITER-007:** Committing a rejected outcome shall retain it as simulation-step trace evidence and return the exact same `ValidatedWorldState` object without canonical state or event effects.

**ARBITER-008:** Committing a failed or succeeded outcome shall validate all state-dependent delta invariants before applying the complete change set atomically to a replacement snapshot and revalidating that snapshot against the same packages.

**ARBITER-009:** The commitment core shall not validate proposal/submission identity agreement, source authorization, actionability, or operation-specific agreement among a proposal, state changes, and events.

**ARBITER-010:** Outcome commitment failure shall use separate strict immutable `OutcomeCommitIssueCode`, `OutcomeCommitIssue`, and `OutcomeCommitError` contracts.

**ARBITER-011:** Initial outcome-commit issue codes shall be exactly `resolution-time-mismatch`, `unknown-change-target`, `before-value-mismatch`, and `unknown-after-reference`.

**ARBITER-012:** Every outcome-commit issue shall contain its stable code, deterministic path into the supplied outcome, and non-blank human-readable message.

**ARBITER-013:** Outcome commitment shall aggregate independent state-dependent issues and shall apply no state change or canonical event when any issue exists.

**ARBITER-014:** If accepted commitment checks produce a replacement snapshot that fails relational world-state validation, the implementation shall treat that result as a kernel invariant defect rather than flattening it into an ordinary outcome-commit issue.

**ARBITER-015:** Commitment issue ordering shall place any outcome-level time mismatch first, followed by state-dependent checks in state-change tuple order.

**ARBITER-016:** For each non-time state change, commitment shall validate target existence first; an unknown target shall produce only `unknown-change-target` for that change and suppress its before-value and after-reference checks.

**ARBITER-017:** For a known non-time target, `before-value-mismatch` shall precede an independently applicable `unknown-after-reference` issue.

**ARBITER-018:** For `SimulationTimeChanged`, a from value unequal to current world time shall produce `before-value-mismatch`, and a to value unequal to outcome completion time shall produce `resolution-time-mismatch`, at paths for that change's fields in tuple position.

**ARBITER-019:** A rejected outcome or valid-attempt outcome without a simulation-time change shall require its completion time to equal current world time and shall report mismatch at `outcome.resolved_at_seconds`.

**ARBITER-020:** A successfully committed outcome with no state changes shall preserve the exact input `ValidatedWorldState` object even when it contains canonical events.

**ARBITER-021:** When state changes exist, commitment shall replace affected runtime records at their existing tuple positions, preserve unaffected record identities and collection order, and return a new `WorldState` and `ValidatedWorldState` paired with the exact same validated packages.

#### Actor-action authorization

**AUTHZ-001:** Actor-action submission authorization shall be a separate boundary from operation dispatch and resolution.

**AUTHZ-002:** The public authorization operation shall have the contract `authorize_actor_action(world: ValidatedWorldState, submission: ActorActionSubmission) -> AuthorizedActorAction`.

**AUTHZ-003:** `AuthorizedActorAction` shall be a strict immutable record preserving exactly the supplied validated world and actor-action submission objects.

**AUTHZ-004:** The intended actor shall resolve to an authored character in the validated world.

**AUTHZ-005:** A player-interpreter source shall be authorized only for the one authored player character.

**AUTHZ-006:** An NPC-policy source shall require its NPC identity to equal the intended actor identity, the intended actor to be an NPC, and its policy identity to equal that NPC's configured decision-policy identity.

**AUTHZ-007:** The interpreter identity shall remain trusted application-supplied provenance, and this boundary shall not introduce an interpreter registry or allowlist.

**AUTHZ-008:** Submission authorization shall not resolve proposal targets, validate current actionability, dispatch operations, invoke resolvers, or generate outcomes.

**AUTHZ-009:** Authorization failure shall use separate strict immutable `ActorActionAuthorizationIssueCode`, `ActorActionAuthorizationIssue`, and `ActorActionAuthorizationError` contracts with a non-empty immutable issue tuple.

**AUTHZ-010:** Initial authorization issue codes shall be exactly `unknown-actor`, `source-actor-mismatch`, `actor-type-mismatch`, and `policy-mismatch`.

**AUTHZ-011:** Authorization shall first resolve `submission.actor_id`; an unknown actor shall produce only `unknown-actor` at `submission.actor_id`.

**AUTHZ-012:** For a player-interpreter source and known non-player actor, authorization shall produce only `actor-type-mismatch` at `submission.actor_id`.

**AUTHZ-013:** For an NPC-policy source, unequal source NPC and intended actor identities shall produce only `source-actor-mismatch` at `submission.source.npc_id` and suppress actor-type and policy checks.

**AUTHZ-014:** When an NPC-policy source identity matches a known intended actor that is not an NPC, authorization shall produce only `actor-type-mismatch` at `submission.actor_id` and suppress the policy check.

**AUTHZ-015:** When an NPC-policy source matches an authored NPC but its policy identity differs from the NPC definition, authorization shall produce `policy-mismatch` at `submission.source.policy_id`.

#### Wait resolution

**WAIT-001:** The first operation resolver shall resolve an authorized Wait proposal without perception, package-rule lookup, randomness, or an LLM.

**WAIT-002:** The public resolver shall have the contract `resolve_wait(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> SucceededOutcome` and shall not generate runtime identities internally.

**WAIT-003:** Wait resolution shall advance simulation time by exactly the proposal's strictly positive requested duration and shall use the resulting time as outcome completion and event occurrence time.

**WAIT-004:** A resolved Wait shall produce reason code `wait-completed`, exactly one `SimulationTimeChanged`, and exactly one `ActorWaitedEvent` identifying the intended actor and requested duration.

**WAIT-005:** Wait resolution shall preserve the authorized submission's proposal identity and shall use the caller-supplied outcome and event identities for causation.

**WAIT-006:** Passing an authorized non-Wait proposal to the Wait resolver shall raise `TypeError` as a dispatch/programmer defect and shall not produce an in-world rejected outcome.

**WAIT-007:** The Wait resolver shall not commit its outcome, process scheduled activity, invoke NPCs, or perform presentation.

#### Move resolution

**MOVE-001:** The initial Move resolver shall resolve an authorized Move proposal using only immutable authored connection topology, authored base traversal duration, canonical character location, and canonical connection availability; it shall not interpret traversal requirements, skills, terrain, encumbrance, interruption, randomness, or an LLM.

**MOVE-002:** The public resolver shall have the contract `resolve_move(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` and shall not generate runtime identities internally.

**MOVE-003:** Move actionability checks shall occur in the deterministic order unknown connection, actor not at the connection source, then unavailable connection, with later checks suppressed after the first applicable rejection.

**MOVE-004:** A Move referencing an unknown authored connection shall return a rejected outcome with reason code `unknown-connection`; a Move whose actor is not at the connection source shall return a rejected outcome with reason code `actor-not-at-connection-source`; and a Move over an unavailable connection shall return a rejected outcome with reason code `connection-unavailable`.

**MOVE-005:** Every rejected Move shall use the input snapshot's current simulation time, preserve the originating proposal and caller-supplied outcome identities, and contain no state changes, canonical events, or time advancement; the caller-supplied event identity shall remain unused.

**MOVE-006:** A valid Move shall advance simulation time by exactly the authored connection's `base_traversal_seconds` and shall return a succeeded outcome with reason code `move-completed` at the resulting completion time.

**MOVE-007:** A succeeded Move shall contain exactly two ordered state changes: first one `CharacterLocationChanged` from the actor's current location to the connection destination, then one `SimulationTimeChanged` from current time to completion time.

**MOVE-008:** A succeeded Move shall contain exactly one `ActorMovedEvent` using the caller-supplied event identity and outcome causation, occurring at completion and identifying the actor, connection, source location, and destination location.

**MOVE-009:** Passing an authorized non-Move proposal to the Move resolver shall raise `TypeError` as a dispatch/programmer defect and shall not produce an in-world outcome.

**MOVE-010:** The Move resolver shall not commit its outcome, dispatch another operation, process scheduled activity, invoke NPCs, perform perception or presentation, or introduce movement modifiers and requirement mechanics.

#### Observe resolution

**OBSERVE-001:** The initial Observe resolver shall implement a deliberately narrow focused-perception action using only the accepted deterministic current-state perception snapshot; it shall not reveal richer facts, perform checks, consult package rules, use randomness, or invoke an LLM.

**OBSERVE-002:** The public resolver shall have the contract `resolve_observe(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` and shall not generate runtime identities internally.

**OBSERVE-003:** A surroundings target shall always be perceptible for an authorized actor, while a location, connection, character, or object target shall be perceptible only when its same typed identifier is represented by the corresponding current-state observation returned for that actor.

**OBSERVE-004:** Observe target matching shall inherit the current-state projection boundary exactly: current location; authored outgoing connections including unavailable ones; co-located other characters excluding the actor; and directly co-located or actor-possessed objects excluding another actor's possessions.

**OBSERVE-005:** An unknown, remote, incoming-only, self-character, otherwise hidden, or wrong-namespace specific target shall produce one rejected outcome with reason code `target-not-perceptible`, without distinguishing whether the target exists in canonical truth.

**OBSERVE-006:** A rejected Observe shall use current canonical simulation time, preserve the proposal and caller-supplied outcome identities, contain no effects or event, and leave the caller-supplied event identity unused.

**OBSERVE-007:** A perceptible Observe shall return a succeeded outcome with reason code `observation-completed` at current canonical simulation time, no state changes, and exactly one `ActorObservedEvent` using the caller-supplied identities, authorized actor identity, and proposal's exact typed target.

**OBSERVE-008:** Observe v0 shall never produce a failed outcome or advance simulation time; richer inspection, search, capability, skill, uncertainty, duration, and information-revelation mechanics require later accepted contracts.

**OBSERVE-009:** Passing an authorized non-Observe proposal to the Observe resolver shall raise `TypeError` as a dispatch or programmer defect and shall not produce an in-world outcome.

**OBSERVE-010:** Observe resolution shall reuse `project_current_perception` rather than duplicate spatial or visibility rules, and it shall not commit outcomes, filter event feedback, enrich or record observations, create memory or belief state, persist data, or perform presentation.

#### Speak resolution

**SPEAK-001:** The initial Speak resolver shall treat another character at the speaker's exact current location as audible; it shall not model hearing range, barriers, volume, language comprehension, sensory conditions, or generated interpretation.

**SPEAK-002:** The public resolver shall have the contract `resolve_speak(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` and shall not generate runtime identities internally.

**SPEAK-003:** Speak v0 audibility shall use canonical runtime character locations directly and shall not treat the speaker's visual perception snapshot as a hearing model.

**SPEAK-004:** An unknown, remote, self, or wrong-namespace recipient shall produce one rejected outcome with reason code `recipient-not-audible`, without distinguishing whether the supplied identifier exists elsewhere in canonical truth.

**SPEAK-005:** A rejected Speak shall use current canonical simulation time, preserve the proposal and caller-supplied outcome identities, contain no effects or event, and leave the caller-supplied event identity unused.

**SPEAK-006:** An audible Speak shall return a succeeded outcome with reason code `speech-completed` at current canonical simulation time, no state changes, and exactly one `ActorSpokeEvent` using the caller-supplied identities, authorized speaker identity, proposal recipient identity, and exact utterance.

**SPEAK-007:** Speak v0 shall never produce a failed outcome or advance simulation time; speech duration requires a later explicit rule or proposal contract and shall not be inferred from utterance length.

**SPEAK-008:** Successful speech shall establish only that the utterance was audibly addressed to the recipient; it shall not establish comprehension, belief, memory, agreement, obedience, response, or any recipient state change.

**SPEAK-009:** Passing an authorized non-Speak proposal to the Speak resolver shall raise `TypeError` as a dispatch or programmer defect and shall not produce an in-world outcome.

**SPEAK-010:** Speak resolution shall not deliver event feedback to the recipient, invoke an actor policy or LLM, create a response, commit an outcome, persist data, or perform presentation; addressed-speech perception is an immediate separate follow-up boundary.

**SPEAK-011:** Repeated Speak resolution with equal inputs and caller identities shall produce equal outcomes without mutating or replacing the authorized action, world, submission, proposal, or utterance.

#### Take resolution

**TAKE-001:** The initial Take resolver shall determine object accessibility from canonical runtime state directly; perception, authored initial placement, package rules, randomness, and an LLM shall not authorize the state transition.

**TAKE-002:** The public resolver shall have the contract `resolve_take(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` and shall not generate runtime identities internally.

**TAKE-003:** An object shall be accessible to Take v0 only when its runtime object state exists and its exact current placement is `ObjectAtLocation` at the authorized actor's exact current location.

**TAKE-004:** An unknown, remote, actor-possessed, other-character-possessed, wrong-namespace, or otherwise inaccessible object identifier shall produce one rejected outcome with reason code `object-not-accessible`, without distinguishing which canonical condition applied.

**TAKE-005:** A rejected Take shall use current canonical simulation time, preserve the proposal and caller-supplied outcome identities, contain no effects or event, and leave the caller-supplied event identity unused.

**TAKE-006:** An accessible Take shall return a succeeded outcome with reason code `object-taken` at current canonical simulation time and shall not advance simulation time.

**TAKE-007:** A succeeded Take shall contain exactly one `ObjectPlacementChanged` from the object's exact current `ObjectAtLocation` placement to `ObjectPossessedByCharacter` for the authorized actor.

**TAKE-008:** A succeeded Take shall contain exactly one `ObjectTakenEvent` using the caller-supplied event and outcome identities, current canonical time, authorized actor identity, proposal object identity, and the exact previous placement.

**TAKE-009:** Take v0 shall never produce a failed outcome; duration, carrying limits, permission, consent, theft, transfer, competition, checks, and other possession mechanics require later accepted contracts.

**TAKE-010:** Passing an authorized non-Take proposal to the Take resolver shall raise `TypeError` as a dispatch or programmer defect and shall not produce an in-world outcome.

**TAKE-011:** Take resolution shall not commit its outcome, use perception as mutation authority, produce witness feedback, invoke an actor policy or LLM, trigger an NPC response, update memory or belief, persist data, or perform narration or presentation.

**TAKE-012:** Repeated Take resolution with equal inputs and caller identities shall produce equal outcomes without mutating or replacing the authorized action, world, submission, proposal, object state, or placement.

#### Use resolution

**USE-001:** The initial Use resolver shall interpret a proposal only through the validated rule-pack mechanic, scenario binding, and canonical runtime overlays; authored names, initial placement, perception, randomness, generated text, and Greybridge-specific kernel logic shall not authorize or define its effect.

**USE-002:** The public resolver shall have the contract `resolve_use(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` and shall not generate runtime identities internally.

**USE-003:** A Use proposal shall be applicable only when its exact `(object_id, target location_id)` selects one validated scenario binding, the bound mechanic has the accepted location-target and boolean-fact effect kinds, the actor is currently at that target location, and canonical runtime state places the exact object in that actor's possession.

**USE-004:** An unknown or unbound object, unsupported or wrong-namespace target, non-bound location, remote actor, object not possessed by the actor, missing applicable mechanic, or fact already equal to the binding's target value shall produce one rejected outcome with reason code `use-not-applicable`, without distinguishing which canonical or authored condition applied.

**USE-005:** A rejected Use shall use current canonical simulation time, preserve the proposal and caller-supplied outcome identities, contain no effects or event, advance no time, and leave the caller-supplied event identity unused.

**USE-006:** An applicable Use shall return a succeeded outcome with reason code `object-used` at current canonical time plus the bound mechanic's strictly positive duration.

**USE-007:** A succeeded Use shall contain exactly two ordered state changes: first one `BooleanWorldFactChanged` from the fact's exact current value to the binding's target value, then one `SimulationTimeChanged` from current time to completion time.

**USE-008:** A succeeded Use shall contain exactly one `ObjectUsedEvent` using the caller-supplied event and outcome identities, occurring at completion and identifying the authorized actor, proposal object, and proposal's exact typed target.

**USE-009:** Use v0 shall never return a failed outcome and shall not consume, move, destroy, quantify, or otherwise change the used object; checks, interruption, costs, repeated-use success, progression, and additional effect or target kinds require later accepted contracts.

**USE-010:** Passing an authorized non-Use proposal to the Use resolver shall raise `TypeError` as a dispatch or programmer defect and shall not produce an in-world outcome.

**USE-011:** Use resolution shall not commit its outcome, process newly eligible scheduled activity, change bridge connections as an implicit consequence, produce witness feedback, invoke an actor policy or LLM, update memory or belief, persist data, or perform narration or presentation.

**USE-012:** Repeated Use resolution with equal inputs and caller identities shall produce equal outcomes without mutating or replacing the authorized action, validated packages, world, submission, proposal, mechanic, binding, object state, fact state, or typed target.

#### Operation dispatch

**DISPATCH-001:** Actor-action operation dispatch shall be a pure boundary after authorization and before operation-specific resolution; it shall accept only an `AuthorizedActorAction` and shall not authorize a submission itself.

**DISPATCH-002:** The public dispatcher shall have the contract `dispatch_actor_action(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> Outcome` and shall not generate runtime identities internally.

**DISPATCH-003:** Dispatch shall select a resolver by the concrete operation-specific proposal type rather than by package content, a generic registry, or generated text.

**DISPATCH-004:** `MoveActionProposal`, `WaitActionProposal`, `ObserveActionProposal`, `SpeakActionProposal`, `TakeActionProposal`, and `UseActionProposal` shall route to their corresponding concrete resolvers, preserving the exact authorized action and caller-supplied identities.

**DISPATCH-005:** Dispatch shall return the selected resolver's outcome directly without intentional reconstruction, commitment, repair, presentation, or exception translation.

**DISPATCH-006:** Help proposals shall raise `OperationResolverUnavailableError` until deterministic Help mechanics are accepted and implemented; missing capability shall not produce a canonical rejected or failed outcome.

**DISPATCH-007:** `OperationResolverUnavailableError` shall be a public `RuntimeError` subclass with a typed `operation: ActorActionOperation` attribute and a stable non-blank message identifying the unavailable operation.

**DISPATCH-008:** The unavailable-resolver error shall represent one application capability defect directly and shall not use validation issue tuples or a repair attempt.

**DISPATCH-009:** Initial dispatch shall use the same required caller-supplied `outcome_id` and `event_id` convention as Move and Wait; it shall not introduce an ID provider, event-ID collection, or speculative multi-event abstraction.

**DISPATCH-010:** Dispatch shall not commit outcomes, process scheduled activity, invoke NPC policies or an LLM, perform perception or presentation, access persistence, or introduce a generic resolver protocol, service class, or configurable resolver registry.

#### Trusted submissions and operation references

**ACTION-011:** The system shall keep an untrusted operation-specific proposal payload separate from its trusted application-created proposal-submission envelope.

**ACTION-012:** A proposal submission shall contain proposal identity, source role and identity, intended actor when applicable, simulation-step context, and trace provenance, and generated output shall not supply or override that metadata.

**ACTION-013:** Before resolving an operation, the simulation arbiter shall validate both the proposal payload and whether its trusted source is authorized to submit for the intended actor or world-level operation.

**ACTION-014:** Intent, reasoning, and other cognition records shall remain separate from proposal payloads and shall not become canonical facts merely because they accompany a proposal submission.

**ACTION-015:** Operation arguments shall use namespace-aware references constrained to the domain kinds permitted by that operation rather than one ambiguous universal target identifier.

**ACTION-016:** A move proposal shall identify one authored directed connection rather than only a destination location.

**ACTION-017:** Speak and help proposals shall identify a character, take proposals shall identify an object, and use proposals shall identify the used object together with a typed target reference.

**ACTION-018:** An observe proposal shall distinguish an explicit surroundings target from typed location, connection, character, or object targets.

**ACTION-019:** A wait proposal shall contain a strictly positive integer duration in simulation seconds.

**ACTION-020:** Runtime proposal, simulation-step, outcome, and event identities shall use application-assigned UUID values and shall not be generated by proposal producers or Pydantic model construction.

**ACTION-021:** Authored package identifiers shall remain domain-readable strings and shall not be replaced by runtime UUID identities.

**ACTION-022:** Proposal-submission sources shall be a closed discriminated union with source-specific provenance for the player interpreter, an NPC decision policy, the System director, or a scheduled activity when that source is introduced.

**ACTION-023:** NPC-policy submission provenance shall identify the NPC and configured policy, and System-director provenance shall identify the eligible hook responsible for invocation.

#### Canonical events

**EVENT-001:** The simulation kernel shall represent canonical events as a closed discriminated union of strict event-specific contracts rather than as an event name paired with an arbitrary payload mapping.

**EVENT-002:** Every canonical event shall contain stable event identity, simulation time, an event-type discriminator, a causation link to its originating outcome, and a typed factual payload.

**EVENT-003:** Canonical events shall contain mechanical facts rather than generated narrative prose.

**EVENT-004:** Canonical events shall not encode their observers or player visibility; the perception engine shall determine observations independently for each character.

**EVENT-005:** A rejected outcome shall remain available in the simulation-step trace but shall not create a canonical event, because no attempted action occurred in the simulated world.

**EVENT-006:** The system shall persist current canonical world state directly and shall retain canonical events as durable causal history without requiring event replay as the sole means of world reconstruction.

**EVENT-007:** The initial canonical-event union shall contain exactly actor observed, actor moved, actor spoke, object taken, object used, actor helped, actor waited, and actor action failed variants.

**EVENT-008:** Every initial canonical event shall contain application-assigned event identity, originating outcome identity, non-negative integer occurrence time, and its fixed event-type discriminator.

**EVENT-009:** Actor-observed and object-used events shall reuse the accepted typed observation-target and use-target contracts respectively.

**EVENT-010:** Actor-moved events shall identify the actor, directed connection, previous location, and new location; the two locations shall differ.

**EVENT-011:** Actor-spoke events shall identify speaker, recipient, and non-blank utterance; object-taken events shall identify actor, object, and previous placement.

**EVENT-012:** Actor-helped events shall identify actor and assisted character; actor-waited events shall identify actor and a strictly positive integer duration; actor-action-failed events shall identify actor and attempted supported actor operation.

**EVENT-013:** Failed and succeeded outcomes may contain no canonical event, and the contract layer shall not require one event merely because an operation was validly attempted.

#### Perception

**PERCEPTION-001:** Initial perceived information shall use a closed discriminated union of strict typed observation variants rather than an arbitrary payload mapping or generated prose.

**PERCEPTION-002:** The initial observation union shall contain exactly `LocationObserved`, `ConnectionObserved`, `CharacterObserved`, `ObjectObserved`, and `EventObserved`, discriminated by `observation_type` values `location`, `connection`, `character`, `object`, and `event` respectively.

**PERCEPTION-003:** Every initial observation shall contain the observing character's authored identifier and non-negative integer `observed_at_seconds`.

**PERCEPTION-004:** Location, connection, character, and object observations shall use `source_type="current_state"`; event observations shall use `source_type="canonical_event"` and contain the exact typed `CanonicalEvent` that passed filtering.

**PERCEPTION-005:** `LocationObserved` shall contain `location_id`; `ConnectionObserved` shall contain `connection_id` and strict boolean `is_available`; `CharacterObserved` shall contain `character_id`; and `ObjectObserved` shall contain `object_id` plus the existing typed `ObjectPlacement` perceived for that object.

**PERCEPTION-006:** Initial observations shall remain ID-linked projections and shall not copy authored names, descriptions, connection endpoints, traversal durations, archetypes, goals, plans, or unrestricted package records.

**PERCEPTION-007:** `PerceptionSnapshot` shall be a strict immutable record containing one `observer_id`, one non-negative integer `perceived_at_seconds`, and an immutable ordered tuple of initial observations.

**PERCEPTION-008:** Every observation in a perception snapshot shall have the same observer identity and observation time as the snapshot envelope.

**PERCEPTION-009:** An event observation shall reject a contained canonical event whose occurrence time is later than that observation's time.

**PERCEPTION-010:** Perception snapshots shall accept structurally valid empty observation collections, normalize JSON/YAML-style lists to immutable tuples, and preserve supplied observation order.

**PERCEPTION-011:** Initial observation and snapshot construction shall not resolve world references, determine visibility, enforce actionability, deduplicate observations, perform restricted definition enrichment, invoke an LLM, or claim that a structurally valid snapshot was produced by the perception engine.

**PERCEPTION-012:** Initial transient observation values shall not contain generated observation UUIDs, confidence scores, or salience scores; durable observation identity and scored uncertainty or salience require later accepted recording and rule semantics.

**PERCEPTION-013:** The later initial perception engine shall not infer that an object possessed by another co-located character is visible merely from canonical possession; directly located objects and the observer's own possessions are the safe initial possession boundary until explicit visibility mechanics exist.

**PERCEPTION-014:** Restricted context enrichment shall resolve only identifiers already present in a perception snapshot into approved authored display fields and shall not expose unrestricted canonical world or package content to a narrator or actor policy.

**PERCEPTION-015:** The public current-state projection shall have the contract `project_current_perception(world: ValidatedWorldState, observer_id: AuthoredId) -> PerceptionSnapshot` and shall be independent of wall-clock time.

**PERCEPTION-016:** If `observer_id` does not identify a character in the validated world's character-state namespace, current-state projection shall raise public `PerceptionObserverNotFoundError`, a `ValueError` carrying the supplied `observer_id` and exact message `perception observer not found: {observer_id}`; an object identifier shall follow the same path.

**PERCEPTION-017:** A successful current-state projection shall use canonical `world.state.simulation_time_seconds` for the snapshot and every contained observation and shall contain only `source_type="current_state"` observation variants.

**PERCEPTION-018:** Current-state projection shall begin with exactly one `LocationObserved` for the observer's current canonical location.

**PERCEPTION-019:** After location, projection shall include every authored connection whose source is the observer's current location, in authored connection order, regardless of availability, using its current canonical `is_available` value; incoming-only connections shall be excluded.

**PERCEPTION-020:** After connections, projection shall include every other character currently at the observer's location, excluding the observer, in authored entity order; characters elsewhere shall be excluded.

**PERCEPTION-021:** After characters, projection shall include objects directly at the observer's current location and objects possessed by the observer, in authored entity order; objects elsewhere or possessed by another character shall be excluded even when that possessor is co-located.

**PERCEPTION-022:** Current-state observation ordering shall be location, outgoing connections, co-located other characters, then perceptible objects, with authored order inside each multi-item group rather than runtime tuple order.

**PERCEPTION-023:** Current-state projection shall consume relational guarantees already established by `ValidatedWorldState` and shall not revalidate complete overlays, package references, or authored uniqueness.

**PERCEPTION-024:** Repeated projection with the same validated world and observer shall produce equal snapshots without mutating or replacing the input world, generating identities, or consulting randomness or an LLM.

**PERCEPTION-025:** Initial current-state projection shall not accept or emit canonical-event feedback, apply sensory, environmental, capability, condition, attention, concealment, or within-location geometry rules, perform definition enrichment, record observations, create memory or belief state, persist data, or produce narrative.

**PERCEPTION-026:** The public initial self-action feedback projection shall have the contract `project_self_event_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` and shall be independent of wall-clock time.

**PERCEPTION-027:** Self-action feedback projection shall validate `observer_id` in the same character-state namespace as current-state projection and shall raise the existing `PerceptionObserverNotFoundError` before inspecting event time when the observer is absent.

**PERCEPTION-028:** Self-action event ownership shall use `speaker_id` for `ActorSpokeEvent` and `actor_id` for each of the other seven initial canonical-event variants; recipient, assisted character, target, object possessor, and spatial proximity shall not imply ownership.

**PERCEPTION-029:** Self-action feedback projection shall support the initial canonical-event union exhaustively and shall emit feedback only for events owned by the requested observer.

**PERCEPTION-030:** Before ownership filtering, self-action feedback projection shall validate the entire supplied candidate batch in input order against canonical `world.state.simulation_time_seconds`; the first event occurring later shall raise public `FutureEventFeedbackError`, a `ValueError` carrying `event_id`, `occurred_at_seconds`, and `perceived_at_seconds`, even when that event is not owned by the observer.

**PERCEPTION-031:** Each emitted self-action feedback item shall be an `EventObserved` whose observer is the requested character, whose observation time is current canonical simulation time, whose source is `canonical_event`, and whose event is the exact supplied canonical event object.

**PERCEPTION-032:** Self-action feedback projection shall preserve supplied order and duplicate matching inputs, accept past and current-time events, and return an immutable empty tuple when the candidate batch is empty or has no owned event.

**PERCEPTION-033:** Candidate-event window selection and already-delivered tracking shall belong to the caller or later coordinator and persistence boundaries; self-action feedback projection shall not query canonical history, maintain a cursor, deduplicate, or record delivery.

**PERCEPTION-034:** Repeated self-action feedback projection with equal inputs shall produce equal outputs without mutating or replacing the validated world or supplied event tuple, generating identities, consulting randomness, or invoking an LLM.

**PERCEPTION-035:** Initial self-action feedback shall not determine witness visibility, speech audibility, pre- or post-action co-location, target awareness, current-state composition, enrichment, observation recording, persistence, memory, belief, narration, or presentation.

**PERCEPTION-036:** The public addressed-speech feedback projection shall have the contract `project_addressed_speech_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` and shall be independent of wall-clock time.

**PERCEPTION-037:** Addressed-speech feedback shall validate `observer_id` in the character-state namespace before inspecting event time and shall reuse `PerceptionObserverNotFoundError` for an absent observer.

**PERCEPTION-038:** Before event-type or recipient filtering, addressed-speech feedback shall validate the entire candidate batch in input order against current canonical simulation time and shall reuse `FutureEventFeedbackError` for the first future event.

**PERCEPTION-039:** Addressed-speech feedback shall emit an observation only for `ActorSpokeEvent` values whose `recipient_id` equals the observer; the committed event's explicit recipient identity shall establish delivery eligibility without rechecking current or visual-perception state.

**PERCEPTION-040:** Current speaker and recipient locations, later movement, the speaker's current perception, and the recipient's current-state perception shall not change whether a past or current addressed-speech event produces recipient feedback.

**PERCEPTION-041:** Each emitted addressed-speech feedback item shall be an `EventObserved` whose observer is the requested recipient, whose observation time is current canonical simulation time, whose source is `canonical_event`, and whose event is the exact supplied `ActorSpokeEvent` object.

**PERCEPTION-042:** Addressed-speech feedback shall preserve matching input order and duplicates, accept past and current-time events, and return an immutable empty tuple for an empty batch or when no event is addressed to the observer.

**PERCEPTION-043:** Candidate-event window selection, already-delivered tracking, self-feedback composition, current-state composition, and deduplication across feedback sources shall belong to a later caller or coordinator rather than addressed-speech projection.

**PERCEPTION-044:** Repeated addressed-speech projection with equal inputs shall produce equal outputs without mutating or replacing the world or event tuple, generating identities, invoking policies or an LLM, recording observations, creating memory or belief, persisting data, narrating, or determining general witness audibility.

**PERCEPTION-045:** The public initial Take-witness projection shall have the contract `project_take_witness_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` and shall be independent of wall-clock time.

**PERCEPTION-046:** Take-witness feedback shall validate `observer_id` in the character-state namespace before inspecting event time and shall reuse `PerceptionObserverNotFoundError` for an absent observer.

**PERCEPTION-047:** Before event-type or witness filtering, Take-witness feedback shall validate the entire candidate batch in input order and require every event occurrence time to equal current canonical simulation time; the first past or future mismatch shall raise public `WitnessEventTimeMismatchError`, a `ValueError` carrying `event_id`, `occurred_at_seconds`, and `perceived_at_seconds`.

**PERCEPTION-048:** Take-witness feedback shall emit an observation only for an `ObjectTakenEvent` whose `actor_id` differs from the observer and whose `previous_placement` is `ObjectAtLocation` at the observer's exact current canonical location.

**PERCEPTION-049:** Each emitted Take-witness item shall be an `EventObserved` whose observer is the requested witness, whose observation time is current canonical simulation time, whose source is `canonical_event`, and whose event is the exact supplied `ObjectTakenEvent` object.

**PERCEPTION-050:** Take-witness feedback shall preserve matching input order and duplicates and shall return an immutable empty tuple for an empty batch or when no event qualifies.

**PERCEPTION-051:** The committed event's exact previous location placement shall establish the Take event location; projection shall not recheck the object's current placement, authored initial placement, ownership, or current-state perception.

**PERCEPTION-052:** Candidate-event window selection, already-delivered tracking, self-feedback composition, addressed-speech composition, current-state composition, cross-source ordering, and deduplication shall belong to a later caller or coordinator.

**PERCEPTION-053:** Repeated Take-witness projection with equal inputs shall produce equal outputs without mutating or replacing the world or event tuple, generating identities, invoking policies or an LLM, triggering reactions, recording observations, creating memory or belief, persisting data, narrating, or adding line-of-sight, concealment, attention, or other witness mechanics.

**PERCEPTION-054:** Take-witness projection shall not change current-state, self-action, or addressed-speech feedback behavior, validation, ownership, recipient, order, duplicate, or event-identity semantics.

**PERCEPTION-055:** The public initial speech-overhearing projection shall have the contract `project_speech_overhearing_feedback(world: ValidatedWorldState, observer_id: AuthoredId, events: tuple[CanonicalEvent, ...]) -> tuple[EventObserved, ...]` and shall be independent of wall-clock time.

**PERCEPTION-056:** Speech-overhearing feedback shall validate `observer_id` in the character-state namespace before inspecting event time and shall reuse `PerceptionObserverNotFoundError` for an absent observer.

**PERCEPTION-057:** Before event-type or overhearing filtering, speech-overhearing feedback shall validate the entire candidate batch in input order and require every event occurrence time to equal current canonical simulation time; the first past or future mismatch shall reuse `WitnessEventTimeMismatchError` unchanged.

**PERCEPTION-058:** After observer and time validation, speech-overhearing feedback shall resolve the speaker of every supplied `ActorSpokeEvent` in input order before filtering any event for the requested observer; the first absent speaker shall raise public `SpeechSpeakerNotFoundError`, a `ValueError` carrying exact `event_id` and `speaker_id` attributes.

**PERCEPTION-059:** Speech-overhearing feedback shall emit an observation only for an `ActorSpokeEvent` when the requested observer is neither its speaker nor its addressed recipient and the resolved speaker has the observer's exact current canonical location.

**PERCEPTION-060:** Each emitted speech-overhearing item shall be an `EventObserved` whose observer is the requested third party, whose observation time is current canonical simulation time, whose source is `canonical_event`, and whose event is the exact supplied `ActorSpokeEvent` object.

**PERCEPTION-061:** Speech-overhearing feedback shall preserve matching input order and duplicates and shall return an immutable empty tuple for an empty batch or when no event qualifies.

**PERCEPTION-062:** Exact-current-time speaker and observer locations shall establish immediate co-location for speech overhearing; projection shall not revalidate recipient existence or location, reconstruct historical locations, or call current-state perception.

**PERCEPTION-063:** Candidate-event window selection, already-delivered tracking, composition with self-action or addressed-speech feedback, current-state composition, cross-source ordering, and deduplication shall belong to a later caller or coordinator.

**PERCEPTION-064:** Repeated speech-overhearing projection with equal inputs shall produce equal outputs without mutating or replacing the world or event tuple, generating identities, invoking policies or an LLM, triggering comprehension or reactions, recording observations, creating memory or belief, persisting data, narrating, or adding hearing range, barriers, volume, language, attention, or other richer audibility mechanics.

#### Actor loop

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

**POLICY-007:** The initial bounded NPC decision context shall contain an application-assigned decision-context identity, the NPC's authored identity summary, goals and current plan, and one perception snapshot for that NPC; it shall not contain canonical world state, another actor's private information, memories, beliefs, or trusted action-submission metadata.

**POLICY-008:** An NPC decision context shall be strict and immutable, shall require at least one goal, and shall require its perception snapshot's observer identity to equal its NPC identity.

**POLICY-009:** The Greybridge caretaker rule policy shall deterministically propose only from its bounded decision context, shall make no LLM call, and shall return an untrusted actor-action proposal payload rather than a trusted submission.

**POLICY-010:** When the Greybridge caretaker context does not satisfy a recognized safe action rule, the policy shall return a deterministic 60-second Wait proposal without modifying its context or canonical world state.

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

### Initial scenario

**SCENARIO-001:** The initial scenario shall be Storm at Greybridge, centered on a remote waystation, an unstable bridge, and its far bank.

**SCENARIO-002:** The player and an injured LLM-assisted courier carrying medicine shall begin at the waystation.

**SCENARIO-003:** A rule-driven caretaker at the bridge shall initially observe structural damage unavailable to the player and courier.

**SCENARIO-004:** A scheduled flood event shall make crossing the bridge more dangerous or impossible according to canonical bridge state and loaded rules.

**SCENARIO-005:** A world-creation System director hook shall be able to propose an optional objective concerning the courier or medicine crossing before the route closes.

**SCENARIO-006:** The scenario shall permit materially different outcomes, including the courier crossing, only the medicine crossing, the player crossing alone, the bridge being reinforced, or the route closing without a crossing.

**SCENARIO-007:** The scenario shall not designate one mandatory outcome as the only valid continuation of the world.

**SCENARIO-008:** The initial rule pack shall support a Fieldcraft check and a player-visible Fieldcraft progression event within the scenario.

**SCENARIO-009:** The first authored content foundation shall use rule package `greybridge-rules` version `0.1.0` and scenario package `storm-at-greybridge` version `0.1.0`, with the scenario manifest pinning that exact rule identity.

**SCENARIO-010:** The Greybridge content foundation shall define the waystation, span, and far bank as three locations connected in both directions, with 60-second waystation-span traversal and 120-second span-far-bank traversal.

**SCENARIO-011:** The Greybridge content foundation shall include one player at the waystation, the injured LLM-assisted courier at the waystation, the rule-driven caretaker at the span, medicine possessed by the courier, and reinforcement materials at the waystation, with all archetype and policy references resolving through the paired rule package.

**SCENARIO-012:** Until dedicated schemas exist, the Greybridge content foundation shall not encode Fieldcraft, actions, bridge damage, perceptible facts, scheduled flood activity, System director hooks, objectives, progression, or other mechanics as unknown fields or misleading substitutes, and shall not be described as a complete playable scenario.

**SCENARIO-013:** Greybridge package version `0.2.0` shall preserve the `0.1.0` foundation and add one authored `reinforce-structure` object-use mechanic, one initially false `bridge-reinforced` boolean world fact, and one deterministic binding from `reinforcement-materials` at `greybridge-span` to that fact becoming true after 300 simulation seconds; the scenario shall pin `greybridge-rules` version `0.2.0` exactly.

### Primary persistence

**STORE-001:** The initial version shall persist authoritative world and character data in SQLite.

**STORE-002:** When a simulation step completes, the system shall commit its canonical state transitions and events atomically before reporting completion.

**STORE-003:** The SQLite store shall preserve world metadata, simulation time, canonical entities and locations, committed events, character memories and beliefs, and simulation-step traces across application restarts.

**STORE-004:** When an authoritative SQLite transaction fails, the system shall not report the associated simulation step as completed.

**STORE-005:** Qdrant shall remain a derived retrieval index and shall not be required to recover authoritative world or character history.

**STORE-006:** One application-owned SQLite transaction shall define simulation-step completion across the replacement world state, canonical events, scheduled-queue effects, authoritative character data, and simulation-step trace; participating repositories shall not commit those records independently.

**STORE-007:** The initial SQLite representation shall store the current immutable canonical world state as one schema-versioned JSON snapshot, keep world identity, revision, and exact rule and scenario package identities and versions in explicit columns, and retain canonical events and simulation-step traces as separate append-only records.

**STORE-008:** SQLite persistence operations participating in one application step shall use an explicit unit of work whose repositories share one active connection, cannot commit independently, and become durable only when the application explicitly commits the unit; exceptions and uncommitted exits shall roll back the transaction.

**STORE-009:** Opening an empty SQLite store shall create the current schema version 3 transactionally and record it with `PRAGMA user_version`; opening schema version 1 or 2 shall migrate transactionally to version 3 without losing world, canonical-event, or completed actor-action trace data, opening version 3 shall preserve its data, and opening any other version shall fail without modifying the database.

**STORE-010:** Loading persistence data shall strictly decode a stored-world record containing its package references, runtime state, and scheduled queue without resolving package files; before simulation use, an application service shall resolve the exact recorded package versions and validate the decoded state against them.

**STORE-011:** Creating the singleton world shall assign revision 0, and replacing it shall atomically require the loaded revision, increment the stored revision by exactly one on success, and reject a mismatch without making any unit-of-work writes durable.

**STORE-012:** Canonical event history shall preserve committed insertion order, associate each event with its world and resulting world revision, retain event and outcome identities, event type and occurrence time, reject duplicate event identities atomically, and strictly decode stored payloads as `CanonicalEvent`.

**STORE-013:** Simulation-step trace history shall be a separate append-only SQLite record ordered by database-assigned insertion sequence and associated with its world, resulting world revision, unique simulation-step identity, outcome identity, outcome status, and strict trace payload.

**STORE-014:** A trace insert shall require the current world identity and revision, reject a duplicate simulation-step identity, and strictly cross-check explicit trace metadata against its payload; any failure shall poison and roll back the surrounding unit of work.

**STORE-015:** Player-input trace history shall be a separate append-only SQLite record ordered by database-assigned insertion sequence and associated with its world, observed and resulting world revisions, unique application-assigned player-input identity, completion kind, optional linked actor-action simulation-step identity, and strict trace payload.

**STORE-016:** A player-input trace insert shall require the current world identity and its resulting revision, reject a duplicate player-input identity, and strictly cross-check explicit metadata against its payload. Thought-only and clarification traces shall retain the same observed and resulting revisions. An action-linked trace shall retain exactly one greater resulting revision and reference a completed actor-action trace with the same world and resulting revision. Any failure shall poison and roll back the surrounding unit of work.

### World lifecycle

**LIFECYCLE-001:** Initial-world construction shall deterministically derive a complete `WorldState` from one `ValidatedGamePackages` pair: simulation time 0, characters and objects in authored entity order at their authored initial placements, connections in authored order and initially available, and boolean world facts in authored order at their authored initial values.

**LIFECYCLE-002:** Initial-world construction shall produce an empty scheduled-activity queue until accepted scenario schemas author initial scheduled occurrences, and shall validate the derived state against the same packages before persistence.

**LIFECYCLE-003:** Creating a world shall accept caller-assigned world identity and validated packages, derive the known initial state, persist the exact package identities and versions at revision 0, explicitly commit, and return an active-world result only after durable success; it shall fail without changing an existing singleton world.

**LIFECYCLE-004:** Resuming shall load the singleton stored world, resolve only the exact recorded rule and scenario package identities and versions beneath the configured game-package root, semantically validate that pair, require exact ownership agreement, validate the decoded runtime state against it, and return the stored scheduled queue without modifying authoritative data.

**LIFECYCLE-005:** Missing, malformed, wrong-kind, dependency-incompatible, package-incompatible, or world-state-incompatible data shall prevent creation or resume from returning an active world; package resolution shall remain outside persistence repositories.

**LIFECYCLE-006:** The explicit development-reset operation shall require an existing singleton world, accept caller-assigned replacement world identity and validated packages, and transactionally delete the prior current world, canonical-event history, and simulation-step-trace history before creating the known initial world at revision 0.

**LIFECYCLE-007:** Development reset shall either commit the complete replacement and empty histories or preserve the prior world and histories unchanged. It shall not preserve revision continuity, emit a canonical event or trace, invoke a world-creation hook, authorize production callers, or expose general state editing.

**LIFECYCLE-008:** World creation, resume, and development reset shall not discover package versions, generate identities, inspect policy implementation registries, invoke an LLM, execute actor policies or scheduled activities, advance simulation time, or create save slots.

### Simulation-step coordination

**STEP-001:** The initial actor-action coordinator shall accept a trusted `ActorActionSubmission`, caller-assigned outcome and event identities, validated game packages, and the authoritative SQLite store; it shall not generate runtime identities or accept an unvalidated proposal payload directly.

**STEP-002:** The coordinator shall load the singleton stored world inside one unit of work, require its exact recorded package identities and versions to match the supplied validated packages, and validate the decoded runtime state against those packages before authorization or resolution.

**STEP-003:** The coordinator shall compose the existing public authorization, type-directed dispatch, outcome commitment, current-state perception, and self-event-feedback boundaries without duplicating their rules.

**STEP-004:** A completed actor-action step trace shall contain exactly trace schema version 1, the simulation-step and decision-context identities, the exact trusted submission, the exact resolved outcome including its state changes, the resulting actor current-state perception snapshot, and the resulting actor self-event feedback.

**STEP-005:** A completed trace shall require its simulation-step and decision-context identities to match the submission, its outcome proposal identity to match the submission proposal, and all perception evidence to identify the submitted actor at the committed outcome time.

**STEP-006:** Every successfully coordinated actor-action submission, including one with a rejected outcome or otherwise unchanged canonical state, shall replace the durable singleton world at the next revision, preserve the scheduled-activity queue unchanged, append any canonical outcome events, append exactly one completed-step trace, and explicitly commit them in one unit of work.

**STEP-007:** The coordinator shall report a completed result only after the unit of work commits. Authorization, dispatch, commitment, package compatibility, validation, trace construction, or persistence failure shall return no completed result and shall leave world, event, and trace history unchanged.

**STEP-008:** The first coordinator shall not select, consume, execute, reschedule, or trace scheduled activities; scheduled-activity execution remains a later coordinator extension after each activity variant has accepted execution semantics.

**STEP-009:** The first coordinator shall not interpret player text, invoke an LLM or actor policy, compose witness or addressed-speech observations, track perception delivery, narrate, present results, create or reset a world, or expose an HTTP interface.

**STEP-010:** The public coordinator result shall identify the committed world and resulting revision and retain the exact completed actor-action trace returned only after durable success.

**STEP-011:** The free-form player-turn coordinator shall read one current player perception and its world revision before calling the player interpreter, without holding a SQLite write unit of work during model latency. It shall then recheck the exact world identity and observed revision before any persistence.

**STEP-012:** If the world changed after the coordinator obtained the interpretation perception, it shall return a typed stale-input failure, create no trusted action metadata, and leave world, event, actor-action trace, and player-input trace history unchanged.

**STEP-013:** For a thought-only or clarification interpretation at the rechecked revision, the coordinator shall application-assign one player-input identity, append exactly one matching no-action player-input trace, commit it, and return completion only after durable success without advancing canonical state or time.

**STEP-014:** For an interpreted proposal at the rechecked revision, the coordinator shall application-assign player-input, proposal, simulation-step, decision-context, outcome, and event identities; create the trusted player-interpreter submission; resolve the actor action; append its completed actor-action trace and the action-linked player-input trace; and commit all resulting world, events, and traces in one SQLite unit of work. It shall return completion only after durable success.

**STEP-015:** The free-form coordinator shall expose only exact interpreted thought or clarification and player-safe committed action evidence. It shall not expose canonical state, package definitions, provider details, another actor's private information, functional prompt messages, or raw generation attempts.

### FastAPI application boundary

**API-001:** The initial FastAPI application shall be constructed from an explicit SQLite store, game-package root, validated initial package pair, identity factory, and development-reset setting rather than module-global mutable state.

**API-002:** A create-world request shall contain no caller-selected canonical identity. The API shall assign the world UUID, create the singleton from the configured validated packages, and return only lifecycle metadata after durable commit.

**API-003:** A resume-world request shall resolve and validate only the singleton's exact recorded package versions and return lifecycle metadata without changing authoritative state.

**API-004:** The development-reset HTTP operation shall be unavailable unless explicitly enabled in application configuration. When enabled, the API shall assign the replacement world UUID and invoke the existing atomic destructive reset without accepting direct state, package, history, or identity edits from the client.

**API-005:** The initial turn request shall accept exactly one strict `ActorActionProposal` payload. The API shall bind it to the validated scenario's sole player and create the trusted player-interpreter source, proposal, simulation-step, decision-context, outcome, and event identities; HTTP clients shall not supply or override trusted provenance or runtime identities.

**API-006:** A successful turn response shall be returned only after the actor-action coordinator commits. It shall expose the world identity, resulting revision, simulation-step identity, structured outcome status and reason, current player perception, and player self-event feedback, but not canonical state, scheduled work, state changes, the full trace, or other actors' private information.

**API-007:** A resolved rejected or failed action is a completed domain result and shall use a successful HTTP response. Missing-world failures shall map to `404`, an existing-world creation conflict shall map to `409`, disabled development reset shall map to `403`, and malformed request bodies shall use FastAPI's `422` validation response.

**API-008:** Unexpected package, stored-state, persistence, or programming failures shall not be flattened into a successful result or expose exception details through an application-defined error response. Failed operations shall preserve the atomicity guarantees of the invoked application service.

**API-009:** The initial API shall not interpret free-form text, invoke an LLM or actor policy, narrate, execute scheduled activities, expose inspection history, authorize arbitrary actor identities, accept canonical state mutations, or implement production authentication.

**API-010:** The free-form player-turn endpoint shall accept exactly one strict non-blank player-text field, bind it to the validated sole player, invoke only the transactional player-turn coordinator, and expose one strict player-safe thought-only, clarification, action-completed, or stale response. Clients shall not supply identities, proposals, provenance, revisions, model configuration, trace evidence, or canonical state.

**API-011:** The endpoint shall return completed thought, clarification, rejected action, failed action, and succeeded action results only after the coordinator commits. A stale result shall map to `409` without claiming completion. If no functional gateway is configured, the application shall use the existing safe failed-generation clarification path rather than exposing provider configuration or failure details.

**API-012:** Runtime bootstrap may configure the local functional gateway only from complete explicit environment settings for base URL, model, positive timeout seconds, and positive completion-token limit. Absent settings shall preserve the safe unavailable-gateway path; partial or invalid settings shall fail bootstrap without opening a server.

**API-013:** The free-form player-turn endpoint shall expose distinct player-safe results for settled action completion, committed action with scheduled progress pending, and scheduled progress completed before a new input is interpreted. It shall not expose NPC context, proposal, trace payload, provider evidence, or unprocessed submitted text.

**STEP-016:** After an action-linked player input commits, the player-turn coordinator shall attempt one due scheduled activity before presenting settled completion. A no-activity or completed scheduled result yields a final player perception and current world revision; a stale or operational scheduled result yields an honest committed-action progress-pending result without claiming a final turn state.

**STEP-017:** Before interpreting a later player input, the coordinator shall attempt pending due scheduled activity. If it completes, it shall return a player-safe scheduled-progress result from the resulting state and shall not call the interpreter, persist the submitted input, or execute another player action. If no activity is due it may proceed to normal interpretation; unresolved progress shall remain pending.

### Deterministic player page

**PLAYERPAGE-001:** The initial Streamlit player page shall communicate only through the FastAPI HTTP boundary and shall not load packages, open SQLite, call simulation or persistence services, or construct trusted submission metadata.

**PLAYERPAGE-002:** The page shall accept an API base URL through explicit local configuration, use a bounded request timeout, validate successful and mapped-error bodies against the API contracts, and distinguish unavailable transport, malformed response, mapped application failure, and durable domain outcome.

**PLAYERPAGE-003:** When no world exists, the page shall offer world creation. When a world exists, it shall show only returned lifecycle metadata and one free-form player-turn input. Development reset shall be a separate explicitly confirmed control.

**PLAYERPAGE-004:** The page shall send one non-blank free-form player input only through the strict player-turn API contract. It shall not construct or infer an action proposal, actor, target, motive, trusted identity, or unreturned consequence.

**PLAYERPAGE-005:** The page shall present player-turn results only from validated player-safe API responses. It shall distinguish thought-only, clarification, settled action, committed action with progress pending, scheduled progress completed, and scheduled progress pending using deterministic structured text; it shall show outcome status and reason, player perception, and self-event feedback only when that response contains them. It shall not invent narration, System notifications, canonical state, hidden actors, or unreturned consequences.

**PLAYERPAGE-006:** Player-page history shall be presentation-only Streamlit session state in validated player-turn response order. It shall retain submitted text only when the API response represents completion of that input; a scheduled-progress response that did not interpret the submitted text shall not retain that text. History shall clear after successful world creation or reset and shall never be treated as canonical history or sent back as action context.

**PLAYERPAGE-007:** Transport, validation, stale-input, and application failures shall remain visibly distinct from completed rejected or failed domain outcomes. A failed request shall not append turn history, advance displayed lifecycle metadata, or claim an action completed.

**PLAYERPAGE-008:** The first page shall not start or configure an ASGI server, implement production deployment or authentication, expose inspection data, invoke an LLM, execute NPC or System activity, or add an alternate direct application path.

### Outcome randomness

**RANDOM-001:** The simulation shall resolve outcomes deterministically unless a loaded rule explicitly requires a random check.

**RANDOM-002:** The simulation arbiter shall be the only component authorized to draw randomness used by canonical outcome resolution.

**RANDOM-003:** The system shall persist the world random seed and generator state required for continued reproducible resolution.

**RANDOM-004:** When the arbiter draws a random value, the resulting event history shall record the draw's purpose, parameters, and result.

**RANDOM-005:** LLM components shall not generate or replace canonical random results.

**RANDOM-006:** The arbiter shall accept an injected random source so tests can exercise specified outcomes without depending on a pseudorandom implementation sequence.

**RANDOM-007:** The initial canonical randomness primitive shall be one inclusive integer-range draw; dice, probability checks, choices, and weighted selection shall be deterministic rule mechanics built on that primitive rather than additional random-source operations.

**RANDOM-008:** `IntegerDrawRequest` shall be a strict immutable record containing exactly application-supplied UUID `draw_id`, extensible strict kebab-case `purpose`, and strict integer `lower_inclusive` and `upper_inclusive` bounds, with `lower_inclusive < upper_inclusive`.

**RANDOM-009:** `IntegerRandomSource` shall expose only keyword-based `draw_integer(*, lower_inclusive: int, upper_inclusive: int) -> int`; the source shall receive neither draw identity nor purpose.

**RANDOM-010:** The public arbiter-facing operation shall have the contract `draw_recorded_integer(request: IntegerDrawRequest, source: IntegerRandomSource) -> IntegerDrawRecord`.

**RANDOM-011:** `IntegerDrawRecord` shall be a strict immutable record containing exactly the request's draw identity, purpose, and inclusive bounds plus the returned strict integer result; the operation shall preserve request metadata exactly and shall not generate identity.

**RANDOM-012:** If an integer random source returns a boolean, non-integer, or value outside the requested inclusive range, the draw operation shall raise `RandomSourceContractError` and shall not produce a draw record; it shall not clamp, coerce, or retry the result.

**RANDOM-013:** If an integer random source raises an exception, the draw operation shall propagate that exception unchanged and shall not produce a draw record.

**RANDOM-014:** The initial recorded-integer-draw boundary shall not provide a concrete pseudorandom generator, seed or generator-state persistence, rule-check formulas, outcome or event integration, simulation-step trace integration, retries, logging, or LLM behavior.

### Activity scheduling

**SCHEDULE-001:** The scheduler shall order eligible activities by simulation time, explicit phase priority, and stable insertion sequence.

**SCHEDULE-002:** For activities due at the same simulation time, the default phase order shall be scheduled environmental events, NPC activities, and System director hooks.

**SCHEDULE-003:** The system shall resolve the triggering player action before processing activities made eligible by that action's time advancement.

**SCHEDULE-004:** The scheduler shall submit eligible activities to the simulation arbiter serially and shall not permit simultaneous canonical state mutation.

**SCHEDULE-005:** The system shall record scheduling and ordering metadata in the simulation-step trace.

**SCHEDULE-006:** Given the same committed state and scheduled activities, the scheduler shall produce the same activity order.

**SCHEDULE-007:** Runtime scheduled activities shall form a closed discriminated union of `EnvironmentalScheduledActivity`, `NpcScheduledActivity`, and `SystemDirectorScheduledActivity` eligibility records rather than one generic activity with an arbitrary payload.

**SCHEDULE-008:** Every scheduled-activity variant shall require an application-assigned UUID `activity_id`, non-negative integer `eligible_at_seconds`, and caller-assigned non-negative integer `insertion_sequence` without generating runtime identity or ordering metadata internally.

**SCHEDULE-009:** Environmental activity shall identify an authored `schedule_id`, NPC activity shall identify an authored `npc_id`, and System-director activity shall identify an authored `hook_id`; NPC activity shall not duplicate policy identity, and no variant shall embed executable callbacks, proposals, outcomes, or arbitrary mechanic arguments.

**SCHEDULE-010:** Scheduler phase priority shall derive from the activity variant as environmental before NPC before System director and shall not be a caller-editable record field; deterministic execution order shall use `(eligible_at_seconds, phase_priority, insertion_sequence)` and shall not use runtime UUID ordering.

**SCHEDULE-011:** `ScheduledActivityQueue` shall be a strict immutable record containing an immutable ordered tuple of scheduled activities, shall normalize JSON/YAML-style lists to tuples, shall allow an empty queue, and shall preserve supplied storage order without requiring it to equal execution order.

**SCHEDULE-012:** A scheduled-activity queue shall reject duplicate activity identities and duplicate insertion sequences while allowing equal eligibility times and deliberately unsorted storage order.

**SCHEDULE-013:** Each scheduled activity shall represent one runtime occurrence; recurring schedule definitions shall create separate one-shot activity occurrences rather than placing recurrence rules in the runtime eligibility record.

**SCHEDULE-014:** Initial scheduled-activity construction shall validate structural contracts only and shall not resolve authored NPC, schedule, or hook references before their owning package-definition and relational-validation boundaries exist.

**SCHEDULE-015:** Scheduled-activity contracts shall not select eligible work, remove activities from a queue, execute mechanics or policies, submit proposals, resolve outcomes, mutate canonical state, advance time, persist data, or invoke an LLM.

**SCHEDULE-016:** The public deterministic selection operation shall have the contract `select_eligible_activities(world: ValidatedWorldState, queue: ScheduledActivityQueue) -> ScheduledActivitySelection` and shall use only canonical world time and the supplied validated queue.

**SCHEDULE-017:** `ScheduledActivitySelection` shall be a strict immutable record containing exactly non-negative `selected_at_seconds`, an immutable ordered `eligible_activities` tuple, and `remaining_queue: ScheduledActivityQueue`; serialized eligible lists shall normalize to tuples.

**SCHEDULE-018:** Selection shall treat every activity with `eligible_at_seconds <= world.state.simulation_time_seconds` as eligible, including overdue and exactly due activities, and shall leave only strictly future activities in the remaining queue.

**SCHEDULE-019:** Eligible execution order shall use the exact key `(eligible_at_seconds, derived_phase_rank, insertion_sequence)`, where environmental rank is zero, NPC rank is one, and System-director rank is two; phase mapping shall be exhaustive and selection shall not use UUID or queue storage order as a tie-breaker.

**SCHEDULE-020:** Selection shall preserve the original supplied storage order of pending activities and shall retain the exact scheduled-activity objects in both result groups.

**SCHEDULE-021:** A structurally valid selection result shall require every eligible activity to be due, every remaining activity to be strictly future, eligible activities to be in exact scheduler order, and activity identities and insertion sequences to be unique across both groups.

**SCHEDULE-022:** When no activity is eligible, selection shall reuse the exact input queue as `remaining_queue`; otherwise it shall return a new remaining queue, including an empty queue when every activity is eligible.

**SCHEDULE-023:** Repeated selection with equal world and queue inputs shall produce equal results without mutating or replacing those inputs, generating identities, resolving package references, executing activities, consulting randomness, persisting data, or invoking an LLM.

**SCHEDULE-024:** A scenario package may declare an ordered immutable catalog of initial one-shot NPC activity occurrences. Each declaration shall contain only a non-negative eligibility time and an authored NPC identity; it shall not contain runtime activity identity, insertion sequence, policy identity, callbacks, proposals, outcomes, recurrence, or arbitrary payload.

**SCHEDULE-025:** Scenario-package validation shall require every initial NPC activity declaration to reference one authored NPC character. It shall not require that NPC's policy implementation to be available at package load or world creation.

**SCHEDULE-026:** World creation and development reset shall deterministically materialize every validated initial NPC activity declaration into the persisted scheduled queue. The application shall derive one distinct runtime activity UUID from the caller-supplied world identity and stable declaration identity, and shall assign insertion sequence from authored declaration order.

**SCHEDULE-027:** Initial queue materialization shall retain authored eligibility time and NPC identity exactly, produce no canonical event or step trace, and persist the resulting queue atomically with revision-zero world creation or destructive development reset.

**SCHEDULE-028:** Initial activity declarations and materialization shall not select, execute, consume, reschedule, recur, invoke an LLM or policy, advance time, or alter the existing resume behavior.

**SCHEDULE-029:** The initial scheduled-execution coordinator shall select at most one first due activity from the validated persisted queue. With no due activity it shall return a typed no-activity result without identities or writes; if the first due variant is unsupported it shall fail without consuming or skipping it.

**SCHEDULE-030:** The initial coordinator shall execute only a due `NpcScheduledActivity` for the authored Greybridge caretaker through its existing bounded policy and authoritative actor-action path. It shall derive policy provenance from the authored NPC rather than activity data, and shall not execute environmental or System-director activity.

**SCHEDULE-031:** Policy evaluation shall occur outside a SQLite write unit of work. Before assigning trusted action identities, the coordinator shall recheck exact world identity, revision, and that the selected activity remains the first due queue entry; a mismatch returns typed stale activity with no writes.

**SCHEDULE-032:** A completed or rejected caretaker activity shall atomically replace the world with the selected activity removed, append the ordinary actor-action events and trace, append exactly one linked scheduled-activity execution trace, and commit once. Operational failure shall leave queue, world, events, and both trace histories unchanged.

**SCHEDULE-033:** A scheduled-activity execution trace shall be strict immutable schema version 1 evidence containing the exact selected activity, its selected-at simulation time, and the linked completed actor-action simulation-step identity. Persistence shall verify the linked actor trace has the same world and resulting revision.

**SCHEDULE-034:** SQLite schema version 4 shall add append-only scheduled-activity execution trace history and migrate V1, V2, and V3 transactionally without rewriting existing world, event, actor-action, or player-input records. Development reset shall clear the new history together with the existing timeline.

### System director eligibility

**DIRECTOR-001:** The system shall invoke the System director only when an explicit configured hook becomes eligible.

**DIRECTOR-002:** Rule or scenario packages shall be able to configure System director hooks for world creation, matching canonical events, scenario milestones, or elapsed simulation-time intervals.

**DIRECTOR-003:** A System director hook shall declare limits that prevent invocation more frequently than its configured minimum simulation-time interval or maximum count.

**DIRECTOR-004:** When no System director hook is eligible, the system shall not invoke the System director.

**DIRECTOR-005:** When a System director hook becomes eligible, the simulation-step trace shall record the hook identifier and eligibility reason.

**DIRECTOR-006:** System director eligibility shall not bypass simulation arbiter validation of any resulting action proposal.

### LLM output contracts

**LLM-001:** The system shall accept output from the player input interpreter, LLM-assisted NPC decision policy, or System director only after it conforms to the role's explicit strict Pydantic model.

**LLM-002:** The narrator may return prose, but its output shall remain presentation derived from a supplied perception snapshot.

**LLM-003:** When a functional LLM output fails validation, the system shall allow at most one repair attempt using the same context envelope, required schema, and validation errors.

**LLM-004:** When player input interpretation remains invalid after repair, the system shall request clarification without advancing simulation time.

**LLM-005:** When an NPC decision remains invalid after repair, the system shall apply the configured safe no-op or deterministic fallback without accepting the invalid output.

**LLM-006:** When a System director output remains invalid after repair, the system shall skip the action proposal without changing canonical world state.

**LLM-007:** The system shall not derive canonical operations from unstructured generated prose using regular expressions or other best-effort extraction.

**LLM-008:** The simulation-step trace shall retain each original functional LLM output, validation errors, repair output when attempted, and final disposition.

**LLM-009:** When calling the local Gemma model for a functional LLM role, the model gateway shall request `chat_template_kwargs.enable_thinking=false` and shall treat absent or invalid `message.content` as a failed functional output rather than using `reasoning_content` as the result.

**LLM-010:** The initial local model gateway shall accept an explicit base URL, model identifier, positive request timeout, positive completion-token limit, and injectable synchronous HTTP client or transport; it shall not read machine-specific configuration inside simulation or actor-domain logic.

**LLM-011:** Each functional request shall use the configured model, temperature zero, the configured completion-token limit, `response_format={"type":"json_object"}`, and `chat_template_kwargs={"enable_thinking":false}`, and shall include the caller's messages plus a deterministic compact JSON Schema instruction derived from the requested strict Pydantic output model.

**LLM-012:** A functional attempt shall be accepted only from an HTTP 200 response with one selected choice whose `finish_reason` is `stop` and whose non-blank `message.content` strictly validates as the requested Pydantic model; no other response field, including `reasoning_content`, shall be used as candidate output.

**LLM-013:** Empty content, a non-`stop` finish reason, invalid JSON, or strict schema-validation failure shall cause exactly one repair request using the same original messages, schema, request settings, failed content, and normalized validation errors; failure of the repair shall return a failed result without further calls or best-effort extraction.

**LLM-014:** Transport failure, non-200 HTTP status, or malformed provider response structure shall return a typed failed result without a repair request, without exposing provider response bodies or transport exception text as accepted model output.

**LLM-015:** Every functional call result shall be strict and immutable and shall contain its final disposition, accepted typed value only on success, and ordered initial and optional repair attempt evidence including content, finish reason, failure kind, and validation errors.

**LLM-016:** The shared gateway shall not choose player clarification, NPC fallback, or System-director skip behavior, construct action submissions, mutate or persist simulation state, or write traces; role-specific callers and later coordination own those actions using the gateway's typed disposition and evidence.

**LLM-017:** A gateway shall close only an HTTP client it created and shall leave an injected client open for its owner.

### Development inspection

**INSPECT-001:** The initial version shall provide a Streamlit development inspection page separate from the player interface.

**INSPECT-002:** The inspection page shall be read-only with respect to canonical world and character state.

**INSPECT-003:** The inspection page shall present simulation steps as an ordered timeline with player interpretation, scheduler ordering, context manifests, functional LLM outputs, validation results, random draws, canonical events, state transitions, observations, narration, and System notifications when present.

**INSPECT-004:** The inspection page shall allow comparison of canonical world state with a selected character's perception snapshot for the same committed simulation step.

**INSPECT-005:** The inspection page shall expose stable identifiers and provenance needed to trace information between stages.

**INSPECT-006:** World reset shall remain a separate explicit development operation and shall not be performed through direct state editing on the inspection page.

### Documentation and delegated context

**DOC-001:** Each durable documentation artifact shall have one primary information-ownership role so orientation, normative contracts, architecture, planning, execution, and historical evidence remain distinguishable.

**DOC-002:** README shall be a concise human landing page for project purpose, current status, setup, repository orientation, and documentation routing rather than a duplicate reference for detailed domain contracts.

**DOC-003:** The domain guide shall provide non-normative conceptual orientation and shall link to canonical vocabulary, requirements, decisions, and design instead of replacing or restating their detailed contracts.

**DOC-004:** Every Ready delegated task shall route exact pre-code documentation extracts, record their approximate word budget, and justify exceeding the initial soft limit of 8,000 words rather than silently loading whole canonical documents.

**DOC-005:** Delegated implementation shall exclude human-orientation, planning, continuation, review, and completed-task artifacts by default, and its handoff shall identify the bounded documentation and initial source or test context actually used.

**DOC-006:** Repository-wide agent instructions shall route each substantial activity to exactly one responsibility-specific guide for architecture and integration, implementation, or independent review, and delegated task briefs shall name the selected guide explicitly.

### Development foundation

**DEV-001:** The initial application shall target Python 3.12 and shall reject installation on a different Python minor version.

**DEV-002:** The project shall use `uv` to create its development environment and shall commit `uv.lock` so the declared environment can be reproduced.

**DEV-003:** The Python distribution `llm-system` shall expose its import package from `src/llm_system` rather than from the repository root.

**DEV-004:** The initial scaffold shall use Hatchling as its build backend and shall contain no application runtime dependencies before a feature requires them.

**DEV-005:** The project shall provide Make targets named `install`, `test`, `format`, `format-check`, `lint`, `mypy`, and `check` as the stable local and delegated-agent development interface.

**DEV-006:** When `make check` is run against the initial scaffold, it shall verify formatting, linting, static types, and tests without requiring the local LLM, embeddings service, Qdrant, FastAPI, or Streamlit.
