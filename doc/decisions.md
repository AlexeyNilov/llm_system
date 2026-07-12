# Decisions

## Why record decisions

Write down key development decisions while the context is fresh. A short note today can save hours later by explaining what was chosen, what was rejected, and why the trade-off made sense at the time.

## Guidance

Use a lightweight Architecture Decision Record (ADR) style:

* Record decisions that affect architecture, data flow, public APIs, dependencies, deployment, security, or long-term maintenance.
* Write the decision when it is made, not after the context has faded.
* Prefer short entries that explain the context, decision, alternatives, and consequences.
* Include enough reasoning for a future maintainer to understand the trade-off.
* Do not document every small implementation detail; focus on choices that would be costly or confusing to rediscover.
* Update or supersede earlier decisions instead of silently rewriting history.

## Entry template

```markdown
### YYYY-MM-DD: Decision title

**Status:** Proposed | Accepted | Superseded

**Context:** What problem, constraint, or trade-off led to this decision?

**Decision:** What was chosen?

**Alternatives considered:** What other options were rejected, and why?

**Consequences:** What becomes easier, harder, riskier, or more constrained?
```

## Actual decisions

### 2026-07-11: The simulation owns truth

**Status:** Accepted

**Context:** LLMs will help describe the world, interpret player input, propose NPC actions, and generate events. If those LLMs can independently change reality, the world will become contradictory and difficult to inspect or test.

**Decision:** Canonical world state and resolved outcomes belong to the simulation. LLMs may interpret state, propose intentions, and narrate outcomes, but they may not directly establish or modify canonical facts. Proposed actions and events must pass through simulation rules before they take effect.

**Alternatives considered:** Treat an LLM conversation or generated narrative as the world state. This is simpler initially, but makes consistency, persistence, validation, and debugging unreliable.

**Consequences:** World state and events must have structured representations. The application must separate perception, intention, validation, state transition, and narration. LLM output must be treated as untrusted proposals, and deterministic tests can verify the simulation independently of generated prose.

### 2026-07-11: Agents receive bounded context

**Status:** Accepted

**Context:** The intended experience is a persistent, inspectable simulation whose participants act from limited knowledge. Giving every LLM the complete world state would undermine believable perception and make prompts harder to reason about.

**Decision:** Each LLM-assisted participant receives a role-specific context assembled from its perception, relevant knowledge, goals, and memories. The player receives a personal narrative derived only from events and state they can perceive.

**Alternatives considered:** Give every participant the full simulation state. This reduces context-assembly work, but permits impossible knowledge, weakens agent identity, increases prompt size, and obscures information flow.

**Consequences:** Information architecture and context engineering are first-class parts of the design. Context sources, selection rules, provenance, and visibility boundaries must be explicit and inspectable. Different roles will require different context views over the same canonical state.

### 2026-07-11: Defer GraphRAG for the first NPC implementation

**Status:** Accepted

**Context:** NPCs need identity, goals, relationships, knowledge, and memory, but the retrieval questions and graph traversal patterns are not yet known. Introducing GraphRAG now would add architectural complexity before its value can be demonstrated.

**Decision:** Begin with structured NPC profiles and simple episodic memory retrieval. Add graph-based retrieval only after concrete use cases show that relationships or multi-hop knowledge cannot be represented or retrieved adequately by the simpler design.

**Alternatives considered:** Build NPC knowledge around GraphRAG from the start. This offers richer relationships in principle, but risks optimizing infrastructure before validating NPC behavior.

**Consequences:** The initial NPC design remains smaller and easier to test. Data boundaries should still allow a later graph representation, but no speculative graph abstraction or dependency will be introduced.

### 2026-07-11: Begin with one persistent world

**Status:** Accepted

**Context:** Persistence is necessary for a coherent ongoing simulation, but multiple worlds, save slots, branching timelines, and offline progression would add lifecycle complexity before the core simulation is validated.

**Decision:** The initial version has one player in one continuously saved world. Completed simulation steps persist their resulting state and event history. Application restarts resume that world, a development operation can reset it to a known scenario, and the world does not advance while the application is stopped.

**Alternatives considered:** Support multiple saves or worlds from the beginning, or treat each application session as a disposable world. Multiple saves add premature management complexity; disposable sessions work against persistence and long-running consequences.

**Consequences:** Persistence can use a simple single-world lifecycle while retaining an inspectable history. Multiple saves, branching, multiplayer, and offline simulation remain outside the initial scope, but can be reconsidered after the core loop works.

### 2026-07-11: Use discrete, action-driven simulation time

**Status:** Accepted

**Context:** Real-time progression would couple world behavior to server uptime, player response speed, and local LLM latency. A rigid round structure would be reproducible, but would assign artificial equal turns to activities with different durations.

**Decision:** World time advances in discrete increments caused by consequential player actions or an explicit wait. Actions have simulation durations. Private thoughts do not advance time. After time advances, the simulation resolves eligible NPC activity and scheduled events before narrating what the player can perceive. No background world ticks run while awaiting player input.

**Alternatives considered:** Advance continuously with wall-clock time, or use fixed rounds in which every participant receives one turn. Continuous time complicates reproducibility and operation; fixed rounds poorly represent actions with different durations.

**Consequences:** Event ordering can be deterministic and inspected independently of LLM response latency. The simulation will need a clock, action durations, and scheduling rules. A later real-time mode could drive the same clock, but is not part of the initial version.

### 2026-07-11: Give NPCs bounded proactive autonomy

**Status:** Accepted

**Context:** Purely reactive NPCs would behave like dialogue interfaces rather than inhabitants of a persistent world. Unrestricted autonomous LLM loops, however, would be expensive, difficult to reproduce, and able to contradict canonical state.

**Decision:** NPCs may proactively propose actions when the simulation scheduler determines they are eligible. Each decision uses bounded NPC-specific context and produces a structured intention. The simulation validates and resolves that intention; the NPC cannot mutate world state directly. NPC activity does not depend on being observed by the player.

**Alternatives considered:** Make NPCs react only to player interactions, or allow NPC agents to run continuously and execute their own changes. Reactive NPCs cannot sustain an independent world; unrestricted loops weaken consistency and control.

**Consequences:** NPCs can pursue goals and cause off-screen consequences while remaining subject to world rules. Decision context, proposed intentions, validation results, and resolved events can be inspected separately. Detailed LLM decisions should be reserved for active NPCs, while distant or inactive NPCs may later use coarser schedules and plans.

### 2026-07-11: Separate creative direction from simulation authority

**Status:** Accepted

**Context:** A traditional game master combines creative direction, rule interpretation, and authority over the game world. Giving all three responsibilities to an LLM would allow creative output to silently override rules and canonical state.

**Decision:** The LLM-assisted System director acts as the creative part of a game master and proposes world-level developments using structured operations. A deterministic simulation arbiter owns rule enforcement and canonical state, and validates and resolves every System director action proposal before it can take effect. System director context is broad but deliberately selected and inspectable.

**Alternatives considered:** Let the System director directly narrate changes into existence or act as both creative agent and final authority. This is flexible, but makes outcomes inconsistent, difficult to test, and difficult to distinguish from hallucination.

**Consequences:** Creative direction and mechanical authority can be evaluated independently. Player, NPC, and System director action proposals share a validation boundary. The rules may be loaded or changed through an explicit lifecycle, but the System director cannot rewrite them while resolving play.

### 2026-07-11: Separate the simulation kernel from game packages

**Status:** Accepted

**Context:** Rules and scenarios should be easy to change and may eventually be generated from source material. Encoding all game-specific mechanics and content in the application would couple experimentation to core code changes. Making every behavior declarative, however, would require building a general-purpose rule language.

**Decision:** Keep simulation invariants in a stable Python kernel. Load changeable mechanics from versioned rule packs and initial world content from versioned scenario packs. Packages use explicit operations supported by the kernel and are validated before use. Each persistent world records its package identities and versions. Incompatible package changes require an explicit reset or migration.

**Alternatives considered:** Hard-code each game's rules and scenario in the application, or build a universal rule language before implementing the core simulation. Hard-coding impedes experimentation; a universal language would dominate the project before its required semantics are known.

**Consequences:** Common mechanics and content can change independently of the kernel, while state-transition invariants remain testable in Python. Some unusual mechanics may later need explicit Python extension points. Package schemas, validation, compatibility rules, and provenance become important parts of the information architecture.

### 2026-07-11: Build an open simulation with a lightweight game layer

**Status:** Accepted

**Context:** A fixed plot or command menu would make behavior easier to constrain, but would undermine experimentation and autonomous consequences. A completely unstructured conversational sandbox would offer freedom without legible mechanics, stakes, or a recognizably LitRPG experience.

