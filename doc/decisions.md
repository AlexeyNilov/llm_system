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

### 2026-07-11: Configure an experimenter for evidence tasks

**Status:** Accepted

**Context:** Ready preflight tasks need reproducible environment evidence but do not require the planning agent's broader context. The user wants these bounded tasks to use GPT-5.6 Terra with high reasoning while retaining permission to write an authorized report and task handoff.

**Decision:** Add the project custom agent `experimenter` under `.codex/agents/`. Configure it with `gpt-5.6-terra`, high reasoning, and workspace-write sandboxing. Restrict its instructions to Ready evidence or experiment task briefs and their explicitly authorized files. Task briefs remain the source of task-specific context.

**Alternatives considered:** Use the planning agent, rely on inherited model selection, or embed the entire task inside the custom-agent instructions. The planning agent is unnecessarily broad; inheritance does not guarantee the requested model; embedding tasks would mix stable role configuration with changing work.

**Consequences:** A fresh Codex task can select a predictable lower-cost experiment role without receiving this planning transcript. The agent still inherits repository safety boundaries and must stop on design gaps or unauthorized mutations.

### 2026-07-13: Configure an implementer for Ready code tasks

**Status:** Accepted

**Context:** Multiple Ready implementation tasks have used the same stable execution constraints: TDD, task-authorized writes, bounded context, explicit verification, design-gap escalation, and a Review-or-Blocked handoff. Leaving model, reasoning, sandbox, and these durable boundaries to inherited defaults makes otherwise comparable executions less predictable.

**Decision:** Add the project custom agent `implementer` under `.codex/agents/`. Configure it with `gpt-5.6`, high reasoning, and workspace-write sandboxing. Restrict it to one Ready implementation or scenario-authoring task brief at a time. The task brief remains the source of task-specific context, accepted contracts, scope, verification, and artifact permissions; the role guide remains the detailed execution procedure.

**Alternatives considered:** Continue using `Default`, use the faster experimenter profile, or duplicate implementation procedure and task context in the custom-agent instructions. Default does not provide stable execution settings; the experimenter profile optimizes evidence gathering rather than code delivery; duplicated procedure and context would drift from the role guide and task brief.

**Consequences:** New Ready implementation and scenario-authoring briefs select `implementer` unless they name a justified alternative. Historical task briefs remain unchanged. The parent session's live permission settings can still override the profile sandbox, so the delegated agent must report approval or sandbox limitations rather than treating the configured setting as guaranteed.

### 2026-07-13: Configure a reviewer for independent evidence tasks

**Status:** Accepted

**Context:** The M3.5 kernel review demonstrated a repeatable independent-review responsibility: reconstruct behavior from repository evidence, compare it with accepted contracts, classify findings by impact, assess missing and low-value tests, and return recommendations without implementing or accepting them. Reusing implementation context or inherited agent defaults weakens independence and makes the reviewer boundary less predictable.

**Decision:** Add the project custom agent `reviewer` under `.codex/agents/`. Configure it with `gpt-5.6-luna`, high reasoning, and workspace-write sandboxing. Restrict it to one Ready independent review, audit, or bounded evidence task at a time, using `doc/agent_roles/reviewer.md` as its one role guide. Workspace write is permitted only because review tasks may authorize a durable report and task handoff; the reviewer remains behaviorally read-only and may not implement fixes or change application behavior.

Independent review is selective rather than mandatory after every implementation. When required by risk, a milestone, the roadmap, or the user, prepare a separate Ready review task that references the implementation task, diff, accepted contracts, verification evidence, and execution context-used record. Do not reuse the implementation task as the review brief because its one role guide belongs to the implementation responsibility. The integrator remains responsible for finding disposition, verification, acceptance, and Done status.

**Alternatives considered:** Continue using `Default`, make every implementation task undergo a custom-agent review, use a literal read-only sandbox, or let the reviewer share the implementation task and context. Default does not provide stable independent-review behavior; mandatory review adds disproportionate process to small bounded changes; a read-only sandbox prevents task-authorized report artifacts; shared role context violates the one-guide boundary and increases anchoring.

**Consequences:** New Ready independent-review briefs select `reviewer` unless they name a justified alternative. Historical review tasks remain unchanged. Parent verification must confirm that reviewer changes are limited to the authorized report and task fields. Live parent permission settings can still override the profile sandbox, so filesystem scope remains an integration check rather than an assumed guarantee.

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

### 2026-07-12: Validate context-free outcome consistency structurally

**Status:** Accepted

**Context:** Some invalid outcome combinations can be detected from the record alone, while others require the input world snapshot, proposal, loaded rules, and authority context. Putting all checks in either Pydantic models or the arbiter would respectively couple data contracts to world lookup or allow malformed nested records to circulate.

**Decision:** Outcome construction enforces that nested events use the containing outcome ID and completion time, event IDs are unique within the outcome, each character location, object placement, or connection availability changes at most once, and at most one simulation-time change exists. Sequential deltas to one field must be collapsed into one before-and-after change. The later arbiter verifies before values against state, time agreement with input, actionability, source authority, and semantic agreement among proposal, changes, and events.

**Alternatives considered:** Perform every check in Pydantic validators, defer every check to the arbiter, allow sequential changes inside one atomic outcome, or validate only during persistence. These choices respectively require external context in constructors, admit internally contradictory records, obscure final deltas, or discover defects after the trust boundary.

**Consequences:** Outcome values are internally coherent before reaching the arbiter without pretending to be valid for a particular world. The outcome models need small cross-record validators, and arbiter tests retain responsibility for all state-dependent guarantees.

### 2026-07-12: Define state changes and events before outcome aggregates

**Status:** Accepted

**Context:** Outcome variants depend directly on completed state-change and canonical-event unions and then add cross-record invariants over them. Implementing all three layers in one delegated task would require an agent to stabilize leaf payloads and aggregate semantics simultaneously.

**Decision:** Split the roadmap into TASK-014 for state-change and canonical-event contracts, followed by TASK-015 for rejected, failed, and succeeded outcome contracts plus context-free aggregate consistency. The simulation arbiter follows both.

**Alternatives considered:** Keep one large contract task, define outcomes before concrete effect unions, or let the arbiter use generic effect payloads temporarily. These choices respectively broaden context, invert type dependencies, or introduce a weak boundary that would immediately be replaced.

**Consequences:** Each task has one coherent type layer and focused tests. The project gains an additional versioned milestone, but outcome work begins with stable imported unions and can concentrate on aggregate invariants.

### 2026-07-12: Keep outcome reason codes formatted but resolver-extensible

**Status:** Accepted

**Context:** Outcomes need stable machine-readable explanations, but the complete reason vocabulary depends on supported operations and later versioned mechanics. A central enum would make the core outcome contract change for every legitimate resolver reason, while arbitrary strings would weaken inspection and tests.

**Decision:** Define `OutcomeReasonCode` as a strict non-empty lowercase kebab-case semantic value rather than a closed enum. Deterministic kernel and resolver implementations own and document the meanings they emit. LLMs and package content cannot establish canonical reason semantics merely by supplying a syntactically valid code.

**Alternatives considered:** Use one central enum, accept any string, use generated prose as the reason, or let rule packages declare executable reason meanings. These choices respectively overcouple mechanics, weaken contracts, lose stable machine meaning, or cross the code-data authority boundary.

**Consequences:** Outcome schemas remain stable as resolver catalogs grow, while codes stay predictable for traces and presentation mapping. Each resolver task must specify and test its emitted codes instead of relying on an ungoverned global list.

### 2026-07-12: Require explicit effect tuples on valid-attempt outcomes

**Status:** Accepted

**Context:** Failed and succeeded outcomes may legitimately have no state changes or events. If those fields default silently, however, omitted resolver output becomes indistinguishable from an intentional empty effect set at the trace and validation boundary.

**Decision:** Require both immutable ordered `state_changes` and `events` fields on every failed or succeeded outcome, even when either value is an empty tuple. Neither field has a default. Rejected outcomes continue to omit both fields entirely and reject attempts to add them.

**Alternatives considered:** Default both fields to empty tuples, make them optional, or add empty fields to rejected outcomes. These choices respectively hide omission, introduce null semantics, or weaken the structural rejection guarantee.

**Consequences:** Resolver code must be explicit about no-effect results, serialized traces distinguish complete data from malformed omission, and outcome construction fails early when aggregate evidence is incomplete.

### 2026-07-12: Separate arbiter commitment from operation resolution

**Status:** Accepted

**Context:** The roadmap previously grouped the simulation arbiter with all seven initial operations. Move and Wait have partial mechanical grounding, but Observe depends on perception, Speak on hearing, Take on accessibility and possession, and Use and Help on rule-pack mechanics not yet defined. Most durations also remain unspecified. Implementing the group would force temporary defaults or invented rules.

**Decision:** Split deterministic arbiter work into an outcome-commitment core, submission authorization and operation dispatch, and individual operation resolvers. The commitment core validates and atomically applies already resolved typed outcomes against validated state without knowing operation semantics. Implement each resolver only after its actionability, duration, failure, state-change, and event rules are accepted. Do not approximate missing mechanics with generic dictionaries or temporary hard-coded defaults.

**Alternatives considered:** Implement all proposal variants immediately, let the coding agent choose plausible mechanics, add generic rule mappings, or postpone every arbiter responsibility. These choices respectively freeze guesses, violate the architecture role boundary, weaken typed mechanics, or delay independently useful atomic state application.

**Consequences:** The kernel can establish safe deterministic commitment now while operation behavior remains honest and incremental. More tasks are required, and a resolved outcome is not proof that its originating proposal was authorized or semantically resolved correctly until later arbiter layers are present.

### 2026-07-12: Commit outcomes into one validated-world result

**Status:** Accepted

**Context:** The commitment core needs one explicit atomic boundary without claiming proposal authorization or operation resolution. Returning state and events as unrelated values would duplicate information already owned by the outcome and permit callers to mix mismatched records.

**Decision:** Expose `commit_outcome(world: ValidatedWorldState, outcome: Outcome) -> OutcomeCommitResult`. The strict immutable result contains exactly the committed outcome and resulting validated world. Rejection is retained as trace evidence and returns the exact same world object; its type has no effects. Failed or succeeded outcomes are fully validated against the input snapshot, then their complete delta set is applied to one replacement snapshot and revalidated against the same packages. Events remain inside the outcome. Proposal/submission agreement, authority, actionability, and operation-specific meaning remain later arbiter responsibilities.

