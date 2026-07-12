# TASK-011: Define actor action proposal and trusted submission contracts

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-010

## Objective

Provide strict immutable public contracts for the seven initial actor action proposal payloads and for trusted application-created actor-action submissions. Functional proposal producers must be able to return small operation-specific payloads without controlling runtime identity, actor authority, or provenance.

This task establishes contracts only. It does not validate an actor's authority, resolve references, mutate state, produce outcomes or events, or implement any operation.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Action”, “Action proposal”, “Action proposal submission”, “Actor”, “Decision policy”, “Intent”, “Simulation arbiter”, and “System director”
* `doc/requirements.md`: `ACTION-001` through `ACTION-005`, `ACTION-011` through `ACTION-023`, `LOOP-004` through `LOOP-005`, and `POLICY-001` through `POLICY-002`
* `doc/decisions.md`: “Use closed operation-specific action proposal contracts”, “Separate proposal payloads from trusted submission metadata”, “Use namespace-aware operation references and connection-based movement”, “Inject UUID runtime identities and type submission sources”, and “Defer concrete world-action proposals to their owning mechanics”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/game_packages/_types.py`, `src/llm_system/game_packages/entities.py`, `src/llm_system/game_packages/spatial.py`, `src/llm_system/game_packages/__init__.py`, `tests/test_entities.py`, `tests/test_spatial.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, completed task briefs, experiments, or implementation roadmap beyond this task.

## Fixed assumptions

* All new contracts are strict, frozen Pydantic 2 models that forbid unknown fields and do not generate identifiers or other defaults with hidden nondeterminism.
* Proposal payloads contain no proposal ID, simulation-step ID, source metadata, intended actor, intent, reasoning, outcome, event, or state mutation.
* The seven operation discriminator values are exactly `observe`, `move`, `speak`, `take`, `use`, `help`, and `wait`.
* `ActorActionProposal` is a closed discriminated union of exactly those seven payload variants.
* Observation targets are a closed discriminated union of surroundings, location, connection, character, and object target references. Surroundings is explicit and carries no domain identifier.
* Use targets are a closed discriminated union of location, connection, character, and object target references; surroundings is not a valid use target.
* Each non-surroundings target variant has a domain-specific identifier field rather than a generic `target_id` field.
* Move identifies `connection_id`; it does not accept a destination location.
* Speak identifies `character_id` and carries a non-blank utterance string.
* Take identifies `object_id`.
* Use identifies `object_id` plus one typed use target.
* Help identifies `character_id`.
* Wait contains only a strictly positive integer `duration_seconds` argument in addition to its discriminator.
* Authored domain references use the same lowercase kebab-case identifier behavior as existing package identifiers. Do not change existing package-model behavior merely to share an internal alias.
* Runtime `proposal_id`, `simulation_step_id`, and decision-context provenance use required `uuid.UUID` values supplied by the application. Models have no UUID factories.
* The initial actor submission source union contains exactly a player-interpreter source and an NPC-policy source. System-director and scheduled-activity sources belong to later world-action and scheduling contracts.
* Player-interpreter source provenance contains a required non-blank `interpreter_id` opaque application identifier.
* NPC-policy source provenance contains required `npc_id` and `policy_id` authored-domain identifiers.
* `ActorActionSubmission` contains the trusted proposal ID, simulation-step ID, decision-context ID, typed source, intended `actor_id`, and one `ActorActionProposal` payload.
* Source authorization, including agreement between NPC source identity and intended actor, belongs to the later simulation-arbiter task and must not be approximated with model validators here.
* Concrete world-action proposal or submission contracts are not introduced in this task.
* No new dependency is required.
* This public contract milestone advances the project version from `0.9.0` to `0.10.0`; the lockfile's editable root-package version must match.

## In scope