**Decision:** The player interacts through free-form intentions in an open simulation. Scenario packs provide situations, pressures, and opportunities rather than mandatory plots. Rule packs provide lightweight, visible mechanics such as abilities, resources, action resolution, and progression. The System director may propose objectives for presentation by the System interface, but the player can ignore or oppose them and experience the resulting consequences.

**Alternatives considered:** Build a scripted game with a prescribed story, or build a mechanics-free narrative sandbox. The scripted approach limits emergence; the sandbox makes outcomes difficult to understand and weakens the role of the player-visible System interface.

**Consequences:** The intention interpreter must map open-ended input onto supported operations without inventing mechanics. Local conflicts can succeed or fail while the persistent world continues. The initial vertical slice must demonstrate both meaningful freedom and at least one visible progression event.

### 2026-07-11: Separate the hidden System director from the visible System interface

**Status:** Accepted

**Context:** LitRPG conventions benefit from a System interface that communicates abilities, status, progression, and objectives to the player. If the creative System director speaks directly, however, generated language could be mistaken for an authoritative mechanical outcome.

**Decision:** The System director remains an internal creative agent. A separate diegetic System interface presents player-visible mechanical facts confirmed by the simulation arbiter. An LLM may style those notifications but cannot change their factual payload. The narrator remains responsible for perceived world events.

**Alternatives considered:** Hide all mechanics behind narration, or allow the System director to address the player directly. Hidden mechanics weaken the LitRPG experience; direct director speech conflates creative proposals with canonical facts.

**Consequences:** System notifications need structured factual payloads distinct from their presentation. Mechanical communication can be tested without testing generated prose. Objectives offered through the interface remain optional until accepted by the player.

### 2026-07-11: Model space as a location graph with deterministic perception

**Status:** Accepted

**Context:** The simulation needs movement, visibility, travel time, barriers, and descriptions of a character's surroundings. Letting an LLM invent space on demand would undermine canonical truth, while exact continuous geometry would add pathfinding and measurement complexity unnecessary for the initial experience.

**Decision:** Represent world topology as structured location nodes connected by explicit traversal edges. Characters and objects have canonical locations. A deterministic perception component derives what an observer can detect from world state, and the narrator turns only that perception snapshot into prose. Within-location positioning initially uses coarse relationships rather than exact coordinates.

**Alternatives considered:** Use an LLM-generated map implicit in narrative history, or begin with a coordinate grid or continuous geometry. Narrative maps are inconsistent; geometric maps introduce complexity before the simulation requires precise distance.

**Consequences:** Scenario maps can be validated using graph properties such as reachability and connectivity. Connections can carry direction, duration, requirements, and state. Optional coordinates may later support visual presentation or import workflows without becoming the initial source of mechanical truth.

### 2026-07-11: Separate truth, perception, memory, and belief

**Status:** Accepted

**Context:** NPCs need to remember, infer, misunderstand, learn, and potentially be deceived without changing what is canonically true. Treating retrieved text as truth would collapse those distinctions and leak unavailable information into decisions.

**Decision:** Maintain separate representations for canonical world state, current character perception, durable episodic memories, and mutable beliefs. Character decision context combines only character-available information with identity, goals, and plans. Vector search may select relevant memories, but its index is derived and rebuildable rather than authoritative.

**Alternatives considered:** Give NPCs canonical state directly, or treat a vector database as the canonical memory store. Direct access creates impossible knowledge; vector retrieval does not provide an adequate durable or auditable source of truth.

**Consequences:** NPCs can hold false or uncertain beliefs while the simulation remains consistent. Observations and memories need provenance and simulation-time metadata. Primary persistence owns memory records, while Qdrant can be used as an optional retrieval projection.

### 2026-07-11: Use an explicit cognition and action loop

**Status:** Accepted

**Context:** Actors need a consistent path from world events to perception, interpretation, choice, action, consequence, and learning. Without explicit boundaries, canonical facts can leak into character reasoning and generated intentions can be mistaken for completed actions.

**Decision:** Model NPC behavior as canonical reality, perceptual filtering, observation and memory, sensemaking, intent, structured action proposal, arbiter resolution, outcome, and renewed perceptual filtering. Feedback is actor-specific evidence about an outcome and does not bypass perception. For the player, the human owns sensemaking and intent; the application interprets only explicitly supplied thoughts and attempted actions.

**Alternatives considered:** Use a single LLM call from world state directly to narrative and state changes, or give actors direct outcome feedback. A single call collapses responsibilities; direct feedback gives actors knowledge they may not possess.

**Consequences:** Each stage has explicit inputs and outputs and can be tested or inspected independently. Character traits and limitations can affect the appropriate stage. Player motives must not be silently invented by the application.

### 2026-07-11: Make NPC decision policies interchangeable

**Status:** Accepted

**Context:** Not every actor benefits from open-ended LLM reasoning. Simple creatures, routine behaviors, and strong archetypes can be represented more coherently and cheaply with limited action sets, priorities, schedules, or deterministic rules.

**Decision:** NPC decision-making uses a common contract from bounded decision context to structured action proposal. An NPC may use a rule-based, scripted, LLM-assisted, or hybrid policy. Prefer rule-based behavior when it adequately represents the actor. Archetypes provide defaults that individual NPC definitions may override. Every policy remains subject to arbiter validation and cannot modify canonical state.

**Alternatives considered:** Use an LLM for every NPC, or hard-code one global behavior system. Universal LLM use adds latency and weakens predictability; one fixed behavior system cannot represent both simple and socially complex actors well.

**Consequences:** LLM calls can be reserved for decisions that require richer interpretation. Different policies can be compared under the same inputs and tested against the same output contract. Behavioral simplicity is modeled through actual constraints rather than prompts asking a model to reason poorly.

### 2026-07-11: Validate the architecture with a non-combat vertical slice

**Status:** Accepted

**Context:** The first playable scenario must exercise the architectural boundaries without requiring a large game-mechanics subsystem. Combat would introduce targeting, range, health, damage, equipment, incapacitation, death, and balance before the core actor loop is validated.

**Decision:** Build a compact non-combat scenario with three connected locations, one player, one rule-driven NPC, one LLM-assisted NPC, a scheduled environmental event, asymmetrically available information, an optional objective, basic world interactions, a skill check, visible progression, and restart persistence. Mutable belief state and belief revision are not part of this slice.

**Alternatives considered:** Begin with combat, or build isolated technical components without a playable scenario. Combat expands scope sharply; disconnected components do not validate their integration into a coherent experience.

**Consequences:** The vertical slice can test every major information and authority boundary with limited mechanics. Combat remains a future rule-pack extension rather than a kernel concern.

### 2026-07-11: Use SQLite as the initial authoritative store

**Status:** Accepted

**Context:** The initial deployment is local, single-player, and single-world, but requires transactional persistence, restart recovery, event history, character memory, and inspectable traces. A separate database service would add operations without addressing a current concurrency or scale requirement.

**Decision:** Use SQLite as the authoritative store for initial world and character data. Commit completed simulation steps atomically. Treat Qdrant as a rebuildable retrieval projection over durable memory data rather than an authoritative store.

**Alternatives considered:** Begin with PostgreSQL, use Qdrant as the primary memory store, or persist ad hoc JSON files. PostgreSQL is premature operational complexity; Qdrant is not the canonical record; multiple JSON files make transactional consistency and querying harder.

**Consequences:** Local setup and inspection remain simple while the simulation gains transactional guarantees. Persistence access must remain behind repository boundaries so a later concurrency requirement can justify a different database without changing domain logic.

### 2026-07-11: Author game packages in YAML and validate with Pydantic

**Status:** Accepted

**Context:** Rule and scenario packages must be comfortable to hand-author, inspect, diff, and eventually generate, while the simulation kernel requires strict typed inputs. JSON is verbose for substantial scenario content, and raw YAML mappings are too permissive to form a runtime boundary.

**Decision:** Use YAML as the package authoring format. Safely parse package files and validate them into strict Pydantic models before simulation logic can access them. Require explicit schema versions, package identities and versions, stable record identifiers, valid cross-references, and supported operations. Do not permit executable YAML constructs.

**Alternatives considered:** Use JSON, TOML, or unvalidated YAML dictionaries at runtime. JSON is less author-friendly for narrative content; TOML is awkward for deeply nested world data; raw dictionaries allow ambiguous types and delayed failures.

**Consequences:** Authors and future generation tools get readable source files, while the kernel receives typed trusted models. Package validation becomes an early implementation boundary and requires high-signal schema and reference tests.

### 2026-07-11: Use recorded seeded randomness only for explicit checks

**Status:** Accepted

**Context:** Uncertainty can make checks and consequences interesting, but uncontrolled randomness makes failures difficult to reproduce and lets generated narration obscure why an outcome occurred.

