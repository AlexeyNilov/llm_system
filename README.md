# llm_system

An experimental persistent simulation in which a human player and autonomous NPCs perceive limited information, act through explicit rules, remember consequences, and interact through an LLM-assisted narrative interface.

The project is designed as a practical laboratory for information architecture, context engineering, agentic systems, and local LLM-assisted programming.

## Development setup

Prerequisites: Python 3.12 and [uv](https://docs.astral.sh/uv/).

Create the locked development environment:

```bash
make install
```

Use the Make interface for local verification:

```bash
make test
make format
make format-check
make lint
make mypy
make check
```

`make check` verifies formatting, linting, static types, and tests. It does not require any local model or service to be running.

## Game-package manifests

Versioned authored packages live outside Python code:

```text
game_packages/
  rules/<package-id>/<package-version>/manifest.yaml
  scenarios/<package-id>/<package-version>/manifest.yaml
```

Use `llm_system.game_packages.load_game_package()` to safely load one complete,
strict immutable game package. It validates the manifest and its YAML entrypoint
atomically, validates package identity against the directory, and returns either a
`LoadedRulePackage` pairing `RulePackageManifest` with `RulePackDefinition` or a
`LoadedScenarioPackage` pairing `ScenarioPackageManifest` with
`ScenarioPackDefinition`. The validated manifest type is the sole selector for
the entrypoint schema, and every loading failure is reported through
`GamePackageLoadError`.

Loading one scenario preserves its exact required-rule-pack reference but does
not locate or resolve that dependency. Duplicate and cross-package references,
graph invariants, compatibility, supported operations, and playability remain
semantic validation responsibilities outside this structural loading boundary.

## Greybridge content foundation

The repository includes the schema-version-1 Greybridge package pair with its
first authored Use foundation, while retaining the compatible `0.1.0` pair:

```text
game_packages/rules/greybridge-rules/0.2.0/
game_packages/scenarios/storm-at-greybridge/0.2.0/
```

Schema version 1 represents typed reference catalogs, reusable object-use
mechanics, authored spatial topology and entities, and concrete scenario
bindings to boolean world facts. Load both repository directories and validate
the pair through the public boundary:

```python
from pathlib import Path

from llm_system.game_packages import load_game_package, validate_game_packages

repository_root = Path.cwd()  # Run this from the repository root.
rules = load_game_package(
    repository_root / "game_packages/rules/greybridge-rules/0.2.0"
)
scenario = load_game_package(
    repository_root / "game_packages/scenarios/storm-at-greybridge/0.2.0"
)
validated = validate_game_packages(rules, scenario)
```

The rule pack authors the reusable `reinforce-structure` mechanic; the scenario
binds it to concrete reinforcement materials, Greybridge Span, and the
`bridge-reinforced` fact. This makes the mechanic representable but does not
resolve or dispatch a Use proposal, initialize runtime state, consume an object,
or trigger flood, progression, scheduling, perception, or presentation behavior.

## Game-package semantic validation

Use `llm_system.game_packages.validate_game_packages()` with one
`LoadedRulePackage` and one `LoadedScenarioPackage` to establish their
relational validation boundary. It returns a frozen `ValidatedGamePackages`
pair preserving those loaded inputs, or raises `GamePackageValidationError`
with an ordered immutable tuple of structured `ValidationIssue` records.

Validation aggregates independent dependency, namespace-uniqueness, typed
reference, object-archetype agreement, binding ambiguity, player-count,
self-loop, and topology defects while gating checks
whose prerequisites are invalid. A scenario's rule-package pin must match
exactly. Every authored location must be reachable by directed connections from
the one player's valid start; reverse reachability is not required, and
parallel directed connections with distinct IDs are valid.

`ValidatedGamePackages` does not establish policy implementation availability,
supported operations, persistent-world compatibility, playability, or
world-creation readiness. Those remain later explicit validation boundaries.

## Actor action contracts

`llm_system.simulation` exposes strict, immutable structured-output contracts
for the seven initial actor operations: observe, move, speak, take, use, help,
and wait. An `ActorActionProposal` is deliberately an untrusted payload with
only an operation and its typed arguments. It has no actor identity, proposal
identity, provenance, intent, or reasoning fields.

The application creates an `ActorActionSubmission` around that payload with
injected UUID proposal, simulation-step, and decision-context identities; the
intended actor; and either player-interpreter or NPC-policy provenance. For
example:

```python
from uuid import uuid4

from llm_system.simulation import (
    ActorActionSubmission,
    PlayerInterpreterActionSource,
    WaitActionProposal,
)

submission = ActorActionSubmission(
    proposal_id=uuid4(),
    simulation_step_id=uuid4(),
    decision_context_id=uuid4(),
    source=PlayerInterpreterActionSource(
        source_type="player_interpreter",
        interpreter_id="local-parser",
    ),
    actor_id="marin",
    proposal=WaitActionProposal(operation="wait", duration_seconds=30),
)
```

These are contracts, not executable actions or proof of authority. They do not
resolve references, mutate state, produce outcomes or events, or define
world-action and scheduled-activity submissions.

## Scheduled-activity contracts

`llm_system.simulation` exposes a closed `ScheduledActivity` union of strict,
immutable `EnvironmentalScheduledActivity`, `NpcScheduledActivity`, and
`SystemDirectorScheduledActivity` records. Each record is one application-
identified runtime occurrence with a required UUID `activity_id`, non-negative
integer `eligible_at_seconds`, and caller-assigned non-negative integer
`insertion_sequence`. Environmental records reference an authored `schedule_id`,
NPC records identify an authored `npc_id`, and System-director records reference
an authored `hook_id`.

These are one-shot eligibility records, not recurring schedule definitions or
executable payloads. They contain no callback, proposal, outcome, mechanic
arguments, cancellation state, or stored phase priority. The scheduler derives
phase order from the variant as environmental, NPC, then System director and
derives execution order separately from queue storage order.

`ScheduledActivityQueue` contains exactly an immutable ordered tuple of those
records. It accepts Python tuples or serialized JSON/YAML-style lists, normalizes
lists to tuples, allows an empty queue, and preserves deliberately unsorted
supplied order. Activity UUIDs and insertion sequences must each be unique;
eligibility times may be equal. Construction validates only these structural
invariants and does not resolve authored schedule, NPC, or hook references.
Use `llm_system.simulation.select_eligible_activities(world, queue)` to
partition one validated queue at the world's exact canonical simulation time.
Overdue and exactly due records are returned in `eligible_activities`, ordered
by `(eligible_at_seconds, derived_phase_rank, insertion_sequence)`. Strictly
future records remain in their original storage order in `remaining_queue`.
The strict immutable `ScheduledActivitySelection` validates that temporal
partition, eligible ordering, and activity-ID and insertion-sequence uniqueness
across both groups.

Selection retains the exact activity objects and never mutates either input. If
nothing is eligible it also reuses the exact input queue; otherwise it creates a
new remaining queue, including an empty one when all work is due. This pure
boundary does not claim, persist, execute, retry, recur, or cancel work; mutate
or advance the world; resolve package references; submit proposals; invoke an
LLM; or process activities created by later execution.

## Recorded integer draws

Use `llm_system.simulation.draw_recorded_integer()` with an application-created
`IntegerDrawRequest` and an injected structural `IntegerRandomSource`. The
request supplies a UUID draw identity, an extensible lowercase kebab-case
purpose, and a strict signed inclusive integer range containing at least two
possible results. The source receives only those bounds through one keyword-only
call.

A valid source result produces an immutable `IntegerDrawRecord` preserving the
request metadata exactly. A boolean, non-integer, or out-of-range result raises
`RandomSourceContractError` without coercion, clamping, or retry. Exceptions
raised by the source propagate unchanged, and the boundary generates no
identity.

This is the arbiter-facing randomness primitive and audit value only. It does
not provide a concrete generator, seed or generator-state persistence, rule
checks, outcomes, events, history or trace attachment, logging, or LLM
integration.

## Actor-action authorization

Use `llm_system.simulation.authorize_actor_action()` to bind a trusted
`ActorActionSubmission` source to its intended authored character before later
operation dispatch. Success returns a frozen `AuthorizedActorAction` preserving
the exact validated world and submission objects. Failure raises
`ActorActionAuthorizationError` with a non-empty immutable tuple of structured
issues.

A player-interpreter source may submit only for the one authored player
character. Its interpreter identity is retained as trusted application-created
provenance; this boundary does not check an interpreter registry or allowlist.
An NPC-policy source must identify the intended actor, that actor must be an
authored NPC, and the source policy identity must exactly match the NPC's
configured decision policy. Unknown actors stop source-specific checks, and NPC
source identity mismatches stop actor-type and policy checks.

Authorization establishes source authority only. It does not inspect proposal
targets, current location, connection availability, possession, current
actionability, simulation-step or decision-context identities, or policy
implementation type. It also does not dispatch or resolve operations, generate
outcomes, commit state, interpret events, invoke an LLM, or authorize world
actions and scheduled activities.

## Wait resolution

Use `llm_system.simulation.resolve_wait()` with an `AuthorizedActorAction` whose
proposal is `WaitActionProposal`. The caller must inject keyword-only UUID
values for `outcome_id` and `event_id`; the resolver does not generate runtime
identities. It returns one `SucceededOutcome` with reason `wait-completed`, the
submission's proposal identity, and completion time equal to current simulation
time plus the requested duration.

The outcome contains exactly one `SimulationTimeChanged` from current time to
completion time and one `ActorWaitedEvent` at completion identifying the actor,
requested duration, supplied event identity, and supplied outcome identity as
its cause. Passing an authorized non-Wait action is a programmer error and
raises `TypeError` rather than producing a canonical rejection.

Wait resolution is a pure evidence-producing boundary. Pass its outcome
separately to `commit_outcome()` to advance canonical simulation time. The
resolver does not commit state or process scheduled activities or NPC actions
made eligible by elapsed time; scheduler processing remains a later, separate
operation.

## Move resolution

Use `llm_system.simulation.resolve_move()` with an `AuthorizedActorAction` whose
proposal is `MoveActionProposal`. The caller must inject keyword-only UUID
values for `outcome_id` and `event_id`; the resolver generates no identities.
Passing an authorized non-Move action raises `TypeError` as a programmer error.

The resolver first finds the proposal's directed connection in authored
scenario topology, then reads the actor's current location and that connection's
runtime availability from the validated world. Actionability is gated in this
exact order: unknown authored connection, actor not at the connection source,
then unavailable runtime connection. The respective effect-free rejections use
reasons `unknown-connection`, `actor-not-at-connection-source`, and
`connection-unavailable` at the current simulation time. A rejected call does
not use its supplied event identity.

Valid movement always succeeds with reason `move-completed`. Completion time is
the current simulation time plus the authored connection's exact positive
integer `base_traversal_seconds`, without modifiers or an artificial maximum.
The outcome contains exactly two ordered changes—`CharacterLocationChanged`
from source to destination followed by `SimulationTimeChanged` to completion—
and one `ActorMovedEvent` at completion using the supplied event identity and
the supplied outcome identity as its cause.

Move resolution only produces typed evidence. Pass the outcome separately to
`commit_outcome()` to update canonical location and time. The resolver does not
commit state, dispatch operations, process scheduler eligibility or NPC
activity, interpret traversal requirements, generate IDs, or perform
perception, persistence, or presentation.

## Observe resolution

Use `llm_system.simulation.resolve_observe()` with an `AuthorizedActorAction`
whose proposal is `ObserveActionProposal`. The caller injects keyword-only UUID
values for `outcome_id` and `event_id`; passing an authorized non-Observe action
raises `TypeError` as a programmer error.

The resolver projects the actor's current perception through
`project_current_perception()`. Surroundings are always perceptible after that
projection. A location, connection, character, or object target succeeds only
when the snapshot contains the corresponding typed current-state observation
with the same typed identifier. This includes unavailable outgoing connections.
Unknown, remote, incoming-only, self-character, wrong-namespace, and otherwise
absent targets all produce the same effect-free `RejectedOutcome` with reason
`target-not-perceptible`, without disclosing whether canonical truth contains
the target or using the supplied event identity.

Success uses reason `observation-completed` at the exact current simulation
time, changes no state, advances no time, and contains exactly one
`ActorObservedEvent` with the proposal's exact typed target and caller-supplied
identities. Observe v0 performs no rich inspection, search, capability or skill
check, uncertainty, enrichment, event-feedback filtering, recording, memory,
belief, persistence, narration, or presentation.

## Speak resolution

Use `llm_system.simulation.resolve_speak()` with an `AuthorizedActorAction`
whose proposal is `SpeakActionProposal`. The caller injects keyword-only UUID
values for `outcome_id` and `event_id`; passing an authorized non-Speak action
raises `TypeError` as a programmer error.

Speak v0 treats only another character at the authorized speaker's exact
canonical runtime location as audible. Unknown, remote, self, object,
connection, location, and otherwise absent recipient identifiers all produce
the same effect-free `RejectedOutcome` with reason `recipient-not-audible`,
without disclosing whether the identifier exists in another namespace or using
the supplied event identity. Audibility does not reuse visual perception.

Success uses reason `speech-completed` at the exact current simulation time,
changes no state, advances no time, and contains exactly one `ActorSpokeEvent`
with the authorized speaker, proposal recipient, exact unnormalized utterance,
and caller-supplied identities. It establishes only audible addressed speech;
it does not establish comprehension, memory, belief, agreement, response, or
recipient state change and does not produce recipient event feedback.

## Take resolution

Use `llm_system.simulation.resolve_take()` with an `AuthorizedActorAction`
whose proposal is `TakeActionProposal`. The caller injects keyword-only UUID
values for `outcome_id` and `event_id`; passing an authorized non-Take action
raises `TypeError` as a programmer error.

Take v0 reads canonical runtime character and object state directly. An object
is accessible only when its exact current placement is directly at the
authorized actor's exact current location. Unknown, remote, actor-possessed,
other-character-possessed, location, connection, character, and otherwise
inaccessible identifiers all produce the same effect-free `RejectedOutcome`
with reason `object-not-accessible`, without disclosing which condition applied
or using the supplied event identity. Authored initial placement and perception
do not authorize acquisition.

Success uses reason `object-taken` at the exact current simulation time and
advances no time. It contains exactly one `ObjectPlacementChanged` from the
exact current `ObjectAtLocation` placement to `ObjectPossessedByCharacter` for
the actor, plus one `ObjectTakenEvent` with the same previous placement and the
caller-supplied identities. Pass the outcome separately to `commit_outcome()`
to update canonical state.

Take v0 does not implement transfer, giving, dropping, theft, consent,
permission, carrying capacity, weight, checks, duration, object-specific rules,
reactions, persistence, narration, or presentation. The resolver itself does
not produce witness feedback; immediate Take witnessing is a separate
perception projection.

## Actor-action dispatch

Use `llm_system.simulation.dispatch_actor_action()` after authorization to route
one `AuthorizedActorAction` by its concrete proposal type. The caller supplies
required keyword-only UUID values for `outcome_id` and `event_id`; dispatch
generates no identities. Move, Wait, Observe, Speak, and Take proposals route to
their corresponding concrete resolvers, and the selected resolver's outcome is
returned without reconstruction or exception translation. Caller identities
and the authorized action pass through unchanged.

Use and Help are structurally valid proposals whose mechanics are not yet
implemented. Dispatch raises `OperationResolverUnavailableError` for each, with
its public typed `operation` attribute identifying the unavailable capability.
This is a software-capability error, not a rejected or failed canonical outcome.

Dispatch does not authorize submissions, commit outcomes, process scheduler
eligibility, invoke NPC policies or an LLM, perform perception or presentation,
access persistence, or provide configurable resolver registration. Authorization,
operation-specific resolution, and commitment remain separate boundaries.

## Runtime-state contracts

`llm_system.simulation` also exposes strict, immutable runtime-state contracts
for the minimal changing facts in a canonical snapshot: simulation time,
character locations, object placement or possession, connection availability,
and strict boolean world facts. The snapshot is an ID-linked overlay on immutable package
definitions; it does not copy authored names, topology, durations, archetypes,
goals, plans, or package identity.

```python
from llm_system.simulation import BooleanWorldFactState, CharacterState, WorldState

state = WorldState(
    simulation_time_seconds=0,
    characters=(CharacterState(character_id="marin", location_id="waystation"),),
    objects=(),
    connections=(),
    boolean_world_facts=(
        BooleanWorldFactState(fact_id="bridge-reinforced", value=False),
    ),
)
```

Structural construction permits empty collections, duplicates, and unresolved
but well-shaped references. It is not proof that the snapshot is world-ready:
package-aware completeness, uniqueness, and reference validation belong to a
separate boundary.

## State-change and canonical-event contracts

State changes and canonical events are separate public leaf contracts.
`StateChange` is a closed union of self-verifying snapshot deltas:
`CharacterLocationChanged`, `ObjectPlacementChanged`,
`ConnectionAvailabilityChanged`, `BooleanWorldFactChanged`, and
`SimulationTimeChanged`. Each delta records explicit before and after values and
rejects a no-op; object changes reuse the runtime `ObjectPlacement` variants.

`CanonicalEvent` is durable factual history, not a mutation command. Its closed
initial union contains `ActorObservedEvent`, `ActorMovedEvent`,
`ActorSpokeEvent`, `ObjectTakenEvent`, `ObjectUsedEvent`, `ActorHelpedEvent`,
`ActorWaitedEvent`, and `ActorActionFailedEvent`. Every event requires
application-supplied event and outcome UUIDs plus its non-negative occurrence
time. Target and placement payloads reuse the existing typed contracts, and
failed actions reuse the public seven-value `ActorActionOperation` vocabulary.

`Outcome` aggregates those leaves as a strict immutable union with separate
`RejectedOutcome`, `FailedOutcome`, and `SucceededOutcome` variants. Every
variant requires application-supplied outcome and proposal UUIDs, one atomic
completion time, and a formatted resolver-owned reason code. Rejection means
the proposal was not attempted and structurally has no effect fields. Failure
means a valid attempt did not achieve its goal, while success means it did;
both valid-attempt variants require callers to supply explicit state-change and
event tuples, even when either tuple is intentionally empty.

Outcome construction guarantees that nested events share the outcome identity
and completion time, event IDs are unique within the outcome, and no affected
character location, object placement, connection availability, boolean fact, or
simulation time appears in more than one state change. It does not apply changes, inspect
a world snapshot or proposal, validate before values or time deltas, infer
agreement between changes and events, resolve references, authorize sources,
or commit effects. Those state-dependent guarantees belong to the simulation
arbiter. Events also contain no visibility, observer, or narration decisions;
those remain perception and presentation concerns.

## Observation and perception-snapshot contracts

`llm_system.simulation` exposes five strict immutable transient observation
variants: `LocationObserved`, `ConnectionObserved`, `CharacterObserved`,
`ObjectObserved`, and `EventObserved`. Their closed `Observation` union carries
one observer ID, one observation time, and fixed provenance. Current-state
variants retain only authored IDs plus the perceived mutable fact where needed:
connection availability or typed object placement. Event observations preserve
the exact typed `CanonicalEvent` and reject an event from later than the
observation time; same-time and earlier events are valid.

`PerceptionSnapshot` groups an ordered immutable tuple of these observations for
one observer at one simulation time. Every observation must match the snapshot's
observer and time. Empty snapshots and exact duplicates are valid, input lists
normalize to tuples, and supplied order is preserved.

These values are ID-linked projections, not copies of package definitions or
proof that perceptual filtering occurred. Construction performs no world lookup,
visibility decision, definition enrichment, ordering, or deduplication. It also
does not generate durable observation identities, persist observations, create
memories, score confidence or salience, produce narration, or invoke an LLM.
Those responsibilities remain separate filtering, restricted enrichment,
recording, cognition, and presentation boundaries.

## Current-state perception projection

Use `llm_system.simulation.project_current_perception()` with a
`ValidatedWorldState` and an authored character ID to produce the exact
current-state `PerceptionSnapshot` available to that observer. The projection
uses canonical simulation time and returns observations in this fixed group
order: the observer's location, outgoing authored connections, co-located other
characters, then visible objects. Connections and entities preserve authored
package order rather than runtime-state tuple order.

All outgoing connections are included with their exact runtime availability;
incoming-only connections are excluded. The observer and remote characters are
excluded. Objects are included only when directly at the observer's location or
possessed by the observer. Remote objects and objects possessed by anyone else
remain excluded, including possessions of a co-located character.

An identifier absent from the runtime character namespace, including an object
identifier, raises `PerceptionObserverNotFoundError` with the supplied
`observer_id`. This pure deterministic boundary does not accept canonical
events or emit `EventObserved`, and it adds no sensory mechanics, definition
enrichment, recording, memory, belief, narration, persistence, or LLM behavior.

## Self-action event feedback projection

Use `llm_system.simulation.project_self_event_feedback()` with a
`ValidatedWorldState`, an authored character ID, and a caller-selected tuple of
canonical events to produce that character's self-action `EventObserved` tuple.
The speaker owns an `ActorSpokeEvent`; the actor owns each other initial event
variant. Recipients, assisted characters, targets, objects, possession, and
proximity do not imply ownership. Matching events retain their exact event
objects, input order, and duplicates and are observed at current canonical time.

Observer validation occurs before event timing is inspected. The entire candidate
batch is then validated in input order before ownership filtering, and the first
event later than current canonical time raises `FutureEventFeedbackError`, even
when another actor owns it. Past and current-time events are eligible.

This operation is a stateless event-observation fragment. The caller owns event
window selection and already-delivered tracking. It does not query event history,
deduplicate, determine witness visibility or audibility, compose current-state
observations or a `PerceptionSnapshot`, enrich or record observations, persist
delivery state, create memory or beliefs, narrate, or invoke an LLM.

## Addressed-speech event feedback projection

Use `llm_system.simulation.project_addressed_speech_feedback()` with a
`ValidatedWorldState`, an authored character ID, and a caller-selected tuple of
canonical events to produce exact speech events addressed to that character.
Only an `ActorSpokeEvent` whose committed `recipient_id` equals the observer
matches. Speaker ownership, other participant roles, possession, and proximity
do not make an event recipient feedback.

The projection validates the observer before inspecting event time, then
validates the entire batch in input order before filtering. Past and current-time
events are eligible; the first future event raises `FutureEventFeedbackError`
even when it is non-speech or addressed to someone else. Matching observations
use current canonical time and preserve exact event objects, input order, and
duplicates. Committed recipient identity is sufficient evidence of delivery at
occurrence time, so later movement and current visual perception are irrelevant.

This pure operation does not select an event window, track delivery, deduplicate,
compose self feedback or current-state perception, infer overhearing or general
witness audibility, record memory or belief, generate a response, persist data,
narrate, or invoke a policy or LLM. Those remain caller, coordinator, perception,
cognition, persistence, and presentation responsibilities.

## Speech-overhearing event feedback projection

Use `llm_system.simulation.project_speech_overhearing_feedback()` with a
`ValidatedWorldState`, an authored character ID, and a caller-selected tuple of
canonical events to produce immediate third-party speech feedback. Observer
validation occurs first. The entire batch must then occur at the world's exact
current simulation time; its first past or future event raises
`WitnessEventTimeMismatchError`, including non-speech or otherwise excluded
events.

After time validation, every `ActorSpokeEvent` speaker is resolved in input
order. The first absent speaker raises `SpeechSpeakerNotFoundError`, even when
the observer is the event's speaker or recipient or is remote. Recipient
existence and location are not revalidated because committed recipient identity
remains addressed-delivery evidence and is not needed for third-party
co-location.

An event matches only when the observer is neither speaker nor addressed
recipient and the speaker's exact current canonical location equals the
observer's. Matches retain exact event objects, input order, and duplicates and
use current canonical observation time. This pure projection does not accept
historical events, reconstruct locations, model comprehension or reactions,
add richer audibility, compose or deduplicate feedback, track delivery, record
memory or belief, persist data, narrate, or invoke a policy or LLM.

## Take-witness event feedback projection

Use `llm_system.simulation.project_take_witness_feedback()` with a
`ValidatedWorldState`, an authored character ID, and a caller-selected tuple of
canonical events to produce immediate Take-witness feedback. The projection
validates the observer first, then requires every event in the batch to occur at
the world's exact current simulation time. The first past or future event raises
`WitnessEventTimeMismatchError`, including a non-Take event or an event that
would not otherwise match.

Only an `ObjectTakenEvent` performed by another actor matches when its exact
committed `previous_placement` is `ObjectAtLocation` at the observer's current
canonical location. The previous placement supplies the event location; the
object's current placement and authored initial placement are not inspected.
The taking actor, remote observers, non-Take events, and events whose previous
placement is character possession are excluded. Matches retain exact event
objects, input order, and duplicates and use current canonical observation time.

This pure projection does not accept historical events, reconstruct historical
observer locations, apply richer visibility, select event windows, compose or
deduplicate feedback sources, track delivery, trigger reactions, record memory
or belief, persist data, narrate, or invoke a policy or LLM. Those remain later
caller, coordinator, perception, cognition, persistence, and presentation
responsibilities.

## Relational world-state validation

Use `llm_system.simulation.validate_world_state()` to compare one structural
`WorldState` with a `ValidatedGamePackages` pair. On success it returns a frozen
`ValidatedWorldState` that preserves both input objects and guarantees exactly
one runtime overlay for each authored character, object, connection, and boolean
world fact, plus
current location and object-possession references that resolve to authored
definitions.

```python
from llm_system.simulation import validate_world_state

validated_world = validate_world_state(validated_packages, state)
```

Failure raises `WorldStateValidationError` with an ordered immutable tuple of
structured runtime-state issues. This narrow relational boundary does not
initialize a world, supply default availability, validate policy implementations
or mechanics, establish persistence compatibility, or prove scenario playability.

## Outcome commitment

Use `llm_system.simulation.commit_outcome()` to commit an already resolved
`Outcome` against one `ValidatedWorldState`. The pure deterministic boundary
checks completion time, runtime targets, before values, and authored after-state
references before applying anything. Boolean deltas resolve against the fact
overlay and need no after-reference lookup. A successful change set produces one new
validated snapshot paired with the exact existing validated packages; unchanged
records retain identity and tuple order. Rejected and effect-free outcomes return
the exact input world, while the result always retains the exact supplied outcome
as trace evidence and leaves canonical events inside that outcome.

Invalid commitment raises one `OutcomeCommitError` containing all deterministic
structured issues and applies neither state changes nor events. Commitment does
not look up proposals or submissions, authorize sources, dispatch or resolve
operations, interpret event payloads as mutations, persist results, or prove
agreement between events and state changes.

## Scenario-pack definitions

`ScenarioPackDefinition` is the strict immutable content-schema-version-1 root
for scenario-pack entrypoints. It contains `spatial_graph`,
`entity_collection`, an authored-order `BooleanWorldFactDefinition` catalog,
and an authored-order `ObjectUseBindingDefinition` catalog. The two new catalogs
default to empty for compatible schema-version-1 content.

This contract does not load YAML entrypoints or perform relational validation.
Connection endpoints, entity placements, mechanic, fact, archetype and policy
references, uniqueness, graph invariants, and player-count requirements remain
deferred to semantic validation. Bindings are authored data, not executable
effects, conditions, callbacks, generic fact dictionaries, or resolver behavior.

## Rule-pack definitions

`RulePackDefinition` is the strict immutable content-schema-version-1 root for
rule-pack entrypoints. It contains authored-order catalogs of
`ObjectArchetypeDefinition`, `CharacterArchetypeDefinition`,
`DecisionPolicyDefinition`, and `ObjectUseMechanicDefinition`. The initial
mechanic contract declares one required object archetype, a location target,
positive integer duration, and the closed boolean-world-fact effect kind.

These definitions contain no executable callbacks, expressions, generic effect
payloads, conditions, randomness, consumption, quantities, or presentation.
Content loading, duplicate-ID validation, scenario-reference resolution, policy
implementation lookup, policy execution, and Use resolution remain separate.

## Spatial definitions

`LocationDefinition` models an authored location node and
`ConnectionDefinition` models one authored directed edge. Reverse travel needs a
separate connection definition. Each connection has an explicit positive
integer-second `base_traversal_seconds` duration.

`SpatialGraphDefinition` stores authored location and connection order as
immutable collections. These package definitions describe stable topology only;
mutable availability, conditions, visibility, and other runtime state belong to
later state models.

## Entity definitions

`EntityDefinition` is a strict immutable union of `ObjectDefinition`,
`PlayerCharacterDefinition`, and `NpcCharacterDefinition`. Objects reference an
object archetype and have one initial placement: either a location or a
possessing character, never both. Characters reference character archetypes and
start at a location.

NPC definitions additionally carry an identity summary, authored ordered goals,
an optional initial plan, and a rule, LLM, or hybrid decision-policy reference.
These are package definitions, not mutable runtime state. Duplicate identifiers,
player count, and location, possession, archetype, and policy-reference
resolution remain deferred to scenario validation.

## Documentation

* [High-level design](doc/high_level_design.md)
* [Domain glossary](doc/glossary.md)
* [Requirements](doc/requirements.md)
* [Architecture decisions](doc/decisions.md)
* [Initial scenario](doc/initial_scenario.md)
* [Agent workflow](doc/agent_workflow.md)
* [Roadmap](doc/roadmap.md)
* [Task template](doc/tasks/TASK_TEMPLATE.md)
* [Postponed ideas](doc/ideas.md)

## Local LLM setup: 
* QDRANT at http://localhost:6333 (in case we need RAG)
* EMBEDDINGS Model(v5-small-retrieval-Q8_0.gguf) at http://127.0.0.1:12346 (llama server)
* LLM_MODEL gemma-4-12b at http://127.0.0.1:12345 (another llama server)

## Fastapi and Streamlit chat example
* See /an/git/llmops/
* /home/lexa/an/git/llmops/src/llmops/use_cases/cognitive_map.py
