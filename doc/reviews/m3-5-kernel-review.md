# M3.5 deterministic-kernel persistence review

## Verdict

**Ready for M4 with prerequisites.**

The implemented kernel has one coherent canonical-authority path: trusted application
metadata is authorized, concrete proposal types are dispatched to deterministic
resolvers, resolved typed deltas are committed into one replacement
`ValidatedWorldState`, and event feedback is projected separately. SQLite does not
need to acquire domain-rule authority to persist that result. The immutable input and
replacement-state model also gives M4 a credible atomic unit.

One prerequisite should be accepted before the first SQLite design task: add one
behavioral kernel-flow test that proves a successful real-package Use through
authorization, dispatch, commitment, and available perception. The current stages are
well tested separately, and a review probe proved the combined path, but the durable
suite bypasses authorization in its successful Use path. M4 would otherwise harden an
integration seam without regression evidence for the authority chain it must wrap.

This verdict does not treat absent M4 coordination, persistence, traces, scheduled-
activity execution, or deferred vertical-slice features as M3 defects.

## Baseline and method

### Reviewed baseline

| Item | Value |
| --- | --- |
| Git revision | `bc35b67bf380e1a79f1661d4b28b853a801c91ad` |
| Branch state at start | `main...origin/main [ahead 2]`; no uncommitted files |
| Project version | `0.33.0` |
| Test inventory | 323 collected tests |

### Verification

| Command | Result |
| --- | --- |
| `git status --short --branch` | Clean; branch ahead by two commits |
| `git rev-parse HEAD` | Passed; revision above |
| `uv sync --locked` | Passed; 19 packages resolved, 18 checked |
| `uv run pytest --collect-only -q` | Passed; 323 tests collected |
| `make check` | Passed; 66 files formatted, Ruff clean, mypy clean, 323 tests passed |
| `uv lock --check` | Passed |
| Focused kernel evidence tests | Passed; 75 tests in Use, authorization, dispatch, commitment, self feedback, scheduling, and randomness |
| Review Use-chain probe | Passed; reported `succeeded 49 True object_used` |

The first sandboxed `uv sync --locked` invocation failed before dependency work with
Snap's `snap-confine has elevated permissions and is not confined` refusal. The exact
command and all other `uv`-backed commands were rerun outside that sandbox and passed.
This is an execution-environment limitation, not repository evidence.

### Method

Verified facts below come from accepted requirements and decisions, the complete
current `src/llm_system/` and `tests/` inventories, named implementation paths, test
collection, and executed checks. The representative trace uses the real public symbols
and Greybridge package behavior. Inferences are labeled where they concern how M4 can
compose existing seams. Recommendations are not claims about current implementation.

## Representative successful Use trace

The concrete scenario is the Greybridge `0.2.0` reinforcement mechanic: the player is
at `greybridge-span`, possesses `reinforcement-materials`, and applies them to the span
while `bridge-reinforced` is false. The authored duration is 300 seconds.