**Decision:** Resolve outcomes deterministically unless a rule explicitly requests a random check. The simulation arbiter owns a seeded pseudorandom source, persists its state, and records the purpose, parameters, and result of every canonical draw. LLMs cannot supply random outcomes. The arbiter accepts an injected random source for tests.

**Alternatives considered:** Make all outcomes deterministic, use unrecorded process randomness, or let an LLM choose uncertain results. Fully deterministic play reduces uncertainty; unrecorded and LLM-selected outcomes cannot be reliably replayed or audited.

**Consequences:** Canonical outcomes can be explained and reproduced. Unit tests can force boundary results through an injected source, while seeded integration tests can verify longer stable flows without coupling every unit test to one pseudorandom algorithm.

### 2026-07-11: Serialize eligible activities deterministically

**Status:** Accepted

**Context:** Multiple environmental events, NPCs, and System director hooks may become eligible when one player action advances simulation time. True simultaneous mutation would require conflict-resolution semantics and make causal ordering harder to inspect.

**Decision:** Resolve scheduled activities serially in a deterministic queue ordered by simulation time, phase priority, and stable insertion sequence. At the same time, scheduled environmental events precede NPC activity, which precedes System director hooks. The triggering player action resolves before the activities made eligible by its time advancement. Record ordering metadata in the step trace.

**Alternatives considered:** Allow concurrent state mutation, or rely on incidental database or collection ordering. Concurrency creates avoidable conflicts; incidental ordering is not reproducible or meaningful.

**Consequences:** Each activity sees a defined committed predecessor state, and causal chains can be replayed. The initial model does not provide true simultaneity; a future rule set requiring simultaneous declarations would need an explicit proposal-batch and conflict-resolution design.

### 2026-07-11: Maintain a canonical domain glossary

**Status:** Accepted

**Context:** The architecture uses familiar terms with narrow meanings, including System director, System interface, intent, action proposal, outcome, event, perception, observation, memory, and belief. Without explicit definitions, documentation, prompts, schemas, code, and tests can silently use incompatible concepts.

**Decision:** Maintain `doc/glossary.md` as the canonical domain vocabulary. Project artifacts use its terms consistently and update it when accepted design introduces or changes a concept. Avoid ambiguous bare terms such as System and director in technical writing.

**Alternatives considered:** Rely on conversational context or define terms independently in each document. Conversation context is temporary; local definitions drift and make cross-component contracts harder to understand.

**Consequences:** Naming becomes part of the information architecture and can guide schemas, interfaces, prompts, and tests. Glossary changes require attention because they may signal a domain-model or public-contract change rather than a prose edit.

### 2026-07-11: Invoke the System director through rate-limited event hooks

**Status:** Accepted

**Context:** Invoking the System director after every player action would add latency and encourage constant intervention even when the world has no need for creative direction. Unspecified invocation timing would also make behavior difficult to test and explain.

**Decision:** Invoke the System director only when an explicit hook configured by a rule or scenario package becomes eligible. Hooks may respond to world creation, matching canonical events, scenario milestones, or elapsed simulation time. Each hook declares simulation-time frequency or count limits, and each eligibility decision is recorded in the simulation-step trace.

**Alternatives considered:** Invoke after every player action, or let application code call the System director opportunistically. Both approaches obscure causality, add unnecessary LLM calls, and weaken scenario control.

**Consequences:** Creative direction becomes event-driven, rate-limited, and reproducible at the eligibility layer. Packages control when intervention is appropriate, while the simulation arbiter still validates every resulting action proposal.

### 2026-07-11: Validate and retain NPC belief revisions

**Status:** Accepted

**Context:** Beliefs are authoritative only as character-internal state and may be false, but LLM-generated sensemaking still must not write durable data without a typed, inspectable boundary. Belief change also loses explanatory value if the previous belief and its basis are overwritten.

**Decision:** NPC sensemaking produces structured belief revision proposals for adding, reinforcing, weakening, replacing, retracting, or expressing uncertainty about beliefs. The actor runtime validates ownership, source references, supported operations, and confidence bounds before applying a revision to that NPC alone. Preserve revision history and never infer player beliefs automatically.

**Alternatives considered:** Let sensemaking overwrite beliefs directly, require every belief to match canonical truth, or omit revision history. Direct writes weaken validation; truth matching prevents mistaken beliefs; overwriting history makes character reasoning difficult to inspect.

**Consequences:** NPC belief evolution can be audited without granting it canonical authority. Rule-based and LLM-assisted sensemaking can share one contract. Implementation is postponed until after the initial vertical slice, which uses asymmetric observations and hidden facts without mutable belief state.

### 2026-07-11: Use bounded hybrid memory retrieval after the vertical slice

**Status:** Accepted

**Context:** Supplying an NPC's complete episodic history would exceed useful context, while semantic search alone can omit recent or highly significant experiences. Qdrant availability must not determine whether durable character history exists.

**Decision:** When episodic memory is enabled, assemble bounded NPC context from configured high-salience, recent, and semantically relevant memories. Deduplicate results, retain stable identifiers and provenance, enforce explicit source and total budgets, and filter all retrieval by NPC ownership. If Qdrant is unavailable, fall back to recent and high-salience durable memories.

**Alternatives considered:** Include all memories, use semantic similarity alone, or make the vector index authoritative. Full history does not scale; similarity alone is an incomplete relevance model; an authoritative vector index weakens durability and auditability.

**Consequences:** Memory selection can be inspected and tuned as context engineering. The initial vertical slice postpones episodic memory and Qdrant integration, so its LLM-assisted NPC cannot rely on prior conversations or observations and must not receive chat history disguised as memory.

### 2026-07-11: Require structured functional LLM outputs with bounded repair

**Status:** Accepted

**Context:** Player interpretation, NPC decisions, and System director proposals can affect later canonical resolution. Loosely formatted prose and best-effort parsing create ambiguous operations and allow malformed output to cross the simulation trust boundary.

**Decision:** Require strict Pydantic-validated output from every functional LLM role. On validation failure, allow one repair attempt using the same context envelope, schema, and validation errors. A second failure produces a role-specific safe result: player clarification, configured NPC no-op or deterministic fallback, or skipped System director action proposal. The narrator remains prose-producing because its output is presentation only.

**Alternatives considered:** Parse operations from prose, retry indefinitely, or accept partially valid output. Prose parsing is brittle; unlimited repair adds latency and loops; partial acceptance makes behavior difficult to reason about.

**Consequences:** Malformed model output cannot directly affect canonical state. Original output, errors, repair output, and final disposition become part of the simulation-step trace. Local model support for the required structured-output protocol must be verified empirically before implementation depends on it.

### 2026-07-11: Use Storm at Greybridge as the initial scenario

**Status:** Accepted

**Context:** The vertical slice needs concrete content that exercises spatial perception, asymmetric information, two decision policies, action-driven time, scheduled pressure, optional System director intervention, rule-governed uncertainty, progression, and multiple player choices without combat or long-term NPC memory.

**Decision:** Set the initial scenario at a remote waystation beside an unstable bridge during rising floodwater. The player and an injured LLM-assisted courier begin at the waystation with medicine. A rule-driven caretaker at the bridge can perceive structural damage hidden from them. A scheduled flood threatens the route, and a world-creation System director hook may propose an optional crossing objective. Fieldcraft supports inspection, reinforcement, safe crossing, and visible progression.

**Alternatives considered:** Begin with an abstract test room, a combat encounter, or a conversation-only scene. A test room lacks meaningful stakes; combat exceeds scope; conversation alone does not exercise the location graph, scheduling, object interactions, or environmental consequences.

**Consequences:** One small scenario can test the complete initial architecture through several valid branches. Because memory and mutable beliefs are postponed, the scenario must rely on current observations, identity, goals, and current plans rather than sustained conversational recall.

### 2026-07-11: Provide a separate read-only inspection page

**Status:** Accepted

**Context:** The project is intended to teach context engineering and agentic-system design. Player-facing narration hides the intermediate information needed to explain eligibility, context selection, model proposals, validation, state transitions, and perception boundaries.

**Decision:** Add a separate read-only Streamlit development page that presents each simulation-step trace as an ordered causal timeline. It exposes context manifests, functional LLM output and repair, scheduling, validation, random draws, canonical changes, observations, and presentation. It supports comparison between canonical world state and one character's perception snapshot, but cannot edit state directly.

**Alternatives considered:** Mix diagnostics into the player interface, rely only on application logs, or provide a general state editor. Mixed diagnostics damage the experience; logs poorly express linked domain records; direct editing bypasses canonical authority.

**Consequences:** Information flow becomes inspectable without weakening the simulation arbiter. Trace records need stable identifiers and provenance. Reset remains a separate explicit development operation.