**Alternatives considered:** Return a tuple of loose values, duplicate events on the result, mutate the supplied world, discard rejected outcomes, or combine commitment with authorization and resolution. These choices respectively weaken pairing, create two event sources, violate snapshot semantics, lose trace evidence, or recreate the oversized arbiter task.

**Consequences:** Callers receive one coherent trace-and-state result and canonical event evidence has one owner. The core needs a separate structured failure boundary for state-dependent mismatches, and later orchestration must ensure only deterministic resolvers supply outcomes for commitment.

### 2026-07-12: Reject invalid commitment with structured atomic issues

**Status:** Accepted

**Context:** Structurally valid outcomes can still target absent runtime records, carry stale before values, reference unknown after-state definitions, or disagree with world time. Raising the first ad hoc exception would weaken inspection, while partially applying valid deltas would violate atomicity.

**Decision:** Define separate strict immutable `OutcomeCommitIssueCode`, `OutcomeCommitIssue`, and `OutcomeCommitError` contracts. Initial codes are `resolution-time-mismatch`, `unknown-change-target`, `before-value-mismatch`, and `unknown-after-reference`. Issues point into the supplied outcome and carry non-blank messages. Aggregate independent issues deterministically and apply no state or event effects when any exist. Revalidate an accepted replacement snapshot against the same packages as an invariant check; if that unexpectedly fails after all commitment checks, treat it as a kernel defect rather than an ordinary caller correction.

**Alternatives considered:** Raise the first mismatch, reuse world-state validation issues, apply valid changes while rejecting others, or convert any final validation failure to one generic commit error. These choices respectively hide evidence, conflate trust boundaries, violate atomicity, or conceal implementation defects.

**Consequences:** Invalid outcomes produce inspectable deterministic evidence and leave their input world untouched. The core must define exact ordering and gating rules and maintain exhaustive handling for every closed state-change variant.

### 2026-07-12: Validate commitment in outcome order with target gating

**Status:** Accepted

**Context:** Aggregated commit failures need reproducible order and must avoid claiming stale or invalid field values for a change whose target does not exist. Time consistency spans both the outcome aggregate and an optional time-change delta.

**Decision:** Report an outcome-level time mismatch first when rejection or a valid attempt has no time change. Then traverse state changes in tuple order. For each non-time change, validate target existence first; an unknown target produces only `unknown-change-target` and suppresses before and after checks. For known targets, report before mismatch before independently invalid after reference. For a time change, report current-world mismatch on `from_seconds` and outcome-completion mismatch on `to_seconds` at that change's tuple position. Rejection or a valid attempt without a time change requires completion time equal to current world time.

**Alternatives considered:** Sort issues lexically, report dependent mismatches for absent targets, validate all after references before before values, or treat every time discrepancy as one outcome-level issue. These choices respectively discard causal order, create cascades, obscure stale input, or lose precise field evidence.

**Consequences:** Issue order follows the submitted outcome and points to the most actionable root fields. Validation helpers must retain tuple indexes and gate each change independently before any application occurs.

### 2026-07-12: Preserve world identity when commitment changes no state

**Status:** Accepted

**Context:** Valid observation, speech, or other attempts may emit canonical events without changing the current snapshot. Allocating an identical replacement world would create meaningless identity churn, while record reordering during real changes would weaken deterministic comparison and references.

**Decision:** A successfully committed outcome with an empty state-change tuple returns the exact input `ValidatedWorldState` object, whether rejected, failed, or succeeded. The outcome itself preserves attempt semantics and may carry events. When changes exist, replace affected records at their existing tuple positions, preserve unaffected record identities and collection order, create a new `WorldState`, and return a new `ValidatedWorldState` paired with the exact same packages object.

**Alternatives considered:** Always allocate a new snapshot, mutate existing tuples, sort records after application, or treat event-only outcomes as state changes. These choices respectively add meaningless churn, violate immutability, disturb canonical order, or conflate history with current state.

**Consequences:** Object identity honestly signals whether snapshot data changed, event-only commitment remains possible, and tuple ordering stays stable. Tests must verify identity preservation as well as value equality.

### 2026-07-13: Authorize actor submissions before operation dispatch

**Status:** Accepted

**Context:** Trusted submission envelopes identify their source and intended actor, but source-specific authority has not yet been checked. Operation dispatch cannot be useful until at least one resolver exists, while actor and policy binding is already fully defined by validated packages and submission provenance.

**Decision:** Separate actor-action authorization from dispatch. Expose `authorize_actor_action(world, submission) -> AuthorizedActorAction`, preserving the exact inputs. The intended actor must be authored. Player-interpreter sources may act only for the one player character. NPC-policy sources require source NPC equal to intended actor, that actor to be an NPC, and source policy equal to the NPC's configured policy. Interpreter ID remains trusted application provenance without a new allowlist. Do not inspect proposal targets or actionability, dispatch operations, invoke resolvers, or generate outcomes.

**Alternatives considered:** Combine authorization with dispatch, trust source metadata without actor binding, introduce an interpreter registry now, or validate proposal targets during authorization. These choices respectively depend on nonexistent resolvers, permit impersonation, add configuration without a requirement, or mix authority with operation semantics.

**Consequences:** Later dispatch can require a type-proven authorized submission and operation resolvers can focus on world mechanics. Authorization gains its own structured failure boundary, while application orchestration remains responsible for constructing trusted envelopes.

### 2026-07-13: Gate authorization errors from actor identity to policy

**Status:** Accepted

**Context:** Authorization failures form a dependency chain. Reporting policy mismatch when the source names a different actor, or actor type when the intended actor does not exist, would produce misleading cascades and obscure the primary impersonation or identity defect.

**Decision:** Use separate strict immutable authorization issue code, issue, and error contracts with initial codes `unknown-actor`, `source-actor-mismatch`, `actor-type-mismatch`, and `policy-mismatch`. Resolve intended actor first. Unknown actor suppresses all source checks. Player source against a known non-player reports actor type. NPC source identity mismatch reports only source-actor mismatch; a matching source against a non-NPC reports only actor type; only a matching authored NPC reaches configured-policy comparison. Paths point into the supplied submission.

**Alternatives considered:** Report every discoverable mismatch, use one unauthorized code, throw ad hoc exceptions, or compare policy before actor identity. These choices respectively create cascades, lose diagnostic meaning, weaken tooling, or validate against the wrong principal.

**Consequences:** Every failure identifies the earliest authoritative broken link and current rules yield one root issue per submission. The error retains the project's immutable non-empty issue-tuple pattern for consistent inspection and future independent checks.

### 2026-07-13: Implement Wait as the first deterministic operation resolver

**Status:** Accepted

**Context:** Dispatch needs at least one real resolver, but most actor operations still depend on unaccepted perception, hearing, accessibility, possession, or package mechanics. Wait already has a strict positive duration contract and an accepted requirement to advance time by exactly that duration.

**Decision:** Implement `resolve_wait(action, *, outcome_id, event_id) -> SucceededOutcome` first. It accepts an authorized action, uses caller-injected identities, advances from current simulation time by the proposal duration, emits reason `wait-completed`, one exact time delta, and one actor-waited event at completion. It does not commit, schedule, invoke NPCs, or present results. Receiving a non-Wait proposal is a dispatcher/programmer `TypeError`, not a canonical rejection.

**Alternatives considered:** Begin with a mechanically underspecified operation, implement all resolvers together, generate IDs inside the resolver, return rejection for incorrect dispatch, or process scheduled consequences immediately. These choices respectively invent rules, recreate oversized scope, hide nondeterminism, turn a code defect into fiction, or mix resolution with scheduling.

**Consequences:** The project gains one honest end-to-end authorization-to-outcome path and a concrete resolver contract for later dispatch. Wait always succeeds at this layer; scheduler behavior after its time advancement remains a separate milestone.

### 2026-07-13: Resolve basic movement before introducing generic dispatch

**Status:** Accepted

**Context:** Wait provides one real operation branch, so a generic dispatcher could now be written, but routing a single operation would add an abstraction without testing meaningful selection. Move is the next operation whose current contracts fully determine actionability and effects: an authored directed connection supplies endpoints and positive base duration, while canonical state supplies actor location and connection availability. The schemas do not yet represent traversal requirements or modifiers.

**Decision:** Implement `resolve_move(action, *, outcome_id, event_id) -> RejectedOutcome | SucceededOutcome` before generic dispatch. Require both caller-supplied identities even though rejection does not consume the event identity. Resolve actionability in order: unknown authored connection, actor not at the connection source, then unavailable connection. These cases produce effect-free rejection reasons `unknown-connection`, `actor-not-at-connection-source`, and `connection-unavailable`. Valid movement deterministically uses the exact authored base traversal duration, emits `move-completed`, changes the actor from source to destination, advances simulation time, and records one actor-moved event at completion. A non-Move proposal is a programmer `TypeError`; basic Move has no failed-attempt branch.

**Alternatives considered:** Add generic dispatch with only Wait, let Move target a destination instead of its authored connection, generate identities inside the resolver, allocate an event identity only after resolution, treat non-actionable movement as failed, or introduce skill, terrain, encumbrance, interruption, and requirement rules now. These choices respectively create an uninformative routing layer, lose route identity, hide nondeterminism, complicate the uniform resolver call boundary, invent an attempted action where none began, or exceed the data and mechanics currently accepted.

**Consequences:** Wait and Move will provide two distinct resolver branches against which dispatch can be designed and tested. Initial movement remains deliberately simple and inspectable; richer traversal requires explicit package/runtime contracts and accepted mechanics later. Rejected calls may reserve an unused event UUID, which is an acceptable cost for one uniform caller-injected identity convention.

### 2026-07-13: Introduce partial type-based actor-action dispatch

**Status:** Accepted

**Context:** Wait and Move now provide two accepted operation resolvers, making routing behavior meaningful to test. The actor proposal union also contains five operations whose actionability and effects remain deliberately underspecified. Treating absent resolvers as in-world rejection would falsely claim that the simulation evaluated those attempts, while a configurable registry or ID-provider abstraction would solve needs not yet demonstrated by concrete mechanics.

