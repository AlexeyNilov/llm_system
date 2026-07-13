# TASK-021: Define observation and perception-snapshot contracts

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-012, TASK-014

## Objective

Provide strict immutable value contracts for the initial typed observations and actor-specific perception snapshots, establishing what filtered information can look like without implementing perceptual filtering.

These contracts represent transient deterministic projections. They do not decide what an actor can perceive, enrich IDs into presentation context, record durable memory, or generate narrative.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Event”, “Object placement”, “Observation”, “Perception engine”, “Perceptual filtering”, and “Perception snapshot”
* `doc/requirements.md`: `SPACE-004` through `SPACE-006`, `KNOW-001`, `KNOW-002`, `EVENT-003`, `EVENT-004`, and `PERCEPTION-001` through `PERCEPTION-014`
* `doc/decisions.md`: “Agents receive bounded context”, “Model space as a location graph with deterministic perception”, “Separate truth, perception, memory, and belief”, “Use an explicit cognition and action loop”, “Retain typed canonical events without full event sourcing”, and “Begin perception with typed deterministic observation values”
* `doc/high_level_design.md`: “Perception engine”, “Principal records”, “Actor loop”, and “Testing strategy”
* `src/llm_system/simulation/_types.py`, `src/llm_system/simulation/state.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/__init__.py`, `tests/test_runtime_state.py`, `tests/test_events.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* Implement strict frozen Pydantic contracts using existing `AuthoredId`, `_StrictContract`, `NonNegativeSeconds`, `ObjectPlacement`, and `CanonicalEvent` types rather than parallel primitives or payload dictionaries.
* The public observation variants are exactly `LocationObserved`, `ConnectionObserved`, `CharacterObserved`, `ObjectObserved`, and `EventObserved`.
* Every observation contains `observer_id: AuthoredId`, `observed_at_seconds: NonNegativeSeconds`, and its fixed `observation_type` and `source_type` literals.
* `LocationObserved` has `observation_type="location"`, `source_type="current_state"`, and `location_id: AuthoredId`.
* `ConnectionObserved` has `observation_type="connection"`, `source_type="current_state"`, `connection_id: AuthoredId`, and strict `is_available: bool`.
* `CharacterObserved` has `observation_type="character"`, `source_type="current_state"`, and `character_id: AuthoredId`.
* `ObjectObserved` has `observation_type="object"`, `source_type="current_state"`, `object_id: AuthoredId`, and `placement: ObjectPlacement`.
* `EventObserved` has `observation_type="event"`, `source_type="canonical_event"`, and `event: CanonicalEvent`. Construction rejects an event whose `occurred_at_seconds` is greater than `observed_at_seconds`; equality and observation of earlier events are valid.
* Public `Observation` is the closed annotated union of those five variants discriminated by `observation_type`.
* Public `PerceptionSnapshot` contains `observer_id: AuthoredId`, `perceived_at_seconds: NonNegativeSeconds`, and `observations: tuple[Observation, ...]`.
* Snapshot construction requires every observation's `observer_id` to equal the envelope observer and every `observed_at_seconds` to equal envelope time. Report a non-blank validation error when either invariant fails; context-free construction does not aggregate issue records.
* Snapshot observations normalize only exact input lists or tuples to immutable tuples, matching current runtime collection behavior. Empty tuples and exact duplicate values are structurally valid, and supplied order is preserved.
* The models perform no package or world lookup, reference validation, visibility decision, co-location check, connection-direction check, possession-visibility inference, ordering policy, deduplication, definition enrichment, persistence, memory creation, belief revision, narration, or LLM call.
* Observation payloads contain no authored names, descriptions, endpoints, traversal durations, archetypes, goals, plans, unrestricted definitions, observation UUIDs, confidence, or salience.
* No common public observation base, durable observation record, engine interface, enrichment interface, ID provider, score type, service class, or new dependency is introduced.
* This contract milestone advances the project version from `0.19.0` to `0.20.0`; the lockfile's editable root-package version must match.

## In scope

* Add the five exact observation variants, closed `Observation` union, and exact `PerceptionSnapshot`, and expose all seven names from `llm_system.simulation`.
* Add high-signal behavioral tests for every variant's exact typed payload and provenance, event-time consistency, snapshot observer/time consistency, empty snapshots, list-to-tuple normalization, order and duplicate preservation, strict ID-linked payload boundaries, and immutable inputs/values where behavior is introduced here.
* Update README with the transient observation variants, snapshot invariants, event-time rule, ID-linked payload boundary, and explicit exclusions from filtering, enrichment, persistence, memory, scoring, and narration.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Deterministic perception-engine behavior, observer lookup, current-location projection, outgoing-connection selection, entity co-location, object visibility, event visibility, sensory limitations, environmental facts, attention, confidence, or salience.
* Restricted definition enrichment, narrator or NPC context assembly, prompts, LLM invocation, presentation prose, or Streamlit/API work.
* Durable observation identity or persistence, episodic memory, belief state, memory retrieval, Qdrant, or SQLite.
* New canonical-event, runtime-state, package-definition, entity, action, outcome, or state-change fields or variants.
* Generic observation payloads, arbitrary metadata, public base classes, ID generation, score placeholders, registries, protocols, or service objects.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, high-level design, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/perception.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_perception_contracts.py`.

The seven new public names are exactly `LocationObserved`, `ConnectionObserved`, `CharacterObserved`, `ObjectObserved`, `EventObserved`, `Observation`, and `PerceptionSnapshot`.

## Acceptance criteria

1. Each of the five strict frozen observation variants preserves its exact observer, time, fixed discriminator/provenance, and accepted ID-linked payload (`PERCEPTION-001` through `PERCEPTION-006`).
2. `Observation` discriminates all and only the five accepted variants without an arbitrary payload escape hatch (`PERCEPTION-001`, `PERCEPTION-002`).
3. Event observation accepts same-time and past canonical events but rejects future events without changing the supplied event (`PERCEPTION-004`, `PERCEPTION-009`).
4. Perception snapshots preserve empty or populated ordered immutable tuples, normalize exact lists, and retain exact duplicates without deduplication (`PERCEPTION-007`, `PERCEPTION-010`, `PERCEPTION-011`).
5. Snapshot construction rejects any contained observation whose observer or time differs from its envelope, while accepting a consistent heterogeneous tuple (`PERCEPTION-008`).
6. Construction performs no world lookup or reference validation and introduces none of the excluded names, definitions, generated identities, scores, filtering, enrichment, persistence, memory, or narrative behavior (`PERCEPTION-006`, `PERCEPTION-011` through `PERCEPTION-014`).
7. Public exports and README accurately describe the transient contracts and their future boundaries.
8. Existing state, event, package, resolver, dispatch, commitment, and authorization behavior remains unchanged.
9. Project and installed metadata plus editable root `uv.lock` report `0.20.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production contract logic; record the import or missing-contract failure.
* Run focused perception-contract tests after variant, event, and snapshot groups.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.19.0` to `0.20.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires world-aware filtering, another observation variant, a different payload or provenance field, durable identity, confidence or salience semantics, enrichment, persistence, memory or belief behavior, an engine or service interface, a dependency, or existing contract changes.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