### 2026-07-11: Delegate through repository task briefs

**Status:** Accepted

**Context:** The planning conversation contains accepted choices, rejected alternatives, speculation, and obsolete assumptions. Passing it wholesale to implementation agents would pollute their context, while relying on chat history would make project knowledge unavailable to fresh agents and separate chats.

**Decision:** Treat repository artifacts as durable project memory and a bounded task brief as the unit of delegation. Each Ready task declares an exact context manifest, fixed assumptions, scope, acceptance criteria, verification, stop conditions, and handoff format. Delegated agents do not update governance artifacts unless explicitly authorized. Create detailed briefs just in time after their dependencies stabilize.

**Alternatives considered:** Pass the complete planning transcript, give each agent the entire documentation set, or delegate from a short untracked prompt. Full history and full documentation create context pollution; untracked prompts lose decisions and traceability.

**Consequences:** Fresh and lower-cost agents can execute narrow work without reconstructing the project. The architect and integrator own ambiguity resolution and task readiness. Custom agents and repo skills are introduced only after real repeated work shows stable role or workflow requirements.

### 2026-07-11: Configure a Terra experimenter for evidence tasks

**Status:** Accepted

**Context:** Ready preflight tasks need reproducible environment evidence but do not require the planning agent's broader context. The user wants these bounded tasks to use GPT-5.6 Terra with high reasoning while retaining permission to write an authorized report and task handoff.

**Decision:** Add the project custom agent `terra_experimenter` under `.codex/agents/`. Configure it with `gpt-5.6-terra`, high reasoning, and workspace-write sandboxing. Restrict its instructions to Ready evidence or experiment task briefs and their explicitly authorized files. Task briefs remain the source of task-specific context.

**Alternatives considered:** Use the planning agent, rely on inherited model selection, or embed the entire task inside the custom-agent instructions. The planning agent is unnecessarily broad; inheritance does not guarantee the requested model; embedding tasks would mix stable role configuration with changing work.

**Consequences:** A fresh Codex task can select a predictable lower-cost experiment role without receiving this planning transcript. The agent still inherits repository safety boundaries and must stop on design gaps or unauthorized mutations.

### 2026-07-11: Disable Gemma thinking for functional LLM roles

**Status:** Accepted

**Context:** With thinking enabled, four of five provisional player-interpreter trials exhausted 600 completion tokens inside `reasoning_content` and emitted empty `message.content`. Successful NPC trials also spent most output tokens on hidden reasoning. Functional roles require short validated data rather than an internal reasoning transcript.

**Decision:** For functional calls to the local Gemma service, send `chat_template_kwargs.enable_thinking=false` at request time. Use `message.content` as the candidate structured output and never substitute `reasoning_content`. Continue to use JSON response formatting only as syntactic assistance, strict Pydantic validation as the authority boundary, one repair attempt, and role-specific safe failure.

**Alternatives considered:** Increase output-token limits, parse `reasoning_content`, or leave thinking enabled for all roles. Larger limits waste latency without guaranteeing content; reasoning transcripts are not the functional contract; always-on thinking caused measured failures.

**Consequences:** In the controlled preflight, thinking-disabled player and NPC fixtures were strict-valid in all ten trials, used far fewer completion tokens, and returned substantially faster. The gateway must still handle models or servers that ignore the extension and must trace the request setting and final disposition.

### 2026-07-11: Standardize the initial Python project foundation

**Status:** Accepted

**Context:** Delegated implementation needs one reproducible runtime, dependency workflow, package layout, and quality-gate interface before domain contracts are introduced. The development machine already provides Python 3.12 and `uv`, while the repository currently has no Python package metadata or application dependencies.

**Decision:** Target Python 3.12 exclusively for the initial application, recording `3.12` in `.python-version` and `>=3.12,<3.13` in project metadata. Use `uv` for environments and dependency locking, commit `uv.lock`, use Hatchling with a `src/llm_system` package layout, and initialize the `llm-system` distribution at version `0.1.0`. Begin with no runtime dependencies and only `pytest`, Ruff, and mypy as development dependencies. Expose installation, testing, formatting, linting, type-checking, and aggregate checks through stable Make targets.

**Alternatives considered:** Support several Python minor versions immediately, use Poetry or pip-managed requirements files, use setuptools or a flat package layout, or declare the anticipated application stack up front. Multi-version support adds a test matrix before distribution is a goal; Poetry and parallel requirements files add another project model; setuptools is more machinery than this package needs; a flat layout can hide packaging errors; speculative dependencies obscure which feature justified each library.

**Consequences:** Fresh sessions and delegated agents can reconstruct and verify the same small environment with `uv sync` and Make. The application is intentionally constrained to Python 3.12 until a later accepted change widens or advances the runtime. Pydantic, PyYAML, FastAPI, Streamlit, database helpers, and model clients must be introduced by the tasks that first require them.

### 2026-07-12: Use self-contained exact-version game package manifests

**Status:** Accepted

**Context:** Rule and scenario content must be independently authorable, inspectable, versioned, and safe to load without coupling it to Python source modules. Persistent worlds must be able to identify the exact content contracts they use, while the initial vertical slice does not need a general dependency resolver or multi-file merge semantics.

**Decision:** Store packages under `game_packages/rules/<package-id>/<package-version>/` and `game_packages/scenarios/<package-id>/<package-version>/`. Each self-contained directory has `manifest.yaml` with a shared strict identity envelope: schema version `1`, lowercase kebab-case identifier, stable `MAJOR.MINOR.PATCH` version, `rule` or `scenario` type, non-empty title, and one relative YAML entrypoint. A scenario pins exactly one rule pack by exact identifier and version; a rule pack has no package dependency. Validate safely parsed YAML into strict frozen Pydantic 2 models, forbid unknown fields, verify directory identity and entrypoint containment, and expose one application-owned loading function and manifest error.

**Alternatives considered:** Keep authored YAML inside the Python package, overwrite each package identifier with only its latest version, allow scenario dependency ranges, support multiple entrypoint files with merge semantics, or expose PyYAML and Pydantic errors directly. These choices respectively mix code and content lifecycles, prevent exact restart compatibility, require dependency resolution, introduce undefined merge behavior, or leak implementation libraries across the application boundary.

**Consequences:** Multiple exact package versions can coexist, scenario compatibility is deterministic, and downstream code receives a trusted typed manifest rather than raw mappings. Pydantic and PyYAML become justified runtime dependencies. Prerelease versions, dependency ranges, content parsing, dependency resolution, includes, and multi-file composition require later schema-versioned decisions rather than implicit loader behavior.

### 2026-07-12: Separate authored spatial definitions from runtime state

**Status:** Accepted

**Context:** Scenario packages need stable graph topology, while floods, damage, barriers, and other world events must change canonical state without mutating loaded package definitions. Free-form location descriptions would also bundle perceptible and hidden facts into text that the deterministic perception engine could not filter safely.

**Decision:** Model authored topology with strict frozen `LocationDefinition`, `ConnectionDefinition`, and `SpatialGraphDefinition` records. A location initially contains only a stable lowercase kebab-case identifier and non-blank name. Each connection is one explicit directed edge with its own identifier, name, source and destination identifiers, and strictly positive `base_traversal_seconds`. Canonical simulation durations use integer seconds. The graph accepts authored YAML-style order and exposes immutable ordered collections. Runtime availability, requirements, damage, visibility, coordinates, and perceptible features are separate later contracts.

**Alternatives considered:** Combine definitions and mutable state, use implicit bidirectional edges, derive connection identifiers from endpoints, represent time as configurable ticks or floating-point minutes, or put canonical details in prose descriptions. These choices blur package and world ownership, hide directional behavior, prevent parallel routes, make duration semantics ambiguous, or weaken deterministic perceptual filtering.

**Consequences:** Packages remain immutable inputs while runtime state can evolve through the simulation arbiter. Reverse travel requires a second explicit connection and may have different timing or later conditions. Semantic graph validation remains a separate boundary that checks identifier uniqueness, endpoint existence, self-loops, and reachability after structural models are available.

### 2026-07-12: Model scenario inhabitants as discriminated entity definitions

**Status:** Accepted

**Context:** The scenario needs characters, medicine, reinforcement materials, possession, spatial placement, and bounded NPC context. Treating all records as generic dictionaries would weaken type boundaries, while giving every entity location and holder fields would create contradictory sources of truth for possessed objects.

**Decision:** Use `Entity` as the umbrella for addressable spatial things and define strict frozen `ObjectDefinition`, `PlayerCharacterDefinition`, and `NpcCharacterDefinition` variants under one discriminator. All share identity and name. Characters reference a rule-pack character archetype and start at a location. Objects reference a rule-pack object archetype and use a discriminated initial placement that is either a location or one possessing character, never both. NPCs additionally require an identity summary, ordered goal definitions, optional initial plan, and a structured reference to a rule, LLM, or hybrid decision policy. An ordered immutable entity collection preserves authoring order without making reference validity order-dependent.

