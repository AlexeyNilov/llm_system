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

The repository includes its first authored schema-version-1 package pair:

```text
game_packages/rules/greybridge-rules/0.1.0/
game_packages/scenarios/storm-at-greybridge/0.1.0/
```

Schema version 1 represents only typed reference catalogs, authored spatial
topology, entities, initial placement and possession, and NPC identity, goals,
plans, and policy references. Load both repository directories and validate the
pair through the public boundary:

```python
from pathlib import Path

from llm_system.game_packages import load_game_package, validate_game_packages

repository_root = Path.cwd()  # Run this from the repository root.
rules = load_game_package(
    repository_root / "game_packages/rules/greybridge-rules/0.1.0"
)
scenario = load_game_package(
    repository_root / "game_packages/scenarios/storm-at-greybridge/0.1.0"
)
validated = validate_game_packages(rules, scenario)
```

This is a validated content foundation, not a playable or world-ready scenario.
It does not encode Fieldcraft, actions, bridge condition or damage, perceptible
facts, flood scheduling, System director hooks, objectives, checks,
progression, or mutable runtime state.

## Game-package semantic validation

Use `llm_system.game_packages.validate_game_packages()` with one
`LoadedRulePackage` and one `LoadedScenarioPackage` to establish their
relational validation boundary. It returns a frozen `ValidatedGamePackages`
pair preserving those loaded inputs, or raises `GamePackageValidationError`
with an ordered immutable tuple of structured `ValidationIssue` records.

Validation aggregates independent dependency, namespace-uniqueness, typed
reference, player-count, self-loop, and topology defects while gating checks
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

## Actor-action dispatch

Use `llm_system.simulation.dispatch_actor_action()` after authorization to route
one `AuthorizedActorAction` by its concrete proposal type. The caller supplies
required keyword-only UUID values for `outcome_id` and `event_id`; dispatch
generates no identities. Move proposals route to `resolve_move()`, Wait proposals
route to `resolve_wait()`, and the selected resolver's outcome is returned
without reconstruction or exception translation. Caller identities and the
authorized action pass through unchanged.

Observe, Speak, Take, Use, and Help are structurally valid proposals whose
mechanics are not yet implemented. Dispatch raises
`OperationResolverUnavailableError` for each, with its public typed `operation`
attribute identifying the unavailable capability. This is a software-capability
error, not a rejected or failed canonical outcome.

Dispatch does not authorize submissions, commit outcomes, process scheduler
eligibility, invoke NPC policies or an LLM, perform perception or presentation,
access persistence, or provide configurable resolver registration. Authorization,
operation-specific resolution, and commitment remain separate boundaries.

## Runtime-state contracts

`llm_system.simulation` also exposes strict, immutable runtime-state contracts
for the minimal changing facts in a canonical snapshot: simulation time,
character locations, object placement or possession, and connection
availability. The snapshot is an ID-linked overlay on immutable package
definitions; it does not copy authored names, topology, durations, archetypes,
goals, plans, or package identity.

```python
from llm_system.simulation import CharacterState, WorldState

state = WorldState(
    simulation_time_seconds=0,
    characters=(CharacterState(character_id="marin", location_id="waystation"),),
    objects=(),
    connections=(),
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
`ConnectionAvailabilityChanged`, and `SimulationTimeChanged`. Each delta records
explicit before and after values and rejects a no-op; object changes reuse the
runtime `ObjectPlacement` variants.

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
character location, object placement, connection availability, or simulation
time appears in more than one state change. It does not apply changes, inspect
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

## Relational world-state validation

Use `llm_system.simulation.validate_world_state()` to compare one structural
`WorldState` with a `ValidatedGamePackages` pair. On success it returns a frozen
`ValidatedWorldState` that preserves both input objects and guarantees exactly
one runtime overlay for each authored character, object, and connection, plus
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
references before applying anything. A successful change set produces one new
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
for scenario-pack entrypoints. It has exactly two explicit aggregate sections:
`spatial_graph` with authored `locations` and `connections`, and
`entity_collection` with authored `entities`. Empty aggregates are structurally
valid; they do not establish a playable scenario.

This contract does not load YAML entrypoints or perform relational validation.
Connection endpoints, entity placements, archetype and policy references,
uniqueness, graph invariants, and player-count requirements remain deferred to
semantic validation. It also does not define events, director hooks, objectives,
or mechanics.

## Rule-pack definitions

`RulePackDefinition` is the strict immutable content-schema-version-1 root for
rule-pack entrypoints. It contains authored-order catalogs of
`ObjectArchetypeDefinition`, `CharacterArchetypeDefinition`, and
`DecisionPolicyDefinition`. Archetypes currently declare only a stable ID and a
non-blank name; decision policies additionally declare their `rule`, `llm`, or
`hybrid` type.

These definitions are reference catalogs, not executable mechanics. Content
loading, duplicate-ID validation, scenario-reference resolution, policy
implementation lookup, policy execution, and mechanics such as actions,
abilities, effects, or settings remain outside this initial schema.

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