| Stage | Implemented symbol and evidence | Inputs and outputs | Authority and mutation | Future transaction relationship |
| --- | --- | --- | --- | --- |
| Proposal | `UseActionProposal` in `simulation/actions.py`; proposal-union tests in `tests/test_actions.py` | Untrusted `operation="use"`, exact `object_id`, and typed target | Proposes only; no identity, provenance, validation, or mutation | Trace input; never persisted as authority by itself |
| Trusted submission | `ActorActionSubmission` | Application-injected proposal, simulation-step, and decision-context UUIDs; typed source; actor; proposal | Application owns metadata trust; construction does not prove authorization | Coordinator must create and trace it, never accept these fields from generated output |
| Authorization | `authorize_actor_action()` in `simulation/authorization.py:125`; authorization tests | `ValidatedWorldState` plus submission to exact-input `AuthorizedActorAction` | Checks actor/source authority only; no target resolution or mutation | Must occur inside the application-controlled step before dispatch |
| Dispatch | `dispatch_actor_action()` in `simulation/dispatch.py:32`; Use branch at line 46 | Authorized action plus caller IDs to resolver outcome | Pure type-directed routing; no authorization, commitment, or persistence | Coordinator supplies identities and retains the exact returned outcome |
| Resolution | `_binding()`, `_applicable_use()`, and `resolve_use()` in `simulation/resolvers/use.py:25-127` | Validated packages and runtime overlays to succeeded outcome | Resolver owns Use semantics; reads exact binding, actor location, possession, fact, and mechanic; mutates nothing | Runs before storage; SQLite must not repeat binding or actionability rules |
| Outcome | `SucceededOutcome` with reason `object-used` | Ordered `BooleanWorldFactChanged`, then `SimulationTimeChanged`; one `ObjectUsedEvent` | Typed resolution evidence, not committed state | Outcome, identities, changes, and event belong in the step trace; event is also durable causal history |
| Commitment | `commit_outcome()` in `simulation/commitment.py:363` | Validated world and outcome to `OutcomeCommitResult` | Arbiter commitment validates all deltas before applying any, then returns one revalidated replacement world; input remains unchanged | Natural domain input to one repository transaction; persistence failure must not publish completion |
| Canonical state evidence | `OutcomeCommitResult.world` | `bridge-reinforced=true`, time advanced by 300 seconds, materials still possessed | Replacement `ValidatedWorldState` is canonical in-memory result | Store replacement state and package-version world metadata atomically |
| Canonical event evidence | `OutcomeCommitResult.outcome.events` | Exact `ObjectUsedEvent`, linked to outcome and occurrence time | Outcome owns events; they are facts, not mutation commands or visibility decisions | Store event history in the same transaction; do not duplicate a competing event collection in the domain result |
| Perception | `project_current_perception()` and `project_self_event_feedback()` in `simulation/perception_engine.py:224-266` | Committed world and caller-selected events to current snapshot and exact `EventObserved` feedback | Perception derives actor-limited information without changing truth | Coordinator selects/composes feedback after canonical resolution; persisted delivery/window semantics remain M4/later responsibilities |
| Persistence and step trace | **Planned/absent**; no coordinator or repository symbol exists in `src/llm_system/` | Intended complete step aggregate | M4 turn coordinator owns orchestration; SQLite owns durability, not rules | One transaction must cover replacement state, events, queue changes, authoritative character data, and trace before presentation sees completion |

Verified: `tests/test_use_resolver.py::test_real_greybridge_packages_drive_reinforcement_over_300_seconds`
proves package-driven resolution and commitment at times 120 to 420. The review probe
additionally exercised the public authorization, dispatch, commitment, and self-event
feedback chain and observed success, the changed fact/time, and `object_used` feedback.

## Boundary assessment

### Authority and ownership

Verified:

* Proposal producers may propose but cannot change canonical state (`AUTH-001` through
  `AUTH-004`, `AUTHZ-001`, `ARBITER-001`).
* `ValidatedGamePackages` owns immutable authored definitions; `WorldState` owns only
  mutable ID-linked overlays. `resolve_use()` joins them without copying package-owned
  names, topology, or mechanics into runtime state (`STATE-019` through `STATE-024`,
  `USE-001`).
* Operation resolution produces evidence. Only `commit_outcome()` applies the typed
  delta set, and it returns one replacement validated snapshot (`ARBITER-002`,
  `ARBITER-005` through `ARBITER-021`).
* Canonical events remain inside the outcome; perception decides who receives an
  observation. No event payload encodes observers or narrative (`EVENT-001` through
  `EVENT-013`, `PERCEPTION-001` through `PERCEPTION-035`).

Inference: M4 can keep SQLite below a repository boundary because every Use rule needed
to decide the replacement snapshot has already run before persistence. A repository
can serialize the accepted aggregate without selecting mechanics, authorizing actors,
or interpreting deltas.

### Atomicity and failure behavior

Verified: commitment validates the full change tuple first, aggregates applicable
issues, applies nothing on failure, builds a new `WorldState`, and revalidates it. This
satisfies the in-memory half of immutable atomic replacement. It does not claim durable
commitment, as required by its accepted boundary.

Recommendation: M4 should expose one application-level transaction operation for a
completed simulation step. That operation should store the latest-world replacement,
canonical events, scheduled-queue changes, authoritative character records, and step
trace together. It should return success only after SQLite commits. Presentation must
consume only committed results. This is the behavioral shape required by `WORLD-003`,
`STORE-002`, `STORE-004`, and `high_level_design.md:386-409`; it is not a proposal for
table layout.