**Alternatives considered:** Use one entity model with many optional fields, store both effective location and holder on objects, embed executable policy logic in characters, infer mechanics from names or prose, or require referenced records to appear first. These choices create invalid field combinations, duplicate spatial truth, mix scenario data with runtime code, make rules depend on language, or add irrelevant ordering constraints.

**Consequences:** Generic consumers can operate on a typed entity union while character and object concerns remain distinct. Possessed-object location is derived through its holder. Rule-pack archetypes and policies remain references until their contracts exist. A later validation boundary must resolve all location, possession, archetype, and policy references, enforce exactly one player, and check uniqueness before world creation.

### 2026-07-12: Begin rule-pack content with typed reference catalogs

**Status:** Accepted

**Context:** Scenario objects, characters, and NPCs now reference rule-pack archetypes and decision policies, but those targets do not yet exist. Cross-package validation cannot be complete until the rule side has typed identities. Defining full mechanics or arbitrary settings now would invent semantics before action, skill, effect, and actor-runtime contracts exist.

**Decision:** Define rule-pack content schema version `1` as one strict frozen `RulePackDefinition` containing ordered immutable catalogs of `ObjectArchetypeDefinition`, `CharacterArchetypeDefinition`, and `DecisionPolicyDefinition`. Archetypes initially contain only stable ID and name. Policy definitions contain stable ID, name, and the same `rule`, `llm`, or `hybrid` type vocabulary used by NPC references. The rule pack owns versioned policy declarations; a later application registry owns executable implementations. Empty catalogs and duplicate IDs remain structurally representable until semantic validation.

**Alternatives considered:** Validate scenario references against hard-coded strings, put executable policy code in YAML, add generic property or settings dictionaries, define full game mechanics immediately, or let the application registry be the only policy catalog. These choices respectively hide contracts, violate the code/data boundary, postpone type safety, broaden scope prematurely, or remove package-versioned compatibility information.

**Consequences:** Scenario references gain explicit typed targets without pretending the mechanics system is complete. Cross-package validation can later compare archetype IDs and policy ID/type pairs, then compare policy declarations with the application implementation registry. Actions, abilities, skills, effects, and structured policy configuration require later accepted schema versions.

### 2026-07-12: Load each game package atomically as one typed pair

**Status:** Accepted

**Context:** Manifest-only loading was a useful intermediate boundary before rule and scenario content roots existed. Keeping it public after those roots exist would allow callers to treat package identity as usable while its entrypoint is missing or invalid, and a generic manifest-definition tuple could permit accidental rule and scenario mismatches.

**Decision:** Expose one `load_game_package` operation that loads exactly one package-version directory and returns either a strict immutable `LoadedRulePackage` or `LoadedScenarioPackage`, pairing the concrete manifest with its matching typed definition. Use the validated manifest type as the sole entrypoint-schema selector. Remove the public manifest-only loader and replace its manifest-specific error with one `GamePackageLoadError` that chains the underlying failure. Do not return partial results, infer type from entrypoint keys, resolve a scenario's required rule pack, or perform relational and graph validation during this structural loading step.

**Alternatives considered:** Retain a public manifest-only loader, return only entrypoint content, return an untyped tuple, duplicate package type on the loaded wrapper, infer type from content shape, or load a scenario and its rule dependency together. These choices respectively expose partial trust, discard identity and compatibility data, weaken type pairing, create two type sources, hide manifest mistakes, or mix file loading with package composition.

**Consequences:** Application code receives one coherent structurally trusted package or one stable application-owned failure. Concrete wrapper classes provide runtime narrowing without duplicated discriminators. Dependency resolution, cross-package references, graph invariants, uniqueness, and playability remain explicit later validation stages; a future broken-package browser would require a separate diagnostic API rather than weakening the usable-package loader.

### 2026-07-12: Validate loaded package pairs with structured dependency-aware issues

**Status:** Accepted

**Context:** Structurally loaded packages may still contain duplicate identities, unresolved or mistyped references, a mismatched rule dependency, invalid player setup, or unusable topology. Package authors benefit from seeing independent defects together, but blindly running checks after their prerequisites fail produces misleading cascades. Downstream code also needs a type-level distinction between loaded documents and a relationally coherent pair.

**Decision:** Expose `validate_game_packages` over one `LoadedRulePackage` and one `LoadedScenarioPackage`, returning a strict immutable `ValidatedGamePackages` pair or raising one `GamePackageValidationError` containing deterministic ordered immutable `ValidationIssue` records. Issues use a compact `ValidationIssueCode` string enum plus authored numeric-index paths and human messages. Enforce uniqueness within typed namespaces, exact scenario-to-rule identity, all current graph, placement, archetype, and policy references, policy-type agreement, exactly one player, no self-loops, and directed reachability of every location from the player's start. Aggregate independent issues but gate cross-package or reachability checks when their premises are invalid. Unused definitions and one-way topology remain valid.

**Alternatives considered:** Fail on the first issue, use free-form error strings, require identifiers to be globally unique, infer reference targets across namespaces, validate against a mismatched rule package, require strong graph connectivity, treat unused definitions as errors, or combine policy-registry readiness with package relationships. These choices respectively slow authoring, weaken tooling, create naming friction, introduce ambiguity, generate cascades, forbid intentional one-way routes, confuse correctness with linting, or mix distinct validation authorities.

**Consequences:** Package authors and future generation tools receive stable multi-issue feedback, while later code can require a relationally validated pair. `ValidatedGamePackages` is deliberately not proof of executable policy availability, supported operations, persistent-world compatibility, general playability, or readiness for world creation; those remain later validation layers.

### 2026-07-12: Author Greybridge first as a validated content foundation

**Status:** Accepted

**Context:** The current package schemas can express Greybridge's topology, cast, objects, placements, NPC motivations, and policy references, but not actions, Fieldcraft, bridge condition, perception facts, scheduled flood activity, director hooks, objectives, checks, or progression. Waiting for every mechanic would leave the loading and semantic-validation pipeline without real authored content, while inventing placeholder dictionaries or hiding mechanics in prose would undermine the typed boundary.

**Decision:** Author `greybridge-rules` version `0.1.0` and `storm-at-greybridge` version `0.1.0` as the first repository content foundation. Include exactly the currently representable three-location bidirectional graph, player, courier, caretaker, medicine, reinforcement materials, archetype catalogs, NPC goals and plans, and LLM/rule policy declarations. Use 60-second traversal between waystation and span and 120-second traversal between span and far bank in both directions. Load and semantically validate the real YAML files in repository tests. Do not add unsupported fields or describe this package version as playable or complete.

**Alternatives considered:** Delay all content until mechanics exist, add free-form extension mappings, encode state and rules in names or narrative fields, call the rule package generic core rules, or treat the skeleton as a complete scenario. These choices respectively postpone end-to-end evidence, weaken validation, confuse prose with authority, claim unproven reuse, or conceal major missing systems.

**Consequences:** The project gains one inspectable real package pair that exercises manifests, typed entrypoints, dependency matching, references, topology, and validation. Later schema versions can extend the package from concrete evidence. Package discovery, wheel data distribution, world creation, and the remaining vertical-slice mechanics stay separate tasks.

### 2026-07-12: Use closed operation-specific action proposal contracts

**Status:** Accepted

**Context:** Player interpreters, NPC decision policies, and the System director all submit untrusted proposals across the simulation boundary. A generic operation string with an arbitrary argument mapping would defer schema errors to resolver code, weaken functional LLM validation, and allow package content to imply mechanics that the kernel cannot enforce. System director proposals also describe world-level interventions rather than actions performed by a character.

**Decision:** Represent proposals as closed discriminated unions of strict operation-specific Pydantic contracts. Each supported operation owns its typed arguments. Separate actor-action proposals, which identify the intended actor, from world-action proposals, which pass through the same simulation-arbiter entry boundary without treating the System director as a character. Rule packs may configure kernel-supported operations and their resolution rules, but a genuinely new operation requires a kernel contract and resolver.

**Alternatives considered:** Use one proposal with `operation: str` and a generic argument dictionary, treat every proposal as an actor action, or allow packages to create new operations by naming them. These choices respectively spread validation through runtime branches, corrupt the actor model, or claim executable mechanics that the stable kernel does not implement.

**Consequences:** Functional roles receive precise output schemas, resolvers can narrow proposal types safely, and unsupported mechanics fail at a clear trust boundary. Adding an operation requires a deliberate kernel API change. Actor and world proposal families share arbiter authority and tracing conventions without sharing false domain semantics.

