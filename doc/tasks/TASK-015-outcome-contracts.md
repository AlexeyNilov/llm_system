# TASK-015: Define outcome contracts and aggregate consistency

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** TASK-014

## Objective

Provide strict immutable public contracts for rejected, failed, and succeeded action outcomes. Valid-attempt outcomes aggregate typed state changes and canonical events while enforcing all context-free causation, timestamp, identity, and affected-field consistency.

These contracts do not prove that an outcome is valid for a particular proposal or world snapshot. State-dependent validation and commitment remain the simulation arbiter's responsibility.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Action proposal”, “Event”, “Outcome”, “Simulation arbiter”, and “Simulation step”
* `doc/requirements.md`: `ACTION-006` through `ACTION-010`, `ACTION-024` through `ACTION-042`, and `EVENT-002`, `EVENT-005`, `EVENT-013`
* `doc/decisions.md`: “Distinguish rejected, failed, and succeeded outcomes”, “Make outcome status variants structurally distinct”, “Timestamp outcomes and events at atomic completion”, “Validate context-free outcome consistency structurally”, “Keep outcome reason codes formatted but resolver-extensible”, “Require explicit effect tuples on valid-attempt outcomes”, and “Define state changes and events before outcome aggregates”
* `doc/high_level_design.md`: “Principal records” and “Testing strategy”
* `src/llm_system/simulation/changes.py`, `src/llm_system/simulation/events.py`, `src/llm_system/simulation/_types.py`, `src/llm_system/simulation/__init__.py`, `tests/test_state_changes.py`, `tests/test_events.py`, `tests/test_package.py`, `pyproject.toml`, `uv.lock`, and `README.md`

Do not read postponed ideas, the initial scenario, unrelated requirements or decisions, other task briefs, experiments, or roadmap content beyond this task.

## Fixed assumptions

* All outcome contracts are strict frozen Pydantic 2 models that forbid unknown fields, contain no generated identity or time defaults, and expose only immutable tuples.
* `OutcomeReasonCode` is a public strict lowercase kebab-case string constraint. It is not an enum, generic message, or package-defined semantic registry.
* Every outcome variant requires application-supplied `uuid.UUID` `outcome_id` and `proposal_id`, `reason_code: OutcomeReasonCode`, non-negative strict integer `resolved_at_seconds`, and its exact `status` discriminator.
* `RejectedOutcome` has status `rejected` and has no `state_changes` or `events` fields. Unknown-field rejection makes adding either effect structurally invalid.
* `FailedOutcome` has status `failed`; `SucceededOutcome` has status `succeeded`.
* Failed and succeeded outcomes each require explicit `state_changes: tuple[StateChange, ...]` and `events: tuple[CanonicalEvent, ...]`. Neither field has a default, but either supplied tuple may be empty.
* `Outcome` is a closed union of exactly those three variants, discriminated by `status`.
* Every event nested in a failed or succeeded outcome must have `outcome_id` equal to the containing outcome ID and `occurred_at_seconds` equal to its `resolved_at_seconds`.
* Event IDs must be unique within one outcome. Proposal identity does not appear on events.
* A character-location change conflict key is its character ID; object-placement uses object ID; connection-availability uses connection ID; simulation time uses one singleton key.
* A failed or succeeded outcome may contain multiple changes of different kinds or different affected IDs, but may contain at most one change for any one conflict key. Sequential deltas must already be collapsed.
* Context-free consistency failures use ordinary Pydantic `ValidationError`; no new application-owned semantic error type is introduced.
* Model construction does not know an input `WorldState`, `ValidatedWorldState`, proposal payload, submission source, rule pack, resolver, or persistence transaction.
* Do not validate whether before values match state, a time delta starts at input time or ends at completion time, changes agree with events, events agree with the proposed operation, references are actionable, or the source is authorized. Those checks belong to the arbiter.
* Do not require an event, state change, or simulation-time change for failed or succeeded outcomes.
* Shared private constraints may be centralized if existing public behavior remains unchanged; private helpers must not become public API.
* No new dependency is required.
* This public contract milestone advances the project version from `0.13.0` to `0.14.0`; the lockfile's editable root-package version must match.