**Decision:** Add `dispatch_actor_action(action, *, outcome_id, event_id) -> Outcome` as a pure post-authorization routing boundary. Select by concrete proposal type, route Move and Wait to their existing resolvers with the exact authorized action and caller UUIDs, and return the resolver's exact outcome without reconstruction or exception translation. For Observe, Speak, Take, Use, and Help, raise public `OperationResolverUnavailableError`, a `RuntimeError` carrying the typed operation and a stable non-blank message. Missing implementation is an application capability defect, not a canonical outcome. Keep the current two-ID call convention until a concrete resolver proves that a different identity interface is necessary.

**Alternatives considered:** Wait until all seven resolvers exist, return rejected or failed outcomes for missing resolvers, dispatch by operation strings or package configuration, introduce a resolver registry or protocol, inject an ID provider, or wrap resolver exceptions. These choices respectively postpone a now-testable boundary, confuse missing software with simulated reality, weaken type-directed routing, create premature infrastructure, generalize without evidence, or obscure the original deterministic failure.

**Consequences:** Application code gains one honest entry point for currently executable authorized actions and one inspectable failure for structurally valid but unavailable operations. The dispatcher remains intentionally partial and must gain explicit branches as resolver tasks are accepted. Future multi-event identity needs may require revisiting its arguments, but the current API stays aligned with both implemented resolvers.

### 2026-07-13: Begin perception with typed deterministic observation values

**Status:** Accepted

**Context:** Canonical state and events now exist, but actors and narrators still lack a typed representation of limited information. A generic observation payload could leak hidden fields and weaken exhaustive context assembly. Conversely, assigning durable observation UUIDs or numeric confidence and salience scores now would force identity and scoring machinery into a pure projection before recording, uncertainty, or salience rules exist.

**Decision:** Define a closed initial observation union with location, connection, character, object, and canonical-event variants. Every observation carries observer identity, observation time, and fixed provenance: current state for state-derived facts or the exact typed canonical event for event-derived facts. Payloads contain only stable IDs and the mutable fact actually perceived: connection availability or object placement where applicable. Group them in a strict immutable `PerceptionSnapshot` whose observer and time agree with every item; allow empty snapshots, preserve order, and reject events from the future. Do not assign observation UUIDs or confidence and salience scores yet. Keep authored labels and other definitions outside observations; a later restricted context-enrichment boundary may resolve only IDs already present in the snapshot.

**Alternatives considered:** Use arbitrary payload dictionaries, copy full package or world records into observations, give the narrator direct world access, assign UUIDs during filtering, add placeholder numeric scores, require every snapshot to be non-empty, or infer that all objects held by co-located characters are visible. These choices respectively weaken schemas, leak unavailable facts, bypass perception, introduce an ID source prematurely, invent score meanings, exclude legitimate sensory absence, or confuse possession with visibility.

**Consequences:** Perception becomes an explicit ID-linked information boundary that is deterministic, inspectable, and safe to test before filtering rules exist. The later engine owns world-reference resolution, visibility, ordering, and deduplication. Durable observation recording and scored uncertainty remain separate later work, and possessed objects belonging to another actor stay hidden unless explicit mechanics or perceived events expose them.

### 2026-07-13: Project current state before filtering event feedback

**Status:** Accepted

**Context:** Current-state visibility is already grounded by validated graph topology, character locations, object placements, and connection availability. Canonical-event visibility is a different temporal problem: movement, speech, and interaction events may require pre-outcome locations, post-outcome locations, hearing, or event-specific rules not represented by one general co-location test. Combining both now would conceal unresolved feedback semantics inside the first engine function.

**Decision:** Add pure `project_current_perception(world, observer_id) -> PerceptionSnapshot` for current-state observations only. A missing character observer raises `PerceptionObserverNotFoundError`; object IDs are equally absent from the observer namespace. Use canonical simulation time. Emit one current location, all authored outgoing connections including unavailable ones, co-located other characters, then objects directly at the location or possessed by the observer. Group in that order and preserve authored connection or entity order within groups, independent of runtime tuple order. Do not expose another character's possessions or produce event observations.

**Alternatives considered:** Combine state and event filtering, treat an unavailable connection as invisible, include incoming-only connections, include the observer as a perceived character, expose every possession of a co-located character, order from runtime overlays, return an empty snapshot for an unknown observer, or generate descriptions directly. These choices respectively freeze unresolved time semantics, confuse traversability with visibility, expose non-actionable topology as an exit, duplicate self context, leak inventory, make context order incidental, hide caller defects, or collapse projection into presentation.

**Consequences:** The project gains its first real actor-specific view over canonical truth and can test information exclusion before adding an LLM. Event feedback remains a separate explicit design task. The initial engine is intentionally coarse: it has no concealment, attention, sensory traits, environmental facts, or within-location geometry beyond the conservative possession boundary.

### 2026-07-13: Begin Observe as a focused current-perception action

**Status:** Accepted

**Context:** The current-state perception projection can establish whether a typed target is presently available to an actor, and the event contracts can record that an actor observed it. The model cannot yet expose feature details such as structural damage, environmental clues, or skill-mediated findings. Pretending otherwise would either leak canonical truth or invent inspection mechanics. Waiting for the complete richer model would also leave the accepted proposal and event path untested.

**Decision:** Implement a deliberately thin `resolve_observe(action, *, outcome_id, event_id) -> RejectedOutcome | SucceededOutcome`. Treat surroundings as perceptible and require every specific typed target to match the corresponding observation in `project_current_perception` for the authorized actor. Reject every unknown, remote, incoming-only, self-character, hidden, or wrong-namespace target uniformly as `target-not-perceptible`, without revealing whether it exists canonically. Successful observation uses `observation-completed`, consumes no simulation time, changes no state, and records exactly one actor-observed event at current canonical time with the proposal's exact target. Observe v0 has no failed branch. Route Observe through the actor-action dispatcher while the remaining unavailable operations continue raising the capability error.

**Alternatives considered:** Let Observe access canonical definitions directly, return different reasons for unknown and hidden targets, duplicate visibility checks inside the resolver, advance time by an invented default, treat inspection as a probabilistic failure, emit a new observation directly from the outcome, or postpone all Observe plumbing until rich package facts exist. These choices respectively bypass perception, leak truth, create divergent information boundaries, invent unsupported mechanics, add ungrounded randomness, confuse action evidence with actor-specific feedback, or delay a now-testable resolver boundary.

**Consequences:** Observe becomes executable and auditable without claiming to deliver rich inspection gameplay. Current perception remains the sole target-availability authority, and event feedback or restricted enrichment must later determine what additional information reaches an actor or narrator. Rule-defined searches, Fieldcraft inspection, and time-consuming observation remain separate future mechanics rather than silent extensions of v0.

### 2026-07-13: Begin event feedback with stateless self-action projection

**Status:** Accepted

**Context:** Canonical events and actor-specific event observations exist, but the perception engine does not yet connect them. General witness visibility requires event-specific temporal semantics such as pre-action and post-action locations, hearing, and target awareness. An actor's own action provides a smaller grounded first boundary and lets consequences re-enter the actor loop through perception rather than direct outcome access.

**Decision:** Add pure `project_self_event_feedback(world, observer_id, events) -> tuple[EventObserved, ...]`. Validate the observer first using the existing character-state namespace and error. Then validate the entire caller-supplied candidate batch against current canonical time, raising typed `FutureEventFeedbackError` for the first future event even if another actor owns it. Treat `speaker_id` as the owner of a spoke event and `actor_id` as owner of every other initial event variant. Preserve matching input order and duplicates, wrap each match at current canonical time while retaining the exact event object, and return an empty tuple when nothing matches. The caller owns event-window selection and delivery tracking.

**Alternatives considered:** Add all witness rules at once, merge event processing into current-state projection, return an event-only perception snapshot, give actors direct outcomes, infer ownership from recipient or target roles, silently ignore future events, query all event history internally, deduplicate inputs, or persist delivery state in the perception engine. These choices respectively freeze unresolved temporal rules, mix distinct information sources, misrepresent partial perception as complete, bypass filtering, confuse participation with action ownership, hide coordinator defects, couple a pure projection to storage, alter caller evidence, or mix projection with lifecycle state.

**Consequences:** Every initial canonical event has an exhaustive self-feedback ownership rule, and the actor loop gains its first event-to-observation path. The result remains only an event-observation fragment; later explicit composition must combine it with current state. Witness visibility, audibility, event-window persistence, enrichment, recording, and presentation remain separate tasks.

### 2026-07-13: Represent scheduled work as one-shot typed eligibility records

**Status:** Accepted

**Context:** Time-bearing actions now advance canonical time, but the kernel has no typed representation of work that may become eligible as a result. Environmental mechanics, NPC decisions, and System-director hooks lead to different downstream behavior; treating them as one executable operation or arbitrary payload would blur their authority and validation boundaries. Ordering also must not depend on tuple storage or random UUID comparison.

**Decision:** Define a closed runtime scheduled-activity union with environmental, NPC, and System-director variants. Every one-shot occurrence has an application-assigned activity UUID, non-negative eligibility time, and caller-assigned non-negative insertion sequence. Environmental activity references an authored schedule, NPC activity identifies only the NPC, and System-director activity references its hook. Derive phase priority from the variant as environmental, NPC, then System director; do not store an editable priority. Wrap activities in an immutable queue that preserves supplied storage order while rejecting duplicate activity IDs and insertion sequences. The later scheduler orders by eligibility time, derived phase, and insertion sequence.

**Alternatives considered:** Use one generic payload dictionary, embed callbacks or action proposals, store configurable phase priority, use UUID or tuple order as a tie-breaker, duplicate NPC policy identity, put recurrence rules on runtime occurrences, require queues to be pre-sorted, or combine records with eligibility selection and execution. These choices respectively weaken contracts, confuse eligibility with execution, permit contradictory priority, introduce incidental ordering, create stale authority, mix definition with occurrence, make storage shape authoritative, or broaden the first boundary prematurely.