### 2026-07-12: Distinguish rejected, failed, and succeeded outcomes

**Status:** Accepted

**Context:** An invalid proposal that never enters the world and a valid in-world attempt that fails are mechanically different. Collapsing both into failure would make time costs, consequences, actor feedback, narration, and inspection traces ambiguous.

**Decision:** Resolve every action proposal into exactly one immutable structured outcome with status `rejected`, `failed`, or `succeeded` and a stable machine-readable reason code. Rejection means the proposal could not be attempted and therefore has no canonical effects or time advancement. Failure means a valid attempt did not achieve its goal and may still incur rule-defined time, transitions, costs, or events. Success means a valid attempt achieved its defined result. Every outcome retains its originating proposal identity, and only the simulation arbiter may commit the effects it describes.

**Alternatives considered:** Use a boolean success flag, treat invalid proposals as failed attempts, or let resolvers mutate canonical state before returning a result. These choices respectively lose meaningful state, invent in-world consequences for commands that never occurred, or prevent atomic validation, tracing, and testing of proposed effects.

**Consequences:** Callers and presentation code can distinguish clarification from dramatic failure, while valid failures can still advance the simulation. Outcome contracts must represent reason codes and effects explicitly. Resolver logic remains pure enough to test before the arbiter commits its result.

### 2026-07-12: Retain typed canonical events without full event sourcing

**Status:** Accepted

**Context:** Perception, inspection, causal explanation, and replay diagnostics need durable records of what occurred. Generic payload dictionaries would weaken domain validation, while embedding prose or observer lists would conflate canonical facts with presentation and perception. Requiring the event log to be the sole source for rebuilding world state would add event-sourcing complexity before the vertical slice demonstrates a need for it.

**Decision:** Represent canonical events as a closed discriminated union of strict event-specific contracts. Every event has stable identity, simulation time, an event-type discriminator, a causation link to its originating outcome, and an operation-specific factual payload. Events contain mechanical facts rather than narration, and the perception engine independently derives observer-specific observations. Persist current canonical world state directly while retaining events as durable causal history; do not require event replay as the sole reconstruction mechanism. Rejected proposals remain trace records and produce no canonical event.

**Alternatives considered:** Store generic event names and payload mappings, put player visibility or generated descriptions on events, discard events after updating state, or adopt full event sourcing immediately. These choices respectively weaken contracts, leak presentation concerns into reality, destroy causal evidence, or impose additional schema-evolution and replay obligations prematurely.

**Consequences:** Events can support deterministic perception, inspection, and diagnostic replay while state loading remains straightforward. Each new canonical fact needs an explicit event variant. Persistence must atomically commit direct state changes, events, and trace records later, but world recovery does not depend on replaying the complete event history.

### 2026-07-12: Separate proposal payloads from trusted submission metadata

**Status:** Accepted

**Context:** Functional LLMs and decision policies are untrusted proposal producers. If their structured output includes caller identity, intended authority, or trace provenance, a malformed or adversarial output could impersonate another actor, claim world-level authority, or forge diagnostic context. Putting cognition such as intent into the mechanical payload would also risk treating a character-internal statement as canonical reality.

**Decision:** Keep the operation-specific action proposal payload separate from a trusted application-created proposal-submission envelope. The payload contains only the discriminated operation and its typed arguments. The envelope supplies stable proposal identity, source role and identity, intended actor when applicable, simulation-step context, and trace provenance. Generated output cannot provide or override envelope metadata. The simulation arbiter validates both operation legality and whether the trusted source may submit for the intended actor or world-level operation. Intent and reasoning remain separate cognition or trace artifacts.

**Alternatives considered:** Ask each functional role to generate the complete envelope, trust a payload's actor identifier without source authorization, or embed intent and reasoning in the mechanical proposal. These choices respectively allow provenance forgery, permit cross-actor impersonation, or blur internal cognition with canonical action.

**Consequences:** Functional output schemas become smaller and safer, while application code owns authority and causality metadata. Proposal producers can share operation contracts without sharing permissions. The kernel needs explicit submission-envelope and source-authorization contracts in addition to operation validation.

### 2026-07-12: Use namespace-aware operation references and connection-based movement

**Status:** Accepted

**Context:** Location, connection, character, and object identifiers occupy separate namespaces, so a generic target identifier would be ambiguous. Movement by destination would also discard which directed edge an actor attempted to traverse, even though parallel connections may have different time costs and later availability or requirements.

**Decision:** Give each operation arguments constrained to its permitted domain kinds. Move identifies one authored directed connection. Speak and help identify a character. Take identifies an object. Use identifies the used object and a typed target reference. Observe distinguishes an explicit surroundings target from typed location, connection, character, and object targets. Wait contains a strictly positive integer duration in simulation seconds. The simulation arbiter resolves every reference against canonical state.

**Alternatives considered:** Use one universal `target_id`, move directly to a destination location, infer reference namespaces by searching for matching IDs, or represent observation of surroundings with a missing target. These choices respectively create ambiguous contracts, lose route identity, make behavior depend on namespace collisions, or overload absence with domain meaning.

**Consequences:** Functional schemas express legal reference shapes before resolution, parallel and directional connections remain mechanically meaningful, and reference failures can produce precise rejection reasons. The proposal model needs small typed target-reference variants rather than a generic identifier field.

### 2026-07-12: Add explicit canonical runtime-state contracts before the arbiter

**Status:** Accepted

**Context:** The package layer now provides immutable authored topology and entity definitions, but the simulation arbiter must resolve operations against mutable facts such as current locations, possession, connection availability, and simulation time. The M3 roadmap previously moved directly from action contracts to the arbiter, leaving no owned representation for those facts.

**Decision:** Add a canonical runtime-state contract task between action contracts and the simulation arbiter. Keep authored package definitions immutable and represent changing world facts separately. Begin with only the state required by the initial supported operations: simulation time, character locations, object placement or possession, and connection availability. Add richer conditions and Greybridge-specific state only after their rule semantics are accepted.

**Alternatives considered:** Mutate loaded package definitions, hide runtime facts inside the arbiter implementation, or define all anticipated world-state concepts immediately. These choices respectively destroy package immutability, leave public resolution semantics implicit, or overdesign contracts before supported mechanics exist.

**Consequences:** The arbiter receives a clear canonical input and package content remains reusable as immutable initialization data. M3 gains one additional dependency and task brief, but supported-operation tests can exercise explicit state instead of mocks or ad hoc dictionaries.

### 2026-07-12: Replace immutable world-state snapshots atomically

**Status:** Accepted

**Context:** In-place mutation during validation and resolution could leave partial canonical changes when a later rule rejects or fails, and it makes before-and-after behavior harder to test and inspect. The initial world is small enough that optimizing around mutable large-state storage would be premature.

**Decision:** Represent canonical runtime state as an immutable validated `WorldState` snapshot. Resolution does not mutate its input. When committing a non-rejected outcome, the simulation arbiter applies the complete typed change set and produces one replacement snapshot; rejection returns the original snapshot unchanged. The later persistence boundary atomically stores the replacement snapshot, canonical events, and simulation-step trace.

**Alternatives considered:** Mutate domain objects in place, rely on rollback code after partial application, or optimize immediately for incremental large-world mutation. These choices respectively obscure side effects, add failure paths, or trade clarity for performance the vertical slice does not require.

**Consequences:** Kernel tests can compare explicit before-and-after snapshots, rejection is mechanically side-effect free, and atomic persistence has a clear unit of work. Snapshot copying may eventually need internal optimization for large worlds, but that optimization must preserve the immutable public semantics.

### 2026-07-12: Sequence M3 contracts by their type dependencies

**Status:** Accepted

**Context:** The original M3 roadmap combined action proposals, outcomes, and events before runtime state. Outcomes need typed state changes, and those changes cannot have precise contracts until the canonical runtime-state model exists. The combined unit would either force generic effects or make one delegated task own several unstable boundaries.

**Decision:** Split the start of M3 into action proposal and trusted submission contracts; canonical runtime-state contracts; outcome, state-change, and canonical-event contracts; and then the simulation arbiter with supported operations. Keep recorded randomness, the simulation clock and scheduler, and deterministic perception after those foundations.

**Alternatives considered:** Keep one large contract task, define effects as arbitrary dictionaries, or design outcome types before their referenced state. These choices respectively broaden delegation context, weaken type safety, or create immediate contract churn.

**Consequences:** Each task has a smaller coherent responsibility and a real dependency boundary. M3 contains more task briefs, but downstream agents receive stable types instead of guessing at missing semantics.

### 2026-07-12: Inject UUID runtime identities and type submission sources

**Status:** Accepted