* Add a focused `llm_system.simulation` package for actor action proposal, target-reference, source-provenance, and trusted-submission contracts.
* Expose the intended contracts through the public `llm_system.simulation` package boundary.
* Add behavioral tests covering valid construction, union discrimination, serialization/schema suitability, domain constraints, strict rejection, immutability, and separation of untrusted payload from trusted metadata.
* Update README with the new public contract boundary, its trust split, current limitations, and a concise construction example.
* Update project version, root lockfile metadata, package-version test, and this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Runtime world state, state changes, outcomes, events, the simulation arbiter, operation resolvers, authority validation, reference resolution, clocks, scheduling, randomness, perception, persistence, APIs, or UI.
* Intent or reasoning models and changes to actor cognition.
* Concrete System-director, world-action, or scheduled-activity proposal contracts.
* Optional-objective, Fieldcraft, bridge, flood, progression, or other Greybridge mechanics.
* Generic argument dictionaries, generic target IDs, generic source-role records, executable callbacks, registries, or plugin mechanisms.
* Changes to existing game-package schemas or behavior.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production files are:

```text
src/llm_system/simulation/__init__.py
src/llm_system/simulation/actions.py
```

Names should make the following public concepts directly importable from `llm_system.simulation`:

* the seven operation-specific proposal models and `ActorActionProposal`;
* surroundings, location, connection, character, and object target-reference models plus the observation-target and use-target unions;
* player-interpreter and NPC-policy source models plus `ActorActionSource`; and
* `ActorActionSubmission`.

Keep aliases and implementation helpers private unless callers need them to construct or validate one of these contracts. Likely tests belong in `tests/test_actions.py`; inspect current naming patterns before choosing the exact file.

## Acceptance criteria

1. Each of the seven operation payloads validates only its accepted typed arguments and fixed discriminator, and `ActorActionProposal` discriminates all and only those variants (`ACTION-001`, `ACTION-002`, `ACTION-015` through `ACTION-019`).
2. Move requires a directed connection reference; Speak and Help require character references; Take requires an object reference; Use requires its object and a permitted typed target; Observe supports explicit surroundings or one permitted typed target (`ACTION-016` through `ACTION-018`).
3. Namespace-specific target variants cannot be substituted through a generic target identifier, and surroundings cannot be supplied as a Use target (`ACTION-015`, `ACTION-017`, `ACTION-018`).
4. Proposal payload models contain no trusted identity, intended-actor, provenance, intent, or reasoning fields and reject attempts to add them (`ACTION-011`, `ACTION-014`).
5. `ActorActionSubmission` requires application-supplied UUID proposal, simulation-step, and decision-context identities, one typed actor source, intended actor identity, and one valid proposal; repeated construction does not generate or change identity (`ACTION-012`, `ACTION-020`).
6. Player-interpreter and NPC-policy sources require their fixed source-specific provenance and reject fields belonging to another source variant (`ACTION-022`, `ACTION-023`).
7. Model construction does not perform source authorization or reference resolution, and no contract can mutate canonical state (`ACTION-013`, `LOOP-005`).
8. Every new contract is strict and immutable, rejects unknown fields and invalid identifier shapes or blank required text, and serializes deterministically into JSON-compatible data suitable for functional structured output.
9. Public imports are intentional and documented; the README states that these are untrusted payload and trusted submission contracts, not executable actions or proof of authority.
10. Existing game-package behavior remains unchanged and all existing tests continue to pass.
11. `pyproject.toml`, installed distribution metadata, and the editable root-package entry in `uv.lock` report `0.10.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before adding production action-contract logic; record the import or missing-contract failure.
* Run the focused action-contract tests after each meaningful contract group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change from the task baseline is the editable root package version from `0.9.0` to `0.10.0`.
* `git diff --check`

Record the initial failing command and final command results in the handoff. The initial red state must precede production contract creation; do not remove or rename existing files afterward to manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires choosing operation resolution semantics, adding another operation or target kind, changing an accepted field meaning, introducing source authorization, defining runtime state, outcomes, events, or world actions, changing package schemas, adding a dependency, or weakening strict typed unions with generic mappings.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