**Consequences:** Scheduled work can be persisted, inspected, and deterministically ordered without pretending that all activity types execute the same way. Package schemas and relational validation must later define environmental schedules and director hooks. Eligibility selection, queue removal, execution, recurrence creation, cancellation, rescheduling, tracing, and persistence remain separate tasks.

### 2026-07-13: Partition due scheduled activities without executing them

**Status:** Accepted

**Context:** One-shot activity and queue contracts now exist, but callers need a deterministic boundary that identifies work made eligible by committed canonical time. Returning only an ordered list would leave repeated selection and pending-queue reconstruction ambiguous, while executing activities during selection would mix temporal ordering with environmental mechanics, NPC policy invocation, and System-director orchestration.

**Decision:** Add pure `select_eligible_activities(world, queue) -> ScheduledActivitySelection`. At canonical world time, partition overdue and exactly due activities from strictly future activities. Sort eligible work by eligibility time, derived phase rank, and insertion sequence; preserve pending storage order. Return a strict immutable result with selection time, eligible tuple, and remaining queue. The result validates due-versus-future partitioning, eligible ordering, and metadata uniqueness across both groups. Retain exact activity objects and reuse the exact input queue when no activity is eligible.

**Alternatives considered:** Return eligible work only, mutate the queue, require callers to pre-sort storage, use UUID or tuple order as a tie-breaker, discard overdue work, select only exact-time work, store phase priority, execute while selecting, or integrate persistence and claiming immediately. These choices respectively obscure consumption, weaken purity, make storage authoritative, introduce incidental ordering, lose work, miss time jumps, permit contradictory priority, mix responsibilities, or force transaction semantics before the persistence boundary exists.

**Consequences:** The kernel can deterministically explain which one-shot activities are ready and what remains pending without running them. A later coordinator must transactionally persist or otherwise own the returned partition before serial execution and must define how newly scheduled activities, retries, failures, and cascading eligibility are processed.

### 2026-07-13: Begin recorded randomness with one validated integer primitive

**Status:** Accepted

**Context:** The arbiter needs an injectable and auditable randomness boundary before any rule-specific check exists. A generic arbitrary-parameter API would weaken validation, while separate dice, percentage, choice, and weighted-choice methods would prematurely place game mechanics in the random source. Generator-state persistence and trace attachment also depend on later persistence and simulation-step boundaries.

**Decision:** Begin with an application-identified immutable integer draw request containing an extensible kebab-case purpose and two strict inclusive bounds with at least two possible results. Inject a narrow integer random source that receives only those bounds. A pure arbiter-facing wrapper obtains one result, rejects booleans, non-integers, and out-of-range values with `RandomSourceContractError`, and returns an immutable record preserving the exact request metadata and result. Source-raised exceptions propagate unchanged. The wrapper does not clamp, coerce, retry, or generate identity.

**Alternatives considered:** Expose generic parameter dictionaries, define one random operation per game mechanic, use a closed purpose enum, pass identity and purpose into the entropy source, permit equal bounds, clamp invalid values, retry failures, wrap every source exception, generate draw identities internally, or immediately couple draws to outcomes, events, persistence, and traces. These choices respectively weaken schemas, couple the kernel to rule packs, block extensible mechanics, let metadata influence entropy, record deterministic non-choices as random, conceal source defects, alter canonical sequences, conflate operational and contract failures, hide nondeterminism, or force unresolved consumer contracts.

**Consequences:** Rule mechanics can derive dice, checks, and selections deterministically from one testable primitive, while every successful draw has a self-contained audit value. TASK-027 establishes only the contract and injected boundary; a concrete seeded generator, generator-state persistence, canonical history attachment, and rule-specific checks remain separate later work.

### 2026-07-13: Defer a concrete random generator until its first consumer

**Status:** Accepted

**Context:** TASK-027 provides the injected and recorded randomness boundary, but M3 has no rule-governed random check and M4 persistence has not been designed. Choosing, implementing, versioning, and serializing a project-owned generator now would add compatibility machinery without exercising it in the initial deterministic kernel.

**Decision:** Do not implement a concrete seeded random source during M3. Kernel and resolver tests use injected scripted sources. Reconsider the smallest production implementation when the first accepted random-check mechanic and persistence repository both exist; begin with Python's standard `random.Random` and its documented state facilities unless concrete replay or compatibility evidence justifies a project-owned algorithm.

**Alternatives considered:** Implement SplitMix64 or another owned algorithm immediately, persist Python generator state before repositories exist, or remove seeded reproducibility requirements. These choices respectively add speculative algorithm ownership, force a storage contract without its transaction boundary, or abandon required restart reproducibility.

**Consequences:** The vertical slice avoids unused infrastructure while retaining the authority, testing, audit, and future persistence requirements. `RANDOM-003` remains accepted but is fulfilled later with the first real consumer rather than by an isolated M3 component.

### 2026-07-13: Resolve Speak v0 as co-located zero-time speech

**Status:** Accepted

**Context:** The initial scenario requires characters to address one another, and the action and canonical-event contracts already represent a recipient and exact utterance. The kernel has character locations but no hearing range, barriers, speech duration, language comprehension, conversation memory, or response mechanics. Reusing visual perception as audibility would collapse distinct information channels.

**Decision:** Add pure `resolve_speak(action, *, outcome_id, event_id)`. Treat only another character at the speaker's exact canonical location as audible. Unknown, remote, self, and wrong-namespace recipients reject uniformly as `recipient-not-audible`. Audible speech succeeds as `speech-completed` at current canonical time, changes no state, advances no time, and records one `ActorSpokeEvent` preserving the exact speaker, recipient, utterance, and caller identities. There is no failed branch or automatic response.

**Alternatives considered:** Reuse current visual perception, permit remote or self speech, expose different rejection reasons, infer duration from text length, invent a fixed duration, treat recipient refusal as speech failure, update beliefs or memory directly, generate a response during resolution, or bundle recipient perception into the resolver. These choices respectively confuse senses, exceed current spatial mechanics, leak canonical existence, make wording an implicit scheduling rule, add an ungrounded constant, confuse delivery with reaction, bypass the actor loop, mix resolution with policy, or collapse truth into perception.

**Consequences:** The kernel can record honest addressed speech without claiming comprehension or conversation behavior. Conversation alone does not advance scheduled time in v0. Addressed-speech feedback for the recipient is the immediate follow-up task and remains separate from the canonical resolver and from broader witness audibility.

### 2026-07-13: Project addressed speech from committed recipient identity

**Status:** Accepted

**Context:** Speak v0 validates co-located audibility before creating an `ActorSpokeEvent`, but self-action feedback intentionally treats only the speaker as owner. A recipient needs the exact utterance as an observation for later sensemaking. Rechecking present locations would incorrectly decide historical delivery using state after either character may have moved, while general overhearing still lacks event-time spatial semantics.

**Decision:** Add pure `project_addressed_speech_feedback(world, observer_id, events) -> tuple[EventObserved, ...]`. Validate the observer first and the whole candidate batch for future events before filtering, reusing existing errors and current canonical observation time. Emit only exact `ActorSpokeEvent` objects whose `recipient_id` equals the observer, preserving input order and duplicates. Treat committed recipient identity as sufficient delivery evidence; do not recheck current co-location or visual perception.

**Alternatives considered:** Add recipients to self-action ownership, recheck current location, reconstruct unavailable event-time locations, reuse current visual perception, include general co-located witnesses, deduplicate against self feedback, query event history internally, or update memory and trigger a response directly. These choices respectively blur actor roles, apply present state to past events, invent missing history, confuse senses, broaden audibility without rules, hide composition policy, couple projection to persistence, or bypass later cognition and policy stages.

**Consequences:** Addressed utterances can enter recipient perception without collapsing action resolution, perception, cognition, or response generation. The projection remains a stateless event fragment; the caller still owns candidate windows, delivery tracking, composition, and any deduplication. General witness and overhearing rules remain separate.

### 2026-07-13: Resolve Take v0 as direct co-located acquisition

**Status:** Accepted

**Context:** The action, runtime-state, state-change, and canonical-event contracts already represent taking one object and transferring its placement to a character. The kernel has no transfer, consent, theft, carrying-capacity, duration, competition, or object-specific acquisition rules. Perception is an actor-specific information projection and must not become the authority for canonical mutation.

**Decision:** Add pure `resolve_take(action, *, outcome_id, event_id)`. Treat an object as accessible only when its canonical runtime placement is directly at the authorized actor's exact current location. Unknown, remote, possessed-by-self, possessed-by-another-character, wrong-namespace, and otherwise inaccessible identifiers reject uniformly as `object-not-accessible`. An accessible Take succeeds as `object-taken` at current canonical time, advances no time, changes the exact previous `ObjectAtLocation` placement to `ObjectPossessedByCharacter` for the actor, and records one `ObjectTakenEvent` with the exact previous placement and caller identities. There is no failed branch.

**Alternatives considered:** Use current perception as the actionability authority, permit taking from another character, distinguish rejection causes, treat already-held objects as successful no-ops, invent a fixed duration, infer object rules from authored names or archetypes, add a random check, or bundle witness reactions into resolution. These choices respectively collapse information into truth, invent transfer and conflict mechanics, leak canonical existence or possession, violate state-change meaning, add an ungrounded time rule, bypass versioned mechanics, add unsupported uncertainty, or mix resolution with perception and policy.

**Consequences:** The kernel gains a minimal deterministic possession transition using existing contracts. An object held by the Greybridge courier cannot be taken directly; later transfer, permission, theft, or Help mechanics must model that interaction explicitly. Existing self-action feedback can expose the committed event to the taker, while witness visibility and reactions remain separate.

### 2026-07-13: Project immediate co-located Take witnesses

**Status:** Accepted

**Context:** Take v0 records the object's exact previous placement, advances no time, and changes no character location. This provides enough event-location evidence to determine which other characters immediately witnessed acquisition. General historical witness filtering remains unsafe because present character locations cannot reconstruct past observer locations.

**Decision:** Add pure `project_take_witness_feedback(world, observer_id, events) -> tuple[EventObserved, ...]`. Validate the observer first, then require the entire candidate batch to occur at the world's exact current simulation time, raising `WitnessEventTimeMismatchError` on the first past or future event. Emit only exact `ObjectTakenEvent` values whose actor differs from the observer and whose previous placement is `ObjectAtLocation` at the observer's current canonical location. Preserve order, duplicates, and exact event objects. Treat the committed previous placement as event-location evidence and do not recheck current object state.