Inference: because current domain objects are immutable and events remain paired with
the committed outcome, rollback does not require undoing mutated Python domain objects.
On transaction failure, the coordinator can discard the unpersisted aggregate and
retain the previously loaded committed world.

### Replay, identities, scheduling, and randomness

Verified:

* Runtime UUIDs are caller-injected throughout proposal submission, dispatch, Use
  resolution, events, and recorded draw requests. The kernel does not hide identity
  generation inside deterministic functions.
* `ScheduledActivitySelection` is a validated deterministic partition ordered by
  eligibility time, variant-derived phase, and insertion sequence. It deliberately
  neither claims nor executes work.
* `draw_recorded_integer()` validates one injected result and retains its purpose,
  bounds, identity, and value. A concrete generator and generator-state persistence are
  explicitly deferred until the first real consumer (`RANDOM-014`).

Recommendation: the M4 coordinator must own unique insertion-sequence allocation,
selection consumption, serial execution, and trace order in the same step transaction.
When the first random consumer exists, generator state and successful draw records must
join that transaction. Neither intentional seam requires an M3 refactor.

### Repository seams

Inference: the likely repository seams are viable if they persist domain results rather
than accept mutation commands. A world repository may reconstruct a validated snapshot
against recorded exact package versions; an event/trace repository may serialize the
outcome evidence; a scheduled-activity repository may persist the queue/selection
effects. One transaction owner must compose these repositories. Allowing each
repository to commit independently would create competing definitions of a completed
step and endanger `STORE-002`.

## Findings

### KRV-001 — Medium — missing durable authority-chain Use test

**Timing:** before M4.

**Verified evidence:** `tests/test_use_resolver.py:283-302` constructs
`AuthorizedActorAction` directly. Its real Greybridge success test does the same at
lines 550-568 before resolving and committing. The dispatcher Use test at
`tests/test_actor_action_dispatch.py:255-271` routes an inapplicable action and asserts
rejection. Authorization has strong isolated tests, but no collected test combines
authorization, successful Use dispatch, commitment, and available event perception.

**Impact:** a regression that lets the application bypass authorization, misroutes
successful Use, loses its event during commitment, or fails to project self feedback
could leave all current task-local tests green. This endangers the composed intent of
`AUTHZ-001`, `DISPATCH-004` through `DISPATCH-005`, `USE-006` through `USE-008`,
`ARBITER-008`, and `PERCEPTION-026` through `PERCEPTION-031` at precisely the seam M4
will persist.

**Recommendation:** add one deterministic test using Greybridge `0.2.0` that constructs
the trusted player submission, calls `authorize_actor_action()`,
`dispatch_actor_action()`, `commit_outcome()`, and `project_self_event_feedback()`, and
asserts exact IDs, the 300-second time change, fact replacement, preserved possession,
event causation, and actor feedback. Do not mock internal boundaries. The review probe
shows this can be done without changing architecture.

### KRV-002 — Medium — transaction ownership is the critical planned M4 seam

**Timing:** during M4.

**Verified evidence:** the source tree has no application coordinator or persistence
module. `commit_outcome()` returns only the exact outcome and replacement world;
`select_eligible_activities()` returns a pure queue partition; perception accepts a
caller-selected event tuple. This matches the task's fixed assumptions and accepted
M4 plan rather than contradicting M3.

**Impact:** if M4 persists state, events, queue consumption, and trace through separate
commit points, a failure could expose a new world without its causal event or trace,
re-execute claimed scheduled work, or present a step that `STORE-004` says did not
complete. SQLite would then become an accidental workflow authority.

**Recommendation:** make one turn-coordinator/application transaction the sole owner of
completion. Repository methods should store already validated domain data under that
transaction. Add failure-injection tests proving restart restores the previous complete
step after any pre-commit failure and the complete new step after commit.

### KRV-003 — Low — README is a late, duplicated source-of-truth map

**Timing:** during M4; not a persistence gate.

**Verified evidence:** `README.md` is 722 lines. It repeats detailed contracts for nearly
every M3 boundary, while the authoritative-document links appear only at lines 703-713.
Lines 715-722 then present machine-specific local service endpoints and an absolute path
to another checkout, despite the setup section correctly stating that `make check`
requires no service. Detailed README contract prose duplicates requirements, decisions,
the glossary, and high-level design and can drift as M4 changes boundaries.

