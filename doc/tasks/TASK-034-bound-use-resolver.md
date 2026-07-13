# TASK-034: Resolve bound object use

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-033, TASK-017, TASK-020

## Objective

Make the accepted authored Use capability executable through a pure deterministic resolver and the actor-action dispatcher. A Use succeeds only when the proposal selects one validated object-location binding, the actor carries that exact object at the bound location, and the bound boolean fact can change; it then advances authored time and records exact typed evidence.

This task completes the first package-governed object interaction without introducing a generic effects engine. Consumption, checks, flood consequences, witness feedback, and Help remain separate mechanics.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Boolean world fact”, “Canonical world state”, “Event”, “Object placement”, “Object-use binding”, “Object-use mechanic definition”, “Operation dispatch”, “Outcome”, “Simulation arbiter”, “Simulation time”, “State change”, “Validated game packages”, and “Validated world state”
* `doc/requirements.md`: `PACK-027` through `PACK-028`, `RULE-007` through `RULE-008`, `SCHEMA-001` through `SCHEMA-004`, `STATE-038` through `STATE-045`, `ACTION-006` through `ACTION-010`, `ACTION-017`, `ACTION-024` through `ACTION-042`, `USE-001` through `USE-012`, `DISPATCH-001` through `DISPATCH-010`, and `EVENT-001` through `EVENT-013`
* `doc/decisions.md`: “Separate the simulation kernel from game packages”, “Model runtime state as an ID-linked mutable-facts overlay”, “Distinguish rejected, failed, and succeeded outcomes”, “Retain typed canonical events without full event sourcing”, “Separate arbiter commitment from operation resolution”, “Introduce partial type-based actor-action dispatch”, “Begin Use mechanics with bound boolean-world-fact effects”, and “Resolve bound Use as a deterministic authored effect”
* `doc/high_level_design.md`: “Simulation arbiter”, “Principal records”, “Actor loop”, and “Testing strategy”
* `doc/initial_scenario.md`: “Package implementation stages” and the Greybridge `Use` interaction
* `src/llm_system/game_packages/rules.py`, `src/llm_system/game_packages/scenarios.py`, `src/llm_system/game_packages/validation.py`, `src/llm_system/simulation/actions.py`, `src/llm_system/simulation/authorization.py`, `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/commitment.py`, `src/llm_system/simulation/dispatch.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/resolvers/take.py`, `src/llm_system/simulation/resolvers/__init__.py`, `src/llm_system/simulation/__init__.py`, `tests/test_actor_action_dispatch.py`, `tests/test_take_resolver.py`, `tests/test_outcome_commitment.py`, `tests/test_greybridge_packages.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, `uv.lock`, and the Greybridge `0.2.0` package files

Do not read postponed ideas, unrelated requirements or decisions, experiments, perception-engine implementation, scheduling implementation, randomness, policies, prompts, persistence, other completed task briefs, or Help mechanics.

## Fixed assumptions

* Add public `resolve_use(action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID) -> RejectedOutcome | SucceededOutcome` in a focused resolver module.
* Passing an authorized action whose proposal is not `UseActionProposal` raises `TypeError` with stable non-blank text and produces no outcome.
* Authorization and world validation guarantee exactly one runtime state for the actor and every authored object and boolean fact. Validated package semantics guarantee resolved binding references, object-archetype agreement, and no duplicate concrete object-location binding. Do not revalidate those upstream invariants or turn their violation into an in-world rejection.
* Only `LocationTarget` is supported. Match one binding by the proposal's exact `(object_id, target.location_id)`. Connection, character, and object targets are uniformly inapplicable; do not reinterpret their identifiers as locations.
* Resolve the binding's exact mechanic from `RulePackDefinition.object_use_mechanics`. Use its authored `duration_seconds`; do not infer mechanics from names, object archetypes alone, scenario identity, or generated text.
* A matched Use is applicable only when the authorized actor's exact current location equals the binding target, the exact runtime object placement is `ObjectPossessedByCharacter` for that actor, and the exact runtime fact value differs from the binding target value.
* Unknown or unbound objects, non-location and unbound targets, remote actors, objects located in the world, objects possessed by another character, wrong-namespace identifiers, and facts already at their target value all return the same `RejectedOutcome` reason `use-not-applicable`. Do not reveal which authored or canonical condition applied.
* Rejection uses exact current simulation time, originating proposal identity, and supplied outcome identity. It has no effect fields, consumes no time, produces no event, and leaves `event_id` unused.
* Success uses reason `object-used` and completion time equal to current canonical time plus the matched mechanic's authored duration.
* Success contains exactly two ordered state changes: first `BooleanWorldFactChanged(change_type="boolean_world_fact", fact_id=binding.fact_id, from_value=current_fact.value, to_value=binding.fact_value)`, then `SimulationTimeChanged(change_type="simulation_time", from_seconds=current_time, to_seconds=completion_time)`.
* Success contains exactly one `ObjectUsedEvent` using supplied event and outcome identities, completion time, authorized actor ID, proposal object ID, and the proposal's exact `LocationTarget`. Preserve that exact typed target value; do not reconstruct it from the binding.
* Use v0 never returns `FailedOutcome`. The object remains possessed and unchanged; do not consume, move, destroy, quantify, damage, or replace it.
* `dispatch_actor_action` routes `UseActionProposal` directly to `resolve_use` with the exact action and supplied identities. Help alone remains unavailable through `OperationResolverUnavailableError`.
* Do not commit inside the resolver, process newly eligible scheduled activities, turn `bridge-reinforced` into a connection change, add flood consequences, perform perception or witness feedback, invoke an actor policy or LLM, generate progression, or perform presentation.
* Repeated resolution for equal inputs and caller identities returns equal outcomes and preserves the exact immutable authorized action, packages, world, submission, proposal, mechanic, binding, object state, fact state, and target.
* Prefer direct deterministic lookup helpers local to the resolver. Do not add a resolver registry, mechanic registry, generic effects interpreter, service class, caching layer, logging, or configuration.
* No new dependency or schema change is required.
* This public resolver milestone advances the project version from `0.32.0` to `0.33.0`; the lockfile's editable root-package version must match.

## In scope

* Add the exact bound Use v0 resolver and expose it from `llm_system.simulation`.
* Route Use through the existing actor-action dispatcher and retain the capability error for Help.
* Add high-signal behavioral tests for exact success changes and event; authored duration; binding selection; actor location and possession requirements; already-target fact rejection; unknown, unbound, unsupported-target, remote, other-possessor, and wrong-namespace uniform rejection; wrong-operation failure; dispatch pass-through; commitment compatibility; determinism; and input identity and immutability.
* Include one real Greybridge `0.2.0` integration case proving carried `reinforcement-materials` used at `greybridge-span` changes `bridge-reinforced` from false to true at current time plus 300 seconds. A compact synthetic validated world may cover the rejection matrix.
* Update README with implemented Use behavior, package lookup, time and effect semantics, uniform rejection, dispatch availability, and explicit exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* New package, action, authorization, state, state-change, outcome, event, commitment, scheduler, perception, or persistence contracts.
* Generic targets or effects; formulas, expressions, callbacks, scripts, registries, arbitrary properties or dictionaries; a second fact type; or content schema changes.
* Object consumption, removal, destruction, placement change, quantities, durability, costs, tools, capacity, transfer, ownership, checks, randomness, failure, interruption, repeated-use success, or progression.
* Flood-surge resolution, connection availability changes, scheduled-activity execution or selection, System director behavior, NPC policy execution, LLM calls, memory, belief, narration, UI, API, database, logging, or metrics.
* Use witness feedback or self-feedback changes, Help resolution, new unavailable-capability behavior, ID providers, generic resolver protocols, service classes, or dependencies.
* Modifying Greybridge package content or retained versions; the `0.2.0` pair is consumed as accepted input.
* Changes to requirements, decisions, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-034 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/resolvers/use.py`, with routing in `src/llm_system/simulation/dispatch.py` and public re-exports from `src/llm_system/simulation/resolvers/__init__.py` and `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_use_resolver.py`, with dispatch coverage updated in `tests/test_actor_action_dispatch.py`.