**Alternatives considered:** Apply current observer locations to historical events, infer witnesses from current object possession, include the taking actor, treat a previous possessed placement as a location, reuse visual current-state perception, silently ignore stale events, add line-of-sight or attention rules, or trigger NPC reactions directly. These choices respectively rewrite history, discard event-time evidence, duplicate self feedback, invent spatial facts, conflate current visibility with event witnessing, hide coordinator defects, add unsupported mechanics, or bypass the actor loop.

**Consequences:** Co-located NPCs can receive immediate canonical evidence that an object was taken without gaining general event-history omniscience. The caller must supply the current-step event window and remains responsible for composition, delivery tracking, decision triggering, memory, and presentation. Other witness event types and richer visibility remain separate.

### 2026-07-13: Project immediate third-party speech overhearing

**Status:** Accepted

**Context:** Speak v0 records a zero-time addressed utterance and changes no character location. Addressed-speech feedback already delivers the committed event to its recipient, while self-action feedback returns it to its speaker. For another co-located character, exact-current-time canonical locations provide enough evidence for immediate overhearing, but applying current locations to historical speech would rewrite event-time spatial facts. Unlike Take events, `ActorSpokeEvent` does not carry an event location, so its speaker must still exist in the supplied world for co-location to be determined.

**Decision:** Add pure `project_speech_overhearing_feedback(world, observer_id, events) -> tuple[EventObserved, ...]`. Validate the observer first, then require the entire candidate batch to occur at the world's exact current simulation time by reusing `WitnessEventTimeMismatchError`. Next resolve every `ActorSpokeEvent` speaker in input order before observer-specific filtering, raising public `SpeechSpeakerNotFoundError` with the event and speaker identities for the first absent speaker. Emit exact speech events only to an observer who is neither speaker nor addressed recipient and whose current canonical location equals the resolved speaker's current location. Preserve order, duplicates, and exact event objects. Do not revalidate recipient existence or location.

**Alternatives considered:** Treat all co-located participants identically, include the speaker or addressed recipient, accept historical speech using current locations, add event location to the canonical schema, silently ignore absent speakers, reuse the observer-not-found error for a speaker, validate only events that would match one observer, recheck recipient delivery, introduce a generic witness engine, or trigger comprehension and reactions directly. These choices respectively erase distinct information paths, duplicate existing feedback, rewrite history, broaden a stable event contract unnecessarily, conceal malformed evidence, misname the failing role, hide candidate-window defects, contradict committed delivery evidence, freeze unrelated event semantics, or bypass cognition and policy.

**Consequences:** A nearby third party can receive immediate canonical speech evidence through a clearly named audibility path without making all witness rules generic. The projection remains a stateless fragment; candidate windows, delivery tracking, composition, deduplication, comprehension, memory, reactions, richer hearing mechanics, and presentation remain caller or later-layer responsibilities.

### 2026-07-13: Begin Use mechanics with bound boolean-world-fact effects

**Status:** Accepted

**Context:** The Greybridge vertical slice requires reinforcement through Use, but current rule packages contain only reference catalogs and runtime state cannot represent that the bridge was reinforced. Implementing a resolver first would either hard-code Greybridge into the stable kernel or record an effectless success. A general condition system or effects language would broaden the first playable mechanic substantially.

**Decision:** Extend content schema version 1 backward-compatibly with an optional object-use-mechanic catalog in rule packs and optional boolean-world-fact and object-use-binding catalogs in scenario packs. A reusable mechanic names an object archetype, location target, positive duration, and closed `set_boolean_world_fact` effect kind; a scenario binding supplies the concrete object, target location, fact, and target boolean. Add complete identifier-linked `BooleanWorldFactState` overlays, self-verifying `BooleanWorldFactChanged` deltas, semantic reference and binding-ambiguity validation, and atomic commitment support. Greybridge `0.2.0` binds carried reinforcement materials used at the span to `bridge-reinforced=true` after 300 seconds. Preserve the `0.1.0` package versions. The next resolver requires actor possession and target co-location, does not consume the object, and uniformly rejects inapplicable use.

**Alternatives considered:** Hard-code bridge state in the kernel, record effectless Use success, put arbitrary properties or effect dictionaries in YAML, build a general condition or expression language, attach reinforcement to one directed connection, consume materials before destruction or quantity state exists, or postpone Use until every progression and flood rule is designed. These choices respectively violate package independence, claim a consequence that did not occur, weaken validation, overbuild the vertical slice, misrepresent one physical bridge as one travel direction, invent unsupported object state, or delay an already grounded deterministic mechanic.

**Consequences:** Versioned packages gain their first narrowly executable mechanic without allowing authored code or generic effects, and canonical state can represent one inspectable scenario truth needed by later flood resolution. Boolean facts are a deliberate vertical-slice compromise, not a universal condition model. TASK-033 owns contracts, validation, Greybridge `0.2.0`, and commitment; TASK-034 owns Use resolution and dispatch. Checks, progression, consumption, Help, scheduled consequences, perception, persistence, and presentation remain separate.

### 2026-07-13: Resolve bound Use as a deterministic authored effect

**Status:** Accepted

**Context:** TASK-033 makes one reusable object-use mechanic, its scenario binding, strict boolean fact state, typed fact delta, and atomic commitment representable. The resolver still must prove that a concrete proposal selects that authored capability and that the actor can physically apply the possessed object at the bound location. Exposing distinct rejection reasons would leak canonical state and package content through an actor-facing action boundary.

**Decision:** Add pure `resolve_use(action, *, outcome_id, event_id)`. Match the proposal's exact object and location target to one validated scenario binding, resolve its mechanic, require the actor at that location and the object in that actor's canonical possession, and require the bound fact to differ from its authored target. Every inapplicable proposal rejects uniformly as `use-not-applicable` at current time. An applicable proposal succeeds as `object-used` after the mechanic's authored duration, emits ordered boolean-fact then simulation-time changes, and records one `ObjectUsedEvent` containing the proposal's exact target and caller identities. Dispatch routes Use while Help remains unavailable. There is no failed branch, object consumption, or implicit downstream consequence.

**Alternatives considered:** Dispatch by mechanic registry, match only object archetype, accept any co-located object without possession, expose separate missing-binding, possession, location, and already-applied reasons, treat repeated Use as a successful no-op, consume materials, change bridge connections directly, or process flood and witness consequences inside the resolver. These choices respectively add unnecessary infrastructure, discard scenario specificity, weaken physical authority, leak canonical truth, violate state-change meaning, invent unsupported object state, bypass the authored fact boundary, or collapse resolution into scheduling and perception.

**Consequences:** Greybridge reinforcement becomes executable through package-authored data without embedding scenario identities in Python. A successful action advances time and changes only the bound canonical fact; commitment, newly eligible scheduled activities, event feedback, progression, and presentation remain explicit later boundaries. The narrow resolver can be replaced or extended when accepted mechanics add target or effect variants.

### 2026-07-13: Separate documentation audiences and budget delegated context

**Status:** Accepted

**Context:** README, architecture, requirements, decisions, task briefs, and handoffs increasingly repeated the same contracts. The duplication made human navigation ambiguous and allowed a fresh agent to consume large amounts of irrelevant context even when it received no planning-chat history.

**Decision:** Give each documentation artifact one primary audience and ownership role. README is a concise landing page; the domain guide is non-normative orientation; glossary, requirements, decisions, and high-level design retain their existing canonical responsibilities; completed tasks and reviews remain historical evidence. A delegated task brief references stable truth instead of copying it, routes exact sections or IDs, records a soft pre-code documentation budget, excludes discovery and historical artifacts by default, and reports the context actually used.

**Alternatives considered:** Delete completed history, split every large canonical document, or rely on agents to decide what to read. Deletion loses evidence; broad file splitting creates link churn without guaranteeing smaller prompts; unbounded exploration makes context cost and information authority invisible.

**Consequences:** Human onboarding and agent execution use different paths over the same repository knowledge. Task authors must justify broad context, reviewers can detect irrelevant routing, and stable contracts remain inspectable without being repeated in every task. The initial budget is a soft diagnostic threshold and may be revised from measured delegation evidence.

### 2026-07-13: Route agent work through one responsibility-specific guide

**Status:** Accepted

**Context:** The root agent instructions mixed universal repository rules with coding, planning, integration, and review procedures. They were useful to an implementer but noisy and incomplete for architecture review, while adding more role sections would make every agent pay the context cost. Filesystem-scoped instructions would not solve the distinction because architects, implementers, and reviewers may inspect the same source paths.

**Decision:** Keep root `AGENTS.md` as a compact repository-wide rule set and semantic work-mode router. Select exactly one detailed guide for the active responsibility: architect and integrator, implementer, or reviewer. Ready task briefs name the execution guide explicitly and include it in their context budget. A materially changed responsibility is completed or handed off before another guide is selected; role guides are not combined by default.

**Alternatives considered:** Keep one comprehensive root file, use nested instructions under source directories, or create a guide for every prospective agent label. One root file repeats irrelevant procedure; directory routing describes file location rather than responsibility; speculative roles add maintenance and prompt cost before their workflows stabilize.

**Consequences:** Planning, implementation, and independent evaluation receive different procedures while sharing the same canonical project truth. Root instructions stay broadly applicable, delegated context becomes measurable, and new role guides require demonstrated repetition rather than anticipation.

### 2026-07-13: Give one application transaction ownership of step completion

**Status:** Accepted

**Context:** The M3.5 review found a coherent pure kernel boundary but identified durable transaction ownership as the critical M4 seam. Independent repository commits could expose a replacement world without its events or trace, lose scheduled-queue consumption, or present a step that later fails to persist completely.

**Decision:** The turn coordinator owns one application-level SQLite transaction for a completed simulation step. Replacement world state, canonical events, scheduled-queue effects, authoritative character data, and the simulation-step trace participate in that transaction. Repositories serialize already validated domain results under the shared transaction and do not independently define completion. Presentation may observe the new step only after the transaction commits.

**Alternatives considered:** Let each repository commit independently, make the database interpret state changes, or treat in-memory commitment as durable completion. Independent commits permit partial steps; database rule interpretation creates a second simulation authority; in-memory success does not survive process failure.