**Impact:** a new developer can reasonably mistake README prose for the authoritative
contract, miss current project status until reading hundreds of lines, or infer that
private local services and another repository are prerequisites. This is the concrete
risk anticipated by `IDEA-010` and `IDEA-011`.

**Recommendation:** implement `IDEA-010` incrementally as a concise landing page: current
status and non-goals, setup/check commands, one short architecture orientation, one
minimal working example, and a near-top source-of-truth map that states what each linked
document owns. Move or remove machine-specific notes and detailed boundary reference
material rather than duplicating accepted specifications. Keep `IDEA-011` in backlog
until the vertical slice stabilizes; then write a guided conceptual manual that links to
canonical terms, requirements, and decisions instead of restating them normatively.

### KRV-004 — Low — a few tests have low diagnostic value

**Timing:** defer; not a persistence gate.

**Verified evidence and candidates:**

* `tests/test_spatial_definitions.py::test_location_definition_accepts_a_valid_record`
  checks two constructor-to-getter values already exercised by graph, package, and
  Greybridge tests. Remove it; an incorrect location contract would still break
  meaningful parsing and validation behavior elsewhere.
* `tests/test_rule_pack_definition.py::test_rule_pack_records_preserve_valid_stable_identifiers_and_names`
  is the same getter-level pattern and is subsumed by catalog parsing, semantic
  validation, and real-package tests. Remove it or fold its one distinctive valid-ID
  example into a behavioral catalog test.
* `tests/test_scenario_pack_definition.py::test_scenario_pack_exposes_existing_typed_aggregate_models`
  asserts only concrete Pydantic member types already proven by nested aggregate parsing
  and downstream semantic validation. Consolidate it into
  `test_scenario_pack_parses_its_typed_nested_aggregates` if the public typed-composition
  promise still needs one assertion.
* `tests/test_package.py::test_installed_package_reports_the_declared_distribution_version`
  hard-codes `0.33.0`, so its main effect is forcing a test edit on every required
  version bump. Replace it with a cross-artifact assertion that reads the declared
  project version, or remove it if editable-install metadata is not a project-owned
  behavior under test.

These are named because a plausible defect in the project-owned behavior would not be
diagnosed uniquely by the current assertion. Similar-looking parameterized rejection
tests are not removal candidates: they protect namespace-gating, strict scalar, issue-
ordering, and information-leak contracts.

### Reviewed categories with no additional findings

No competing canonical authority, in-place mutation, package/runtime ownership leak,
hidden identity generation, event-visibility coupling, nondeterministic scheduling key,
unrecorded implemented randomness consumer, or SQLite coupling was found. No naming,
style, performance, deferred Help, deferred Use-witness, absent concrete generator, or
incomplete Greybridge feature was classified as a persistence finding.

## Test-value assessment

### High-risk requirement-to-test evidence

| Contract area | Concrete evidence | Assessment |
| --- | --- | --- |
| Trusted source authorization (`AUTHZ-001`–`015`) | `tests/test_actor_action_authorization.py` | Strong isolated evidence for player/NPC authority, gating precedence, exact issue paths, and input preservation |
| Type-based dispatch (`DISPATCH-001`–`010`) | `tests/test_actor_action_dispatch.py` | Strong route equivalence for all implemented operations and honest Help failure; successful Use route missing |
| Bound Use (`USE-001`–`012`) | `tests/test_use_resolver.py` | Strong mechanic/binding selection, uniform rejection, exact effects, determinism, commitment, and real Greybridge evidence; trusted wrapper is manually constructed |
| Atomic in-memory commitment (`ARBITER-005`–`021`) | `tests/test_outcome_commitment.py` | High signal: all change types, order/identity, aggregate error gating, before/reference mismatches, and invariant failure |
| Canonical events (`EVENT-001`–`013`) | `tests/test_events.py`, resolver tests, commitment tests | Strong typed/causal/time evidence; durable storage remains correctly untested until M4 |
| Perception separation (`PERCEPTION-015`–`035`) | current-state, self, addressed-speech, Take-witness, and overhearing test modules | Strong inclusion/exclusion, temporal validation, ordering, identity preservation, and information-boundary evidence; Use has only self feedback available by accepted scope |
| Deterministic scheduling (`SCHEDULE-001`–`023`) | scheduled-activity contract and selection test modules | Strong ordering and partition evidence, including overdue work, storage-order independence, and input reuse; execution/transaction evidence belongs to M4 |
| Recorded randomness (`RANDOM-001`–`014`) | `tests/test_recorded_random_draws.py` | Strong primitive contract and source-failure evidence; generator restart evidence is intentionally deferred |
| Persistence (`WORLD-001`–`006`, `STORE-001`–`005`) | No repository or persistence tests | Expected at M3; M4 must add restart and transaction-failure behavioral tests before claiming these requirements |
| Inspection (`INSPECT-001`–`006`) | No inspection implementation/tests | Planned later and not a kernel-readiness defect |