The one new public name is exactly `resolve_use`. Existing `UseActionProposal`, `LocationTarget`, `ObjectUseMechanicDefinition`, `ObjectUseBindingDefinition`, `ObjectPossessedByCharacter`, `BooleanWorldFactChanged`, `SimulationTimeChanged`, `ObjectUsedEvent`, outcome and commitment contracts, dispatch API, unavailable error, package validation, runtime state, scheduler, and perception behavior remain unchanged.

## Acceptance criteria

1. A proposal selecting one validated binding succeeds only when the authorized actor is at the bound location, possesses the exact object, and the exact bound fact can change (`USE-001`, `USE-003`).
2. Unknown, unbound, unsupported-target, remote, world-placed, other-character-possessed, wrong-namespace, and already-applied cases reject uniformly as `use-not-applicable`, without authored or canonical information disclosure (`USE-004`, `USE-005`).
3. Success resolves as `object-used` at current time plus exact authored duration and contains exactly ordered fact then time changes with exact before and after values (`USE-006`, `USE-007`).
4. Success contains exactly one `ObjectUsedEvent` with caller identities, completion time, authorized actor, proposal object, and the proposal's exact typed target; rejection leaves the event identity unused (`USE-005`, `USE-008`, `EVENT-009`).
5. The resolver uses only validated package definitions and canonical runtime overlays and contains no Greybridge identifiers, name matching, perception authority, randomness, or generated interpretation (`USE-001`).
6. Use has no failed branch, object change or consumption, check, progression, implicit bridge-connection effect, scheduled-activity execution, witness feedback, persistence, or presentation (`USE-009`, `USE-011`).
7. A non-Use authorized action raises `TypeError` and produces no in-world outcome (`USE-010`).
8. Dispatcher output for Use equals direct resolution with exact input and identity pass-through; Help retains its typed unavailable-capability error (`DISPATCH-003` through `DISPATCH-009`).
9. Committing a successful Use through the existing commitment core produces a validated replacement world with the bound fact changed and simulation time advanced while the object remains in exact actor possession; the resolver itself does not mutate or commit the input.
10. Repeated resolution is deterministic and preserves the immutable authorized action, validated packages, world, proposal, matched authored records, runtime records, and target (`USE-012`).
11. The real Greybridge `0.2.0` packages drive exact reinforcement behavior without package modification or scenario-specific Python logic.
12. Public exports and README accurately describe Use v0, authored binding selection, possession and co-location requirements, authored duration, uniform rejection, exact evidence, dispatch availability, and excluded consequences.
13. Existing package, world-validation, action, authorization, outcome, commitment, other resolver, perception, randomness, scheduler, and Help-dispatch behavior remains unchanged.
14. Project and installed metadata plus editable root `uv.lock` report `0.33.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing resolver and dispatch tests before production logic; record genuine red evidence.
* `uv run pytest tests/test_use_resolver.py tests/test_actor_action_dispatch.py tests/test_outcome_commitment.py tests/test_greybridge_packages.py tests/test_package.py -q`
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm installed metadata reports `0.33.0`.
* Confirm the only `uv.lock` change is editable root version `0.32.0` to `0.33.0`.
* Confirm the Greybridge `0.2.0` package files are unchanged.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires a new target or effect kind, package or runtime schema change, generic effect interpretation, object consumption or placement change, a failed or random-check branch, an implicit flood or connection consequence, scheduled-activity execution, witness feedback, Help mechanics, changing Greybridge content, a dependency, or public behavior not fixed above.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