**Context:** Runtime proposals and their later outcomes, events, and simulation steps need stable identities for causation, persistence, and inspection. Generating identifiers inside model construction would add hidden nondeterminism, while generic source-role strings and identifiers would permit incomplete or meaningless provenance combinations. Authored package identifiers serve a different, human-readable purpose.

**Decision:** Use standard-library UUID values for runtime proposal, simulation-step, outcome, and event identities. The application injects them; Pydantic models and proposal producers do not generate them. Keep authored package identifiers as readable domain strings. Represent proposal-submission sources as a closed discriminated union with source-specific provenance: player interpreter, NPC decision policy identifying NPC and configured policy, System director identifying its eligible hook, and scheduled activity when introduced. Context-manifest and other trace references may remain application-assigned opaque identities until their contracts are designed.

**Alternatives considered:** Generate UUIDs as model defaults, let LLMs return IDs, reuse authored identifiers for runtime records, or use a source-role string with optional generic fields. These choices respectively hide nondeterminism, allow identity forgery, conflate definitions with occurrences, or admit invalid source metadata.

**Consequences:** Tests and replay can inject fixed identities, causal records have collision-resistant keys without a new dependency, and each source variant proves its required provenance. Application orchestration must own ID generation, while domain models remain deterministic constructors.

### 2026-07-12: Defer concrete world-action proposals to their owning mechanics

**Status:** Accepted

**Context:** The initial actor operations have accepted argument semantics, but the first known world operation, offering an optional objective, depends on objective lifecycle and System-interface mechanics planned for M6. Defining an empty union or placeholder objective payload now would add unusable code or freeze an underspecified schema.

**Decision:** Implement the first action-contract task with the seven accepted actor-operation payloads and trusted actor-action submissions only. Preserve the architectural requirement that world actions use a separate typed proposal and submission family, but introduce its first concrete contract with the mechanics task that owns the operation.

**Alternatives considered:** Add an empty world-action abstraction, create a generic world-operation payload, or define the optional-objective schema during actor-action work. These choices respectively provide no executable value, weaken the closed-operation boundary, or pull later lifecycle semantics into the wrong milestone.

**Consequences:** TASK-011 remains cohesive and directly testable. The System director cannot yet submit an executable world action, which is intentional until its supported operation is designed. Later world-action work must not reuse actor-action submissions or treat the System director as a character.

### 2026-07-12: Model runtime state as an ID-linked mutable-facts overlay

**Status:** Accepted

**Context:** The validated packages already own immutable names, topology, traversal durations, archetypes, goals, and initial definitions. Copying those facts into runtime state would create competing sources that could diverge, while the arbiter still needs explicit changing facts for resolution.

**Decision:** Define canonical runtime state as a minimal immutable overlay linked to validated package definitions by stable authored identifiers. Character state records current location, object state records current location or possessor, connection state records current availability, and the world snapshot records simulation time plus immutable collections of those overlays. Arbiter resolution receives both the validated package pair and the runtime snapshot. Persistent world identity and recorded package versions belong to the later M4 world-record boundary rather than this pure M3 snapshot.

**Alternatives considered:** Copy complete entity and graph definitions into each snapshot, mutate loaded package records, or make runtime state self-describing without its validated package context. These choices respectively duplicate authority, violate package immutability, or require definition-owned facts to drift into the state layer.

**Consequences:** Authored and changing facts have one owner each, snapshots remain compact, and resolution must explicitly join overlays to validated definitions. World-readiness validation must later prove that the overlay references and covers the package pair it accompanies.

### 2026-07-12: Require complete overlays at world readiness

**Status:** Accepted

**Context:** A sparse overlay would require implicit rules such as treating a missing connection state as available or consulting an object's initial package placement after play has begun. Those fallbacks create hidden defaults and make it unclear whether absence means unchanged, unknown, or invalid.

**Decision:** A world-ready snapshot contains exactly one character-state record per authored character, one object-state record per authored object, and one connection-state record per authored connection. A separate semantic world-readiness validator compares the structurally valid snapshot with its validated package pair and rejects duplicates, omissions, extra runtime records, and invalid references. Structural Pydantic construction remains independent of package lookup.

**Alternatives considered:** Store only changed records, apply implicit availability defaults during resolution, enforce package completeness inside individual model constructors, or keep consulting initial placements after world creation. These choices respectively introduce absence semantics, hide current facts, couple structural models to I/O context, or confuse initialization with live state.

**Consequences:** Resolution always reads explicit current facts and never guesses from missing state. Initialization must materialize complete overlays, and world-readiness validation becomes an explicit boundary analogous to cross-package semantic validation.

### 2026-07-12: Store canonical runtime collections as ordered immutable tuples

**Status:** Accepted

**Context:** Canonical snapshots need deterministic serialization and deep practical immutability. A frozen Pydantic model containing ordinary dictionaries still exposes nested mutation, while making dictionaries part of the public contract would also turn lookup representation and map ordering into domain semantics.

**Decision:** Store character, object, and connection state in immutable ordered tuples. Initial world creation preserves authored order, but world-readiness validation and resolution do not depend on record order. Consumers may derive temporary identifier indexes for lookup; those indexes are not canonical state.

**Alternatives considered:** Expose mutable dictionaries, use custom immutable-map dependencies, or require tuple order to control resolution. These choices respectively weaken immutability, add an unnecessary dependency, or create hidden behavioral coupling to serialization order.

**Consequences:** Snapshots are straightforward to compare, serialize, and validate without new dependencies. Resolver code incurs small temporary indexing work, which is negligible for the vertical slice and can be optimized internally later without changing public semantics.

### 2026-07-12: Begin runtime state with exact placement and availability variants

**Status:** Accepted

**Context:** The initial operations need current character locations, object location or possession, connection availability, and simulation time. Adding generic condition mappings or an unplaced-object state without accepted destruction, consumption, hiding, or containment semantics would create ambiguous mechanics.

**Decision:** Define `CharacterState` with character and current-location identifiers; `ObjectState` with object identity and exactly one discriminated location-or-possessor placement; `ConnectionState` with connection identity and an explicit strict boolean availability; and `WorldState` with non-negative integer simulation seconds plus the three ordered state tuples. Do not initially represent unplaced, destroyed, consumed, hidden, quantified, conditioned, or nested objects, or richer character and connection conditions.

**Alternatives considered:** Reuse one model with optional location and possessor fields, allow no placement, add generic status dictionaries, or model anticipated lifecycle states immediately. These choices respectively admit contradictory combinations, make disappearance ambiguous, weaken typed mechanics, or freeze semantics without a supported operation.

**Consequences:** Every initial object always has one resolvable current placement and every connection has explicit availability. Consumption or destruction later requires a deliberate state and transition design rather than silent record removal.

### 2026-07-12: Separate runtime-state structure from world-readiness validation

**Status:** Accepted

**Context:** Runtime-state records can be structurally valid while still duplicating an ID, omitting an authored entity, referencing an unknown definition, or pointing to an invalid location or possessor. Enforcing those relationships inside Pydantic constructors would require package context and repeat the coupling avoided by the package model and semantic-validation split.

**Decision:** Implement strict immutable runtime-state structural models in TASK-012 without package lookup or relational validation. Implement a separate world-readiness validation task that compares one snapshot with `ValidatedGamePackages` and enforces completeness, uniqueness, definition matching, and runtime-reference validity. Outcome and event contracts follow that validated boundary.

**Alternatives considered:** Combine structural models and package-aware validation, put all state and validation into one large task, or defer world-readiness checks to individual operation resolvers. These choices respectively couple constructors to external context, broaden delegation scope, or duplicate incomplete checks across operations.

**Consequences:** TASK-012 remains a small stable public-contract task, and world-readiness failures gain their own deterministic semantic boundary. Structurally constructed snapshots are not proof that a world is ready for resolution.

### 2026-07-12: Require a narrow validated-world-state wrapper at the arbiter boundary

**Status:** Accepted

**Context:** Structural runtime models deliberately allow duplicates, omissions, and unresolved references. Passing a raw snapshot and package pair to every resolver would require repeated defensive checks and would not let type signatures distinguish relationally coherent state from merely well-shaped data.

**Decision:** Relational validation returns an immutable `ValidatedWorldState` pairing one `ValidatedGamePackages` value with one `WorldState`. It guarantees complete unique overlays, matching runtime and authored record identities, and valid current location and character-possessor references. The simulation arbiter later requires this wrapper. Validation failure raises one application-owned error containing deterministic structured issues and returns no partial wrapper. The wrapper does not imply policy implementation availability, supported mechanics, persistence compatibility, or scenario playability.

**Alternatives considered:** Pass raw packages and state to the arbiter, return a boolean, mutate the snapshot during validation, or call the result fully world-ready for every application concern. These choices respectively repeat trust checks, discard diagnostic and type information, hide repairs, or overstate a narrow relational guarantee.