### High-signal strengths

The suite generally tests project-owned behavior rather than coverage numbers. The best
examples would fail on meaningful regressions: commitment issue gating and atomicity,
Use's package-driven effect and uniform rejection, world-overlay completeness,
scheduler ordering independent of UUID/storage order, and perception's exclusion and
time-validation boundaries. The suite avoids internal mocks and the normal check path
requires no external services, satisfying `DEV-005` and `DEV-006`.

### Missing high-risk evidence

Before M4, add only KRV-001. During M4, add transaction failure/restart tests, queue
claim/consumption ordering tests at the coordinator boundary, and proof that
presentation is not invoked for an uncommitted step. Add generator-state restart tests
only with the first accepted random consumer. Add inspection tests with the inspection
interface, not as speculative M3 tests.

### Consolidation and removal

The four KRV-004 candidates are justified removal/consolidation targets. No resolver
rejection matrix, commitment validation case, scheduling invariant case, authorization
precedence case, or perception exclusion case should be removed merely because it uses
the same function: those cases protect distinct observable contracts and have useful
diagnostic names.

## Documentation information architecture

### Current source-of-truth map

| Need | Current owner |
| --- | --- |
| Project purpose, setup, and entry point | `README.md` |
| Canonical vocabulary | `doc/glossary.md` |
| Accepted observable behavior | `doc/requirements.md` |
| Accepted architectural choices and rationale | `doc/decisions.md` |
| Consolidated components and information flow | `doc/high_level_design.md` |
| Greybridge scenario scope | `doc/initial_scenario.md` |
| Dependency order and readiness | `doc/roadmap.md` |
| Deferred possibilities | `doc/ideas.md` |
| Delegated work contracts | `doc/tasks/` and `doc/agent_workflow.md` |

The ownership model itself is sound and agrees with `doc/agent_workflow.md`. The problem
is navigation and duplication: README acts simultaneously as landing page, exhaustive
M3 API reference, local machine note, and document index. Its source-of-truth map is too
late to prevent readers treating the preceding duplicated prose as normative.

### Smallest useful treatment of IDEA-010 and IDEA-011

For `IDEA-010`, create one bounded documentation task after the M4 application seams
have names. Keep README responsible for orientation, setup, current status, and routing;
do not make a new normative API document by copying its current 600-plus lines of
contracts elsewhere. Focused examples may remain close to public code when they teach a
real workflow, but should link to the accepted owner for constraints.

For `IDEA-011`, retain backlog status through the vertical slice. Capture recurring
onboarding questions during M4 and use them to shape a later narrative manual. The
manual should explain how canonical truth, proposals, outcomes, events, perception, and
steps relate, while links and requirement/decision IDs point to normative details. It
must not replace or paraphrase the glossary and requirements as a second authority.

## Recommended gate

Before the first SQLite design task, accept one small testing task implementing KRV-001.
No M3 production-code refactor, package change, governance change, README rewrite,
concrete random generator, scheduled-activity executor, or deferred feature is required.

The first M4 persistence task should then carry these acceptance constraints:

1. SQLite stores already validated domain results and never evaluates Use or other
   operation rules.
2. One application transaction owns state replacement, canonical events, scheduled-
   queue effects, authoritative character data, and the simulation-step trace.
3. Transaction failure leaves the previous committed world recoverable and cannot
   report or present the attempted step as complete.
4. Exact package identities/versions and application-injected runtime identities remain
   traceable across restart.
5. Deterministic scheduler ordering and later recorded randomness remain domain inputs
   to the transaction, not database-defined behavior.

KRV-002 must be resolved by M4 implementation and failure tests. KRV-003 and KRV-004 may
be scheduled independently and do not block SQLite design.