**Consequences:** SQLite remains authoritative storage without owning simulation rules. Transaction failure leaves the previous committed world recoverable and cannot report or present the attempted step as complete. M4 persistence and coordinator tests must cover rollback, restart recovery, and post-commit visibility.

### 2026-07-13: Persist the current world as a typed snapshot with separate history

**Status:** Accepted

**Context:** The kernel already treats canonical runtime state as one immutable validated snapshot, while the initial world is small and its model is still evolving. Fully normalizing each state field would duplicate the domain model in a second schema before the project has demonstrated query or scale requirements. A single opaque payload without explicit identity or validation would make compatibility and inspection fragile.

**Decision:** Store the current `WorldState` as one schema-versioned JSON snapshot in the singleton world record. Keep world identity, revision, and exact rule-pack and scenario-pack identities and versions as explicit columns. On load, decode the payload through the strict Pydantic runtime contract and validate it against the recorded packages before admitting it to the simulation. Store canonical events and later simulation-step traces as separate append-only history records rather than embedding them in the current snapshot.

**Alternatives considered:** Fully normalize the complete world state, store all persistence as one JSON document, or use unrelated JSON files. Full normalization creates schema duplication and migration work without a current query consumer; one document obscures history and package ownership; separate files cannot provide the required atomic transaction.

**Consequences:** Restart recovery matches the kernel's immutable aggregate boundary, while event and trace history remain independently inspectable. Snapshot schema changes require explicit version handling, and persistence tests must prove strict decoding, package ownership, revision replacement, and atomic history writes.

### 2026-07-13: Expose persistence through an explicitly committed unit of work

**Status:** Accepted

**Context:** A completed simulation step will eventually involve the current world, canonical events, scheduled activity effects, character information, and a trace. Repository-owned commits would permit partial durability, while an automatically successful context-manager exit could commit after an early return that never explicitly declared the application step complete.

**Decision:** Provide an application-facing SQLite unit of work. All participating repositories are bound to its one active `sqlite3.Connection` and expose no independent commit operation. The application must explicitly call `commit()` after the complete step is ready. An exception or leaving the context without that call rolls the transaction back. The later turn coordinator owns this lifecycle.

**Alternatives considered:** Let repositories manage transactions, pass a raw connection through every application call, or commit automatically on a clean context-manager exit. Repository transactions break atomic step ownership; pervasive raw connections leak storage mechanics; implicit success can make an incomplete application path durable.

**Consequences:** Transaction ownership is visible and testable without an ORM or new dependency. Forgetting to commit fails safely, repository tests can prove they do not make data independently durable, and coordinator tests can cover rollback and post-commit visibility.

### 2026-07-13: Bootstrap one version-gated SQLite schema before building migrations

**Status:** Superseded by `Migrate SQLite V1 to V2 for trace history`

**Context:** Persistence needs an explicit compatibility boundary immediately, but only one database schema exists. A generic migration framework or third-party migration dependency would have no second version to migrate, while repeated `CREATE TABLE IF NOT EXISTS` calls could silently accept an incompatible database.

**Decision:** Use SQLite `PRAGMA user_version` as the initial schema-version gate. Opening an empty version-0 database creates the complete version-1 schema and records version 1 in the same transaction. Opening version 1 preserves it unchanged. Any other version fails clearly without modifying the database. Add ordered migrations only when version 2 supplies a concrete migration case.

**Alternatives considered:** Add Alembic immediately, build an internal generic migration registry, or rely indefinitely on idempotent creation statements. The first two anticipate absent migrations; the last cannot distinguish a current database from a structurally stale one.

**Consequences:** V1 initialization and incompatibility behavior remain small and testable with the standard library. The first actual schema evolution must introduce and test an explicit V1-to-V2 path rather than weakening the version gate.

### 2026-07-13: Keep package resolution outside the world repository

**Status:** Accepted

**Context:** A durable world records the exact packages that define it, and its JSON must be decoded strictly. Resolving package files and checking state completeness against authored definitions, however, are application and simulation concerns rather than SQLite mechanics. Combining them would couple repository tests and storage access to package paths and Greybridge content.

**Decision:** The world repository decodes a strict stored-world record containing identity, revision, exact package references, `WorldState`, and `ScheduledActivityQueue`. It does not locate or load game packages and does not return `ValidatedWorldState`. A later resume or application service resolves the recorded versions, validates the decoded state against those packages, and admits only the resulting validated wrapper to the kernel.

**Alternatives considered:** Make the repository load packages, store complete package definitions inside the world row, or return untyped JSON to the application. Repository loading mixes persistence with filesystem and semantic concerns; embedded definitions duplicate versioned authored content; untyped payloads weaken the runtime boundary.

**Consequences:** Storage tests remain independent of package layout while malformed persisted records still fail strict decoding. Restart recovery has an explicit two-stage boundary: durable record decoding followed by package-aware world validation.

### 2026-07-13: Protect world replacement with a monotonic revision

**Status:** Accepted

**Context:** The initial application serializes simulation work, but later HTTP requests, retries, or application mistakes can still retain a stale loaded snapshot. Unconditionally replacing the singleton row would silently discard a newer committed world even without supporting general multi-user concurrency.

**Decision:** Creating the singleton world assigns revision 0. Replacement supplies the revision that was loaded and updates only if it still matches the durable row. The repository calculates and returns the next revision, exactly one greater than the prior value. A mismatch raises a specific persistence conflict; the surrounding unit of work cannot commit any associated records.

**Alternatives considered:** Replace unconditionally, let callers choose the next revision, or add a general lock manager. Unconditional writes permit lost updates; caller-chosen revisions weaken monotonicity; a lock manager exceeds the local single-world requirement.

**Consequences:** A small compare-and-swap condition detects stale application state and duplicate processing without changing deterministic scheduling. Tests must prove initial revision, monotonic replacement, conflict signaling, and rollback of other writes in the same unit of work.

### 2026-07-13: Order canonical event history by durable insertion sequence

**Status:** Accepted

**Context:** Canonical events already have identity, outcome provenance, type, and simulation occurrence time, but multiple ordered events can share one timestamp. Persistence also needs to associate the history produced by a transition with the replacement world revision before a complete simulation-step trace contract exists.

**Decision:** Store each canonical event as strict discriminated-union JSON with explicit event ID, outcome ID, event type, occurrence time, world identity, resulting world revision, and a database-assigned durable insertion sequence. Batch insertion preserves resolver order, reads use insertion order rather than occurrence time, and event IDs are unique. Duplicate identity or invalid payload failure aborts the surrounding unit of work.

**Alternatives considered:** Sort history by occurrence time, embed events in the current world snapshot, or store opaque JSON without indexed provenance. Time does not break ties; embedding loses independent append-only history; opaque payloads weaken validation and inspection.

**Consequences:** Event history is deterministic and revision-linked before full step traces exist. Persistence can reconstruct ordered canonical consequences, and atomic tests can use world replacement plus event append as two meaningful participants in one unit of work.

### 2026-07-13: Persist the minimal completed actor-action trace

**Status:** Accepted

**Context:** The first atomic coordinator needs durable causal evidence, but LLM calls, actor cognition, scheduled execution, memory, beliefs, narration, and System direction do not yet participate in its executable path. Designing fields for those future stages now would freeze guesses and inflate every delegated context. Persisting only an outcome would also omit the trusted submission and actor-limited evidence needed to inspect the first real authority chain.

**Decision:** Define trace schema version 1 as one strict `CompletedActorActionStepTrace` containing the trusted submission, its simulation-step and decision-context identities, the exact resolved outcome, the resulting actor current-state perception snapshot, and self-event feedback. The model validates identity, actor, and simulation-time agreement. Store it as separate append-only strict JSON with explicit world, resulting revision, simulation-step, outcome, and status metadata. This initial contract represents only coordinated submissions that reach a resolved and durably committed outcome; pre-resolution operational failures remain exceptions until a real input boundary supplies a concrete consumer for attempted-step failure traces.

**Alternatives considered:** Add placeholders for every future trace stage, store an arbitrary stage dictionary, persist only the outcome, or postpone trace persistence until after LLM integration. Placeholders and generic dictionaries weaken strict context engineering; outcome-only history loses trusted provenance and perception evidence; postponement prevents the coordinator from proving the accepted atomic completion boundary.

**Consequences:** The first trace is small, inspectable, and sufficient for the authorization-to-perception regression. Later stages require an explicit backward-compatible trace variant or payload-schema evolution rather than optional speculative fields. Operational failures before outcome resolution are not yet durable attempted-step records.

### 2026-07-13: Compose the first coordinator before scheduled execution

**Status:** Accepted

**Context:** Authorization, dispatch, deterministic resolution, outcome commitment, perception projection, SQLite repositories, and an explicit unit of work are implemented. Scheduled activities can only be selected: environmental schedules have no accepted mechanic resolver, NPC activities have no policy execution boundary, and System director hooks have no proposal implementation. Removing due records without executing them would lose work, while repeatedly selecting and retaining them would not define progress.

**Decision:** The first application coordinator composes one trusted actor-action submission through package compatibility and world validation, authorization, dispatch, commitment, actor perception, world replacement, event append, trace append, and explicit SQLite commit. It preserves the scheduled queue exactly and returns completion only after durable commit. Every coordinated outcome, including rejection or an unchanged state object, advances the durable world revision by one so the completed trace and any events have one unambiguous resulting revision. Scheduled selection and execution remain a separate follow-up after variant-specific execution semantics exist.

**Alternatives considered:** Implement placeholder scheduled handlers, silently consume eligible activities, retain due activities after claiming to process them, combine the task with NPC and director policy work, or postpone all coordination. These options respectively invent mechanics, lose work, cause repeated eligibility, cross milestone boundaries, or delay the first end-to-end application seam despite sufficient implemented foundations.

**Consequences:** M4 gains a real atomic player-action path without pretending Greybridge scheduling is executable. The coordinator can support deterministic application and API work with an empty or future-only queue. Time-advancing actions do not yet resolve newly due activities, so the full `TIME-005` and `SCHEDULE-003` through `SCHEDULE-005` behavior remains explicitly incomplete.