**Consequences:** Downstream kernel code receives one explicit relational trust boundary and validation remains pure. A separate issue model is needed, and later readiness layers must retain names that do not confuse their stronger guarantees with this wrapper.

### 2026-07-12: Give world-state validation its own structured issue vocabulary

**Status:** Accepted

**Context:** Package validation diagnoses authored content, while world-state validation diagnoses a runtime snapshot's relationship to already validated definitions. Reusing one issue type would blur which trust boundary failed. Free-form errors or uncontrolled cascades would also make repair and inspection unreliable.

**Decision:** Define separate strict immutable `WorldStateValidationIssueCode`, `WorldStateValidationIssue`, and `WorldStateValidationError` contracts. The initial codes are exactly `duplicate-state-id`, `missing-state`, `unexpected-state`, and `unknown-runtime-reference`. Each issue carries a deterministic runtime-state path and non-blank human message. Aggregate independent root defects but suppress reference conclusions that depend on selecting one authoritative record from duplicates or otherwise invalid state identity.

**Alternatives considered:** Reuse package issue classes, throw the first error, use messages without codes, or report every mechanically discoverable consequence. These choices respectively conflate boundaries, slow diagnosis, weaken tooling, or produce misleading cascades.

**Consequences:** Callers can distinguish content defects from snapshot defects and present stable multi-issue feedback. The validator needs explicit deterministic ordering and gating rules rather than relying on incidental traversal behavior.

### 2026-07-12: Order world-state issues by namespace, authorship, and runtime occurrence

**Status:** Accepted

**Context:** Multi-issue validation is only reproducible and useful for repair if ordering and dependent-check suppression are explicit. Runtime tuple order, authored definition order, and duplicate ambiguity each carry different diagnostic meaning.

**Decision:** Validate character, object, and connection overlays in that order, then current references for uniquely identified expected records. Within each namespace, report duplicates by first duplicate encounter, missing records in authored definition order, and unexpected records in runtime tuple order. Reference issues follow character then object runtime tuple order. Validate current locations against authored locations and object possessors against authored characters. Skip references from duplicated or unexpected owning records. If a possessor is an authored character whose runtime overlay is missing, report only the missing overlay rather than also calling the possession reference unknown.

**Alternatives considered:** Sort every issue lexically, use set iteration order, validate references from ambiguous duplicate records, or treat missing runtime possessor state as an unknown authored reference. These choices respectively discard meaningful source order, introduce nondeterminism, create cascades, or confuse completeness with reference identity.

**Consequences:** The same invalid snapshot produces the same concise issue sequence, authored omissions are easy to repair in content order, and runtime paths still identify the exact offending occurrence.

### 2026-07-12: Address world-state issues with runtime field paths

**Status:** Accepted

**Context:** Inspection and repair tooling need stable paths into the supplied snapshot. Missing records have no tuple position, while package-definition paths would point outside the artifact being validated.

**Decision:** Use runtime field paths composed of collection names, zero-based tuple indexes, placement nesting, and field names. Duplicate, unexpected, and reference issues point to exact fields such as `characters[2].character_id` or `objects[1].placement.character_id`. Missing-state issues use the collection path, such as `characters`, and identify the absent authored ID in the human message. Expose `validate_world_state(packages: ValidatedGamePackages, state: WorldState) -> ValidatedWorldState` as the public boundary.

**Alternatives considered:** Invent indexes for missing records, address package definitions, use JSON Pointer immediately, or return paths as unstructured prose. These choices respectively misrepresent supplied data, target the wrong artifact, add unused encoding complexity, or weaken tooling.

**Consequences:** Every issue path either locates a supplied field or honestly names the collection where a record is absent. The function signature makes validated definitions an explicit prerequisite and returns the narrow trusted wrapper.

### 2026-07-12: Represent state changes as self-verifying before-and-after deltas

**Status:** Accepted

**Context:** Immutable snapshot replacement needs an exact description of intended changes. New-value-only commands make stale resolution plans and accidental no-ops difficult to detect, while reconstructing prior values later weakens inspection evidence.

**Decision:** Define a closed discriminated union of character-location, object-placement, connection-availability, and simulation-time changes. Every change includes the affected identity where applicable and explicit before and after values. Equal values are structurally invalid, and time must advance from a non-negative integer to a strictly greater integer. The arbiter later verifies before values against its input snapshot before applying the complete change set. State changes describe snapshot deltas and remain distinct from canonical events describing facts that occurred.

**Alternatives considered:** Store only new values, allow generic field paths and values, infer old values during inspection, or use events themselves as mutation commands. These choices respectively weaken stale-plan detection, abandon typed state, lose durable before-state evidence, or conflate fact history with snapshot application.

**Consequences:** Deltas are explicit, inspectable, and safe to apply atomically after verification. Resolvers must supply slightly more data, and later application logic must reject mismatched or conflicting change sets rather than silently overwriting state.

### 2026-07-12: Make outcome status variants structurally distinct

**Status:** Accepted

**Context:** One outcome model with optional effect fields could represent rejected proposals carrying state changes or events, contradicting the accepted guarantee that rejection never enters the simulated world. Valid failures and successes, however, may independently have state changes, events, both, or neither.

**Decision:** Define a closed discriminated union of `RejectedOutcome`, `FailedOutcome`, and `SucceededOutcome`. Every variant contains application-assigned outcome identity, originating proposal identity, and a stable machine-readable reason code. Rejected outcomes omit effect fields entirely. Failed and succeeded outcomes contain immutable ordered state-change and canonical-event tuples, either of which may be empty. Outcomes and state changes remain simulation-step trace evidence; canonical events additionally become durable canonical history.

**Alternatives considered:** Use one status enum with optional effects, require every success to mutate state, require every valid attempt to emit an event, or store outcomes only transiently. These choices respectively admit contradictory records, exclude observation-like success, overstate event requirements, or lose causal inspection evidence.

**Consequences:** Rejected canonical effects are unrepresentable by construction, while valid operation semantics remain flexible. Outcome schemas need separate variants and later semantic validation must ensure nested event causation and change-set consistency.

### 2026-07-12: Timestamp outcomes and events at atomic completion

**Status:** Accepted

**Context:** Duration-bearing actions need a clear time for their resolved facts. Mixing action-start, intermediate, and completion times inside one atomic outcome would complicate state application and overlap with the later scheduler's responsibility for activities made eligible by elapsed time.

**Decision:** Every outcome has non-negative integer `resolved_at_seconds`. Rejection uses the input snapshot time; valid failure or success uses completion time after any action-duration advancement. Every nested canonical event uses the outcome ID as its cause and the same time as `occurred_at_seconds`. A time-change after value equals completion time; without a time change, completion time equals the input snapshot time. The initial kernel represents no intermediate event times inside one outcome. Activities made eligible by elapsed time resolve later as separate outcomes.

**Alternatives considered:** Timestamp all records at action start, allow arbitrary event times inside an outcome, omit outcome time, or resolve scheduled consequences inside the same outcome. These choices respectively misstate completion, weaken atomicity, force time inference, or blur action resolution with scheduler ordering.

**Consequences:** One outcome has one unambiguous temporal point and nested causation is easy to validate and inspect. The arbiter must enforce consistency with its input snapshot and any time-change delta, while the scheduler remains responsible for subsequent eligible work.

### 2026-07-12: Begin canonical events with eight actor-operation facts

**Status:** Accepted

**Context:** The initial seven actor operations need typed factual history for later perception and inspection, and valid failures may themselves be perceptible. Generic event payloads would weaken those downstream boundaries, while requiring an event for every valid outcome would invent facts for operations whose rules may resolve silently.

**Decision:** Define a closed initial union of `ActorObservedEvent`, `ActorMovedEvent`, `ActorSpokeEvent`, `ObjectTakenEvent`, `ObjectUsedEvent`, `ActorHelpedEvent`, `ActorWaitedEvent`, and `ActorActionFailedEvent`. Every event has application-assigned event ID, causing outcome ID, non-negative occurrence seconds, and fixed event discriminator. Payloads identify the relevant actor, connection, locations, character, object, previous placement, utterance, duration, operation, or accepted typed target. Events contain no observer visibility or narration. Failed and succeeded outcomes may contain an empty event tuple.

**Alternatives considered:** Use one generic operation event, infer events from state changes, require exactly one event per attempt, or postpone all event types until perception. These choices respectively weaken schemas, miss non-state facts such as speech, overconstrain rules, or leave perception without a canonical factual input.

**Consequences:** Initial action facts have precise durable contracts and later perception can distinguish their payloads. Some data intentionally overlaps state changes for audit clarity, and later world operations or mechanics require explicit new event variants rather than arbitrary payload extension.
