# TASK-027: Add the recorded integer-draw boundary

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Default implementer

**Role:** Implementer

**Agent:** Default

**Depends on:** Simulation arbiter contracts

## Objective

Provide one pure arbiter-facing operation that obtains a bounded integer from an injected source and returns a strict immutable audit record.

This task establishes the canonical randomness primitive and its failure boundary only. It does not implement a pseudorandom generator, persistence, game checks, or history integration.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: “Integer draw record”, “Integer draw request”, “Integer random source”, and “Simulation arbiter”
* `doc/requirements.md`: `RANDOM-001` through `RANDOM-014`
* `doc/decisions.md`: “Use recorded seeded randomness only for explicit checks” and “Begin recorded randomness with one validated integer primitive”
* `doc/high_level_design.md`: “Simulation arbiter”, “Principal records”, and “Testing strategy”
* `src/llm_system/simulation/_types.py`, `src/llm_system/simulation/outcomes.py`, `src/llm_system/simulation/__init__.py`, `tests/test_outcomes.py`, `tests/test_package.py`, `README.md`, `pyproject.toml`, and `uv.lock`

Do not read postponed ideas, the initial scenario, scheduling, resolvers, package content, persistence, experiments, or other task briefs.

## Fixed assumptions

* Add a focused `src/llm_system/simulation/randomness.py` module.
* `RandomDrawPurpose` is a public strict string type constrained to the existing non-empty lowercase kebab-case machine-value pattern. It is extensible and is not an enum or authored-package reference.
* `IntegerDrawRequest` is a public strict frozen Pydantic model with exactly `draw_id: UUID`, `purpose: RandomDrawPurpose`, `lower_inclusive: StrictInt`, and `upper_inclusive: StrictInt`.
* Request validation rejects booleans, coercible numeric values, equal bounds, and descending bounds. Signed integer bounds are valid when `lower_inclusive < upper_inclusive`.
* `IntegerDrawRecord` is a public strict frozen Pydantic model with exactly the request fields in the same order followed by `result: StrictInt`. Its validation requires the result to be inside the inclusive bounds and independently preserves the non-degenerate range invariant.
* `IntegerRandomSource` is a public typing protocol with exact keyword-only method `draw_integer(*, lower_inclusive: int, upper_inclusive: int) -> int`.
* Add public `draw_recorded_integer(request: IntegerDrawRequest, source: IntegerRandomSource) -> IntegerDrawRecord`.
* The draw operation calls the source exactly once with only the request bounds. It passes neither identity nor purpose and does not mutate the request or source.
* A valid result produces one record preserving the request UUID, purpose, and bounds exactly. Identity is never generated internally.
* A returned boolean, non-integer, or out-of-range integer raises public `RandomSourceContractError`, a `RuntimeError` with a stable non-blank message, and produces no record. Do not clamp, coerce, or retry.
* An exception raised by the source propagates as the exact exception object without wrapping or retry, and no record is produced.
* The source protocol is structurally typed; do not add runtime protocol checks, abstract base classes, generic type parameters, registries, adapters, or service classes.
* No concrete random source, Python `random` adapter, seed model, generator-state model, state serialization, or dependency is included.
* Do not add rule-check, dice, percentage, choice, weighted-choice, outcome, event, trace, persistence, logging, or LLM integration.
* This public kernel milestone advances the project version from `0.25.0` to `0.26.0`; the lockfile's editable root-package version must match.

## In scope

* Add the strict request and record contracts, injected source protocol, typed invalid-result error, and pure recorded integer-draw operation.
* Publicly re-export `RandomDrawPurpose`, `IntegerDrawRequest`, `IntegerDrawRecord`, `IntegerRandomSource`, `RandomSourceContractError`, and `draw_recorded_integer` from `llm_system.simulation`.
* Add high-signal behavioral tests for strict schemas, valid signed and boundary results, exact source arguments and call count, exact metadata preservation, invalid returned types and ranges, exception identity propagation, no retry, and input immutability.
* Update README and accepted high-level-design descriptions only as needed to document the implemented public API and its exclusions.
* Update project version, lockfile root metadata, package-version test, task status, and handoff report.

## Out of scope

* Concrete pseudorandom or cryptographic generators, seeds, generator state, serialization, restoration, repositories, SQLite, transactions, restart recovery, or replay orchestration.
* Rule-pack schemas, random-check definitions, check formulas, modifiers, thresholds, degrees of success, dice notation, probabilities, collection choice, weighted selection, Fieldcraft, progression, or scenario content.
* Proposal authorization, action resolution, outcomes, canonical events, event history, simulation-step traces, world state, scheduling, perception, UI, API, model calls, or narration.
* Retry, fallback, clamping, coercion, exception wrapping, logging, metrics, ID generation, purpose enums, generic payload dictionaries, source registries, adapter frameworks, or new dependencies.
* Changes to requirements, decisions, glossary, initial scenario, ideas, experiments, agent configuration, completed task briefs, or roadmap structure beyond the explicitly authorized TASK-027 status transition.

## Expected contracts and files

Production belongs in `src/llm_system/simulation/randomness.py`, with public re-exports from `src/llm_system/simulation/__init__.py`. Focused tests belong in `tests/test_recorded_random_draws.py`.

The new public names are exactly `RandomDrawPurpose`, `IntegerDrawRequest`, `IntegerDrawRecord`, `IntegerRandomSource`, `RandomSourceContractError`, and `draw_recorded_integer`. Existing simulation contracts remain unchanged.

## Acceptance criteria

1. The request is strict, immutable, exactly shaped, application-identified, and accepts only a lowercase kebab-case purpose plus a non-degenerate strict signed integer range (`RANDOM-007`, `RANDOM-008`).
2. The source protocol exposes only the keyword-based inclusive integer operation and receives no identity, purpose, or domain context (`RANDOM-009`).
3. The public operation calls the injected source exactly once with the exact request bounds and returns a strict immutable record preserving exact request metadata and a valid inclusive result (`RANDOM-010`, `RANDOM-011`).
4. Boolean, non-integer, below-range, and above-range source results raise `RandomSourceContractError` without coercion, clamping, retry, identity generation, or a record (`RANDOM-012`).
5. A source-raised exception propagates unchanged after exactly one call and produces no record (`RANDOM-013`).
6. Equal or descending request and record bounds and out-of-range record construction fail structural validation independently of the draw operation.
7. Repeated calls with equivalent scripted sources produce equal records and neither request nor source metadata is mutated.
8. Public exports, README, and high-level design accurately describe the one-primitive API, authority boundary, validation, and deferred persistence and mechanic integrations.
9. Existing package, state, action, outcome, event, resolver, perception, scheduler, and commitment behavior remains unchanged.
10. Project and installed metadata plus editable root `uv.lock` report `0.26.0`; dependencies and resolved dependency versions remain unchanged.

## Required verification

* Write a failing behavioral test before implementation logic and record genuine red evidence.
* `uv run pytest tests/test_recorded_random_draws.py tests/test_outcomes.py tests/test_package.py -q`
* `uv sync --locked`
* `make format`
* `make lint`
* `make mypy`
* `make test`
* `make check`
* `uv lock --check`
* Confirm the only `uv.lock` change is editable root version `0.25.0` to `0.26.0`.
* `git diff --check`

Record initial red and final green evidence in the handoff. Do not manufacture failure evidence.

## Stop conditions

Stop and report a design gap if implementation requires a concrete generator, seed or generator-state contract, persistence or replay semantics, history or trace ownership, rule-check mechanics, a second randomness primitive, source retry or exception translation, identity generation, an existing contract change, a dependency, or broader arbiter infrastructure.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