### 2026-07-13: Migrate SQLite V1 to V2 for trace history

**Status:** Accepted

**Context:** TASK-036 intentionally stopped at schema V1 because no trace contract existed. The completed actor-action trace is now a concrete second-schema consumer, and existing V1 databases may already contain the authoritative world and canonical event history.

**Decision:** Make schema V2 the current SQLite schema. New empty databases create the complete V2 schema transactionally. Opening V1 transactionally adds the simulation-step trace table and advances `PRAGMA user_version` to 2 without rewriting existing world or event rows. Opening V2 preserves it; any other version fails unchanged. Implement only this concrete V1-to-V2 path, not a generic migration framework.

**Alternatives considered:** Reject V1 databases, recreate them destructively, keep traces outside SQLite, or introduce Alembic or a generic migration registry. Rejection and recreation violate persistence continuity; external trace files break atomicity; migration infrastructure remains unjustified for one direct transition.

**Consequences:** Existing V1 state survives the first real schema evolution, and trace history joins the authoritative transaction. Migration tests must prove retained world and event data, atomic failure behavior, current-version reopen, and rejection of unsupported versions.

### 2026-07-13: Materialize initial state without requiring future actor policies

**Status:** Accepted

**Context:** The package-validation requirement previously required every declared NPC policy implementation before world creation. That conflicts with the accepted roadmap: M4 must create and resume the world before M5 implements rule and LLM actor policies. Adding placeholder policy registrations would claim executable capability that does not exist and make a deterministic data-materialization boundary depend on later cognition infrastructure.

**Decision:** World creation requires structurally loaded and semantically validated packages, then deterministically materializes their authored initial placements and facts. Application-owned policy implementation compatibility is checked before the corresponding NPC policy is executed, not before its immutable reference can participate in initial world state. Package validation continues to prove policy reference identity and type agreement.

### 2026-07-13: Keep trusted turn metadata on the server side of the first HTTP boundary

**Status:** Accepted

**Context:** The atomic coordinator correctly accepts a trusted `ActorActionSubmission`, but an HTTP request is untrusted. Exposing that submission directly would let a client claim actor identity, source provenance, and causal identities. Waiting for the later free-text interpreter would block the M4 API and deterministic Streamlit work even though typed action proposals already provide a useful bounded input.

**Decision:** The first FastAPI turn accepts only one strict actor-action proposal. The application binds it to the validated scenario's sole player, records a fixed application-owned player-interpreter source, and assigns proposal, step, decision-context, outcome, and event UUIDs through an injected identity factory before calling the existing coordinator. Responses expose only completion metadata, outcome status and reason, current player perception, and self-event feedback. They do not expose canonical state, scheduled work, state changes, the full trace, or client-selectable provenance. World creation and development reset likewise use server-assigned world identities. Reset is guarded by an explicit application setting.

**Alternatives considered:** Accept the complete trusted submission over HTTP, let clients select runtime UUIDs, wait for the LLM interpreter, expose the coordinator trace directly, or build a general command/authentication framework. These choices respectively cross the trust boundary, weaken identity ownership, stall the deterministic M4 seam, leak canonical and provenance data, or introduce infrastructure without a first-slice consumer.

**Consequences:** M4 gains a deterministic player-action API that composes accepted services without pretending text interpretation exists. Tests can inject a deterministic UUID factory, while production defaults may use UUID4. The later player interpreter can replace proposal construction upstream without changing the coordinator. Production authentication, retry/idempotency semantics, text input, narration, and inspection remain separate decisions.

**Alternatives considered:** Reorder M5 before persistence lifecycle, register non-executable placeholder policies, or prohibit creating Greybridge until all actor policies exist. Reordering couples persistence to LLM work; placeholders weaken truthful readiness; prohibition blocks restart and API work that does not execute NPC cognition.

**Consequences:** M4 can establish an honest persistent lifecycle while the Greybridge NPCs remain inert. No caller may infer executable policy availability from world creation or `ValidatedGamePackages`; M5 must introduce and enforce the implementation registry at the policy-execution boundary.

### 2026-07-13: Use explicit create, resume, and destructive development-reset operations

**Status:** Accepted

**Context:** The singleton repository can create and replace snapshots but does not yet define how authored initial data becomes runtime state, how restart resolves exact packages, or what reset does to append-only history. Treating reset as ordinary replacement would retain history belonging to a different initial timeline and continue its revision sequence, while general CRUD would weaken the one-world boundary.

**Decision:** Add a small application lifecycle boundary. Creation accepts validated packages and a caller-assigned world identity, deterministically builds and validates the initial state, stores an empty scheduled queue, and commits revision 0. Resume reads the durable package references, loads only those exact directories beneath a configured package root, validates the package pair and world state, and returns an active-world result without writing. The explicitly named development reset requires an existing world and transactionally deletes the singleton world plus all event and trace history before creating a caller-identified known initial world at revision 0.

**Alternatives considered:** Hide lifecycle behavior in SQLite repositories, preserve old histories across reset, make reset an alias for create, discover the newest package version, generate a world identity, or add save-slot abstractions. These respectively mix application and storage concerns, join unrelated timelines, blur authority, make restarts non-reproducible, hide identity provenance, or exceed the initial product scope.

**Consequences:** Creation and reset are explicit mutations that return only after commit; reset failure preserves the complete prior timeline. Resume is reproducible from recorded package ownership and remains read-only. Reset is intentionally destructive development tooling, produces no event or trace, and does not represent an in-world action.

### 2026-07-13: Begin Streamlit as a thin deterministic HTTP client

**Status:** Accepted

**Context:** The accepted FastAPI boundary can create, resume, reset, and advance the singleton world from strict action proposals, while text interpretation and narration remain M5 work. Letting Streamlit import lifecycle or simulation services would create a second application path and weaken the server-owned trust boundary. Blocking all UI work until the LLM presentation pipeline exists would leave the implemented M4 seam difficult to exercise as a player.

**Decision:** Implement the first player page as a thin HTTP client configured with an API base URL. It validates the existing API response models, exposes deterministic forms for the seven typed proposal variants, and renders only lifecycle metadata, committed outcome status and reason, current player perception, and self-event feedback. Presentation history lives only in Streamlit session state and is never authoritative. Creation and explicitly confirmed development reset use their existing endpoints. The page reports transport and application failures without claiming completion. It does not start an ASGI server, access SQLite or packages, interpret prose, narrate, or expose inspection data.

**Alternatives considered:** Call application services directly from Streamlit, embed the FastAPI app through a test transport, wait for M5, accept arbitrary JSON proposals, or build a general UI state architecture. These respectively bypass the HTTP authority boundary, misuse test infrastructure at runtime, delay an executable player seam, expose low-level contracts unsafely, or add abstractions without a second page consumer.

**Consequences:** M4 ends with one honest structured player interface that exercises the real durable boundary without pretending the LLM experience is complete. A separately running API process remains an explicit prerequisite; deployment bootstrap and production configuration stay deferred. M5 can replace structured forms with interpreted player text and generated narration while preserving the API client and committed-result discipline.

### 2026-07-14: Start actor policies with one pure caretaker decision

**Status:** Accepted

**Context:** M5 needs a real deterministic NPC policy before an actor runtime or scheduled NPC coordinator has a concrete policy contract to invoke. The current perception snapshot can represent the caretaker's location, available outgoing connections, and the reinforcement materials when they are nearby or possessed, but it does not yet expose boolean world facts, durable memory, or mutable plans. Building a registry, scheduler integration, or a general rule language now would combine separate boundaries and freeze abstractions before their first consumer exists.

**Decision:** Define one strict immutable `NpcDecisionContext` containing an application-assigned UUID, NPC identity, authored identity summary, non-empty goals, current plan, and an actor-matching `PerceptionSnapshot`. It contains no canonical world, trusted submission metadata, beliefs, or memories. Implement the `bridge-caretaker` policy as a pure function from that context to an `ActorActionProposal` payload. It follows one fixed priority sequence from perceptible facts: use possessed reinforcement materials at `greybridge-span`; move possessed materials from the waystation toward the span through an observed available connection; take materials observed at the current location; or leave the span for the waystation through an observed available connection to seek them. If no rule safely applies, return `Wait(duration_seconds=60)`. A context for any other NPC is a caller error rather than permission for the caretaker implementation to act as that NPC.

**Alternatives considered:** Pass validated world state to the policy, encode executable Python behavior in YAML, introduce a generic registry before policy execution exists, let the policy create trusted submission identities, or make a placeholder policy that always waits. These respectively violate the information boundary, mix data and executable authority, add infrastructure without a caller, cross the application trust boundary, or fail to exercise meaningful rule choice.

**Consequences:** The first rule policy is deterministic, inspectable, testable without an LLM, and ready for a later actor runtime to invoke and wrap in trusted provenance. It can perform the initial seek, take, return, and reinforce proposal sequence from perception. Because current perception does not reveal the resulting `bridge-reinforced` fact or durable internal completion state, later eligibility/context work must prevent repeated reinforcement attempts after success; TASK-041 does not pretend to complete scheduled actor execution.

### 2026-07-14: Build the first local gateway around functional structured output

**Status:** Accepted

**Context:** Player interpretation and the courier policy need the same measured local Gemma request behavior, while the later narrator also needs the same provider transport. Introducing the OpenAI SDK would add a dependency without providing server-side schema enforcement, and embedding HTTP calls or repair logic in each role would duplicate the most sensitive context-engineering boundary. The role-specific output schemas and safe-failure actions do not exist yet, so the shared layer cannot honestly choose clarification, NPC fallback, or director skip behavior.

**Decision:** Implement a synchronous application-owned `HttpLocalModelGateway` over the existing `httpx2` dependency. Configuration is explicit and injectable: base URL, model, positive timeout, and positive maximum completion tokens. A functional call accepts immutable role messages and a strict Pydantic output-model class. The gateway prepends a deterministic compact JSON Schema instruction and calls `/v1/chat/completions` with temperature zero, `response_format.type=json_object`, and `chat_template_kwargs.enable_thinking=false`. It accepts only a stopped HTTP-200 choice with non-blank `message.content` that passes strict Pydantic JSON validation. Empty or non-stopped content, invalid JSON, and schema errors receive exactly one repair using the same context and settings plus the failed content and normalized errors. Transport, HTTP-status, and malformed-wrapper failures do not repair. The result contains immutable ordered attempt evidence and either an accepted typed value or a failed disposition; it never reads `reasoning_content`, mines prose, applies role fallback, creates trusted submissions, mutates state, persists, or writes a trace.