## In scope

* Add public `OutcomeReasonCode`, `RejectedOutcome`, `FailedOutcome`, `SucceededOutcome`, and `Outcome` contracts.
* Implement exact context-free nested event and state-change consistency validators.
* Expose all intended contracts from `llm_system.simulation`.
* Add behavioral tests for every variant, strict JSON round-trip, explicit empty effects, rejection field absence, reason formatting, injected UUIDs, strict time, immutability, event causation/time matching, event-ID uniqueness, every change conflict key, and permitted independent changes.
* Preserve all existing action, runtime-state, validation, change, and event behavior.
* Update README with outcome status semantics, explicit effect evidence, structural guarantees, and arbiter-deferred guarantees.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* State lookup or mutation, outcome generation, proposal validation, authorization, operation resolvers, reason-code catalogs, state-dependent consistency, or atomic commitment.
* Random draws, world initialization, scheduling, perception, persistence, APIs, UI, narration, or System notifications.
* Rejected effects, optional or defaulted valid-attempt effect fields, additional outcome statuses, warnings, generic effect mappings, or application-owned outcome-validation errors.
* New state-change or event variants, world actions, objectives, Fieldcraft, progression, bridge/flood mechanics, or other Greybridge-specific behavior.
* Changes to existing public contracts beyond additive outcome exports.
* New dependencies or dependency-version changes.
* Changes to governance documents, roadmap, glossary, initial scenario, ideas, experiments, agent configuration, or completed task briefs.

## Expected contracts and files

Likely production belongs in `src/llm_system/simulation/outcomes.py`, publicly re-exported from `src/llm_system/simulation/__init__.py`. Focused tests likely belong in `tests/test_outcomes.py`.

Public names are exactly `OutcomeReasonCode`, `RejectedOutcome`, `FailedOutcome`, `SucceededOutcome`, and `Outcome`.

## Acceptance criteria

1. `Outcome` discriminates exactly rejected, failed, and succeeded variants with required injected IDs, strict completion time, and formatted reason code (`ACTION-024`, `ACTION-025`, `ACTION-029`, `ACTION-039`).
2. Rejected outcomes expose no effect fields and reject attempts to add them; failed and succeeded outcomes require both explicit immutable tuples while allowing either to be empty (`ACTION-007`, `ACTION-026`, `ACTION-027`, `ACTION-041`, `ACTION-042`).
3. Nested events must match the containing outcome identity and completion time, and duplicate event IDs are rejected (`ACTION-031`, `ACTION-034`, `ACTION-035`).
4. Duplicate state changes for the same character, object, connection, or simulation-time singleton are rejected, while independent changes are accepted (`ACTION-036`).
5. Context-free validation does not inspect world state or enforce time-delta, proposal, event/change, rule, actionability, or authorization semantics (`ACTION-032`, `ACTION-037`, `ACTION-038`).
6. Reason codes reject blank, uppercase, underscore, whitespace, and malformed separator values without imposing a central semantic enum (`ACTION-039`, `ACTION-040`).
7. Every model is strict and immutable, rejects unknown fields and invalid discriminators, and round-trips deterministic JSON using arrays for effect tuples.
8. Public exports and README accurately distinguish rejected, failed, and succeeded semantics plus structural versus arbiter guarantees (`ACTION-006` through `ACTION-009`, `ACTION-028`).
9. Existing simulation and package behavior remains unchanged.
10. Project and installed metadata plus the editable root in `uv.lock` report `0.14.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write and run focused failing behavioral tests before production outcome logic; record the import or missing-contract failure.
* Run focused outcome tests after each meaningful contract group.
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is the editable root package version from `0.13.0` to `0.14.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires world or proposal lookup, a different outcome field or status, default effects, reason-code semantics, another conflict rule, a new error type, existing contract changes, a dependency, or arbiter behavior.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