**Alternatives considered:** Adopt the OpenAI SDK immediately, trust `json_schema` response formatting, let each role own provider transport and repair, return exceptions for every failure, implement asynchronous transport first, or include narrator prose and role-specific fallback in the first task. These respectively add an unneeded abstraction, contradict measured enforcement evidence, duplicate safety logic, weaken evidence-driven safe failure, increase integration complexity before concurrent calls exist, or broaden the task beyond concrete functional consumers.

**Consequences:** Player and NPC functional roles gain one fakeable, evidence-producing boundary with no new dependency, and later trace work can retain its attempt records. The synchronous call may block its invoking worker for the configured timeout, which is acceptable for the initial local single-player slice and can be revisited from measured concurrency. Role consumers must still define prompts, strict output schemas, and their safe-failure mapping. Narrator prose support remains a small later extension over the same provider transport rather than speculative scope in TASK-042.

### 2026-07-14: Interpret one player input without creating authority

**Status:** Accepted

**Context:** The player must be able to combine explicit private thought with one attempted action in free-form text, while the existing application accepts one actor-action proposal per turn. Treating speech as a separate executable channel could create two actions from one input, and letting the interpreter build a trusted submission would allow generated output to claim identity or causality. The first perception model exposes stable IDs but not restricted authored-name enrichment, so a safe initial interpreter can use the exact current snapshot and leave richer display context to a later bounded enrichment task.

**Decision:** Define a strict immutable `PlayerInterpreterOutput` with required nullable fields and a discriminator. An `interpreted` output contains optional non-blank `private_thought`, optional one `proposal`, and no clarification, with at least thought or proposal present. A `clarification` output contains only a non-blank clarification. The proposal schema is the existing Observe, Move, Speak, Take, Use, or Wait subset; speech uses `SpeakActionProposal`, and Help is excluded until its resolver exists. Implement one application service that accepts non-blank player text, one current `PerceptionSnapshot`, and an injected `FunctionalModelGateway`. It sends deterministic role instructions plus the exact snapshot and player text, then preserves the input, snapshot, generation evidence, and final output. An accepted gateway value is returned exactly. Any gateway failure maps to one fixed application-owned clarification. The service creates no UUIDs, trusted source, submission, outcome, event, state change, persistence write, time advancement, or narrative.

**Alternatives considered:** Return separate speech and action channels, let the model create trusted metadata, pass validated world state or unrestricted packages, use arbitrary prompt strings as the only result, include Help despite its unavailable resolver, or combine interpretation with HTTP turn execution. These respectively permit multiple actions, cross the trust boundary, leak canonical information, weaken structured evidence, route into a known capability failure, or make private-thought and clarification semantics transactional before their boundary is tested.

**Consequences:** The player role gains a bounded, fakeable, inspectable interpretation stage that can represent thought-only input, speech, another action, or clarification without claiming success. A later API task can create trusted identities and submit only a present proposal; thought-only and clarification results can return without advancing time. The initial prompt operates on ID-linked perception, so authored display-name enrichment remains a separate improvement rather than an implicit package leak.

### 2026-07-14: Separate lean product and flow stewardship from technical planning

**Status:** Accepted

**Context:** The architect guide combined product-direction facilitation,
roadmap prioritization, technical architecture, task preparation, and
integration. As the roadmap moved through several milestones, that combination
left stakeholder feedback, value prioritization, and blocker stewardship
implicit while asking one responsibility to both choose outcomes and design
their technical realization. The project has one active stakeholder and does
not need a full Scrum process, but it does need a durable feedback loop between
product intent and delivery evidence.

**Decision:** Add a lean `scrum_master` role guide as an explicit hybrid of
product-support and delivery-effectiveness responsibilities. The stakeholder
retains final product authority. The scrum master facilitates alignment with
`doc/goal.md`, proposes and maintains accepted milestone outcomes and priority,
routes feedback, limits work in progress, and drives named blockers toward an
owner and next action. The architect retains requirements, decisions, technical
decomposition, task readiness, integration, and factual task outcomes. The
scrum master hands the architect one prioritized outcome; the architect returns
feasibility evidence, dependencies, risks, readiness or a named blocker, and
integrated outcome evidence. Only the architect or integrator may promote tasks
to Ready or Done. Continue selecting exactly one responsibility-specific guide
at a time.

Apply lean principles through customer value, small demonstrable outcomes,
visible flow, pull-based just-in-time planning, waste removal, and continuous
adaptation. Do not add mandatory sprints, estimates, velocity, recurring
ceremonies, a custom agent profile, or a separate feedback artifact without an
observed need.

**Alternatives considered:** Keep all planning with the architect, model a
strict Scrum Master that cannot steward roadmap priority, create separate
Product Owner and Scrum Master roles, split roadmap and technical planning into
new parallel documents, or add a custom agent immediately. These respectively
preserve the overloaded boundary, omit the stakeholder-facing responsibility
that motivated the change, add unnecessary roles for one stakeholder, increase
handoff and synchronization waste, or specialize runtime configuration before
repeated use demonstrates a need.

**Consequences:** Product value and flow gain an explicit owner without moving
technical authority or integration acceptance. `doc/roadmap.md` remains one
artifact with section-level semantic ownership: the scrum master owns milestone
priority and focus, the architect owns decomposition and readiness, and the
integrator records verified results. The earlier decision to use one active
role guide remains in force but now routes four responsibilities instead of
three. The hybrid name must remain explicit so future agents do not mistake the
role for a standards-pure Scrum Master or allow it to override stakeholder or
architect authority.

### 2026-07-14: Persist player interpretation in a linked input trace

**Status:** Accepted

**Context:** The completed actor-action trace begins only after the application has created a trusted submission and reaches a committed outcome. Free-form player input introduces two valid completion paths before that boundary: explicit thought without a proposal, and clarification after either an accepted model result or a safe failed-generation fallback. Dropping those paths would violate the requirement to retain functional-output evidence and make the inspection history misleading. Holding a SQLite write transaction during local-model latency would unnecessarily serialize the world and make failure recovery less clear.

**Decision:** Add a strict immutable player-input trace separate from the existing completed actor-action trace. It contains an application-assigned player-input identity, the exact `PlayerInterpretationResult` including its ordered functional-generation evidence, and one discriminated completion: thought-only, clarification, or action-linked. The first two retain equal observed and resulting world revisions; the action-linked completion names exactly one existing completed actor-action simulation-step identity and has a resulting revision exactly one greater than the observed revision. Store this trace in its own append-only SQLite table with explicit world/revision/identity/completion metadata, strict payload decoding, database insertion order, and duplicate identity rejection. The trace repository verifies action links against the existing actor-action trace in the same world and resulting revision. SQLite schema version 3 migrates V1 and V2 data transactionally while preserving existing world, event, and actor-action trace records.

The interpretation call remains outside a write unit of work. A later player-turn coordinator will obtain current perception, call the interpreter, then open one unit of work to recheck the observed revision and atomically append either a no-action input trace or both the actor-action and action-linked input traces. This decision adds storage and contracts only; it does not yet define stale-input presentation, trusted submission construction, HTTP behavior, or narration.

**Alternatives considered:** Extend `CompletedActorActionStepTrace` with nullable interpretation fields, use one generic JSON stage dictionary, append no-action inputs only to Streamlit session state, or persist an input trace before calling the model. Nullable fields would blur a completed action with no-action input and weaken its strict evidence contract; a generic dictionary loses type-directed validation; session-only history is not durable or inspectable; and pre-call persistence cannot retain the final generation disposition or express atomic linkage to an action outcome.

**Consequences:** Functional player evidence becomes durable for every future completed player turn without changing the established actor-action trace. Persistence gains one concrete V2-to-V3 migration rather than a generic migration framework. The next API/coordinator task must preserve the observed-revision compare-and-commit boundary and may not claim a player input completed until its corresponding input trace commits.

### 2026-07-14: Coordinate a player turn around model latency and one commit

**Status:** Accepted

**Context:** A player interpretation is based on one current perception, but the local model may take long enough for another request to change the singleton world before its output returns. The existing actor-action coordinator owns its complete SQLite unit of work, while an action-linked input trace must be appended in that same transaction. Retrying an old interpretation on a newer world would silently apply a proposal against information the player did not receive; persisting it separately would weaken the trace's causal guarantee.

**Decision:** Add one application-level free-form player-turn coordinator. It reads and validates the singleton world, derives the sole player's current perception and captures its revision, then closes that read transaction before invoking the injected player interpreter. It reopens one unit of work, requires the exact observed world identity and revision, and returns a typed stale-input failure without writes if they differ. For thought-only or clarification output it assigns one player-input UUID, appends the matching no-action trace at the unchanged revision, commits, and returns the exact private thought or clarification. For a proposal it assigns player-input, proposal, simulation-step, decision-context, outcome, and event UUIDs; constructs the trusted player-interpreter submission; uses a narrowly extracted no-commit actor-action composition helper; appends both the completed actor-action and action-linked player-input traces; and commits once.

The coordinator exposes no raw gateway evidence. Gateway failure remains the already accepted fixed clarification and therefore follows the durable clarification path. The first HTTP endpoint is a separate task over this application contract, as is runtime local-model configuration.

**Alternatives considered:** Hold one write transaction across the model call, retry the interpreted proposal automatically after a revision conflict, call the existing self-committing actor coordinator and append the input trace afterward, or combine coordinator, HTTP, Streamlit, and runtime-provider configuration in one task. These respectively serialize SQLite during provider latency, apply an interpretation to a different perception, lose atomic trace linkage, or make failure and authority boundaries unnecessarily difficult to verify.

**Consequences:** Each completed free-form player input has one durable, revision-correct causal record; stale attempts are honestly rejected rather than reinterpreted silently. The extracted actor composition helper has one immediate consumer and preserves the existing public actor-action coordinator behavior. HTTP transport and model runtime configuration remain thin follow-ons rather than sources of simulation authority.
