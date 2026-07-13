# Domain guide

## Purpose and authority

This guide gives developers a coherent mental model of the simulation. It explains how the main concepts relate; it does not define detailed behavior.

Use the following sources when exact wording matters:

* [`glossary.md`](glossary.md) defines canonical vocabulary;
* [`requirements.md`](requirements.md) defines accepted observable behavior and constraints;
* [`decisions.md`](decisions.md) records accepted architectural choices and rationale;
* [`high_level_design.md`](high_level_design.md) defines component and information-flow boundaries; and
* source and behavioral tests show the currently implemented contracts.

If this guide conflicts with those sources, correct this guide rather than treating it as a second specification.

## The central model

The project separates what exists from what an actor knows and from how an experience is narrated:

```text
canonical world state and events
            |
            v
    actor-specific perception
            |
            v
        sensemaking
            |
            v
           intent
            |
            v
     action proposal
            |
            v
  authorization and rules
            |
            v
          outcome
            |
            v
 canonical state replacement
            |
            +----> new perception
            |
            +----> feedback for later sensemaking
```

For an NPC, a rule-based or LLM-assisted decision policy may perform sensemaking and choose an intent. For the player, the human performs those stages. The application may interpret explicitly supplied text, but it must not invent the player's motives.

## Canonical truth

Canonical world state contains the changing facts the simulation currently accepts: simulation time, character locations, object placement or possession, connection availability, and boolean world facts. Canonical events are typed historical facts produced by resolved outcomes.

Generated prose is never canonical truth. An LLM may describe a damaged bridge, propose that an NPC moves, or narrate an object being used, but those statements do not change the world. Only the simulation arbiter may validate and commit a canonical transition.

This is the project's most important trust boundary:

> LLM output is untrusted interpretation or proposal data until deterministic code validates and resolves it.

## Packages and runtime state

Game packages contain authored definitions that should not change during a running world:

* a rule pack defines reusable archetypes, policies, and mechanics;
* a scenario pack defines locations, connections, inhabitants, initial content, and bindings to rule-pack mechanics.

Runtime world state contains only changing overlays linked to package definitions by stable identifiers. For example, a connection's authored endpoints and traversal duration belong to the scenario package, while its current availability belongs to runtime state.

Keeping these layers separate avoids copying definitions into every snapshot and prevents SQLite records or generated text from silently redefining rules.

## From proposal to committed outcome

An actor interaction crosses several deliberately separate boundaries.

### 1. Action proposal

An action proposal is a strict operation payload such as Move, Speak, Take, Use, Observe, or Wait. It expresses what an actor wants to attempt. It contains no trusted identity or proof that the source may act.

### 2. Action proposal submission

The application adds trusted metadata: proposal and simulation-step identities, the intended actor, decision-context identity, and player-interpreter or NPC-policy provenance. Generated output must not be allowed to invent this trusted envelope.

### 3. Authorization

Authorization checks whether the submission source may act for the intended character. It does not decide whether the proposed operation is possible in the current situation.

### 4. Resolution

A concrete deterministic resolver checks operation-specific rules against validated packages and current canonical state. It returns a typed rejected, failed, or succeeded outcome. Resolution produces evidence; it does not mutate the input world.

### 5. Commitment

The arbiter validates an outcome's complete ordered change set before applying anything. A valid commit returns a replacement validated world snapshot while retaining the exact outcome and canonical events. Invalid commitment changes nothing.

This separation keeps authority inspectable: policies propose, authorization establishes source authority, resolvers interpret rules, and commitment replaces canonical state.

## Events, observations, and perception

An event records that something canonically occurred. It contains factual identifiers, time, causation, and operation-specific payload. It does not decide who noticed it and contains no narrative prose.

An observation is information available to one character. The perception engine derives observations from canonical state or selected canonical events under explicit visibility rules. Different actors may therefore receive different observations about the same reality.

A perception snapshot groups one actor's observations at one simulation time. Narration should be derived from the player's perception and confirmed System notifications, not from unrestricted canonical state.

Memory and belief are later character-specific layers:

* episodic memory retains selected observations as durable character history;
* belief represents what a character thinks is true and may be incorrect;
* neither memory nor belief changes canonical reality merely by being recorded.

## Simulation arbiter and turn coordinator

The simulation arbiter owns domain authority. It validates proposals, applies rules, controls canonical randomness, resolves outcomes, and creates canonical state transitions and events.

The turn coordinator is an application service. It will orchestrate one simulation step across interpretation, authorization, resolution, scheduling, actor decisions, perception, persistence, and presentation. It may call authoritative domain boundaries but must not duplicate their rules.

The distinction matters for persistence:

* the arbiter determines the valid replacement world;
* the coordinator owns the application transaction and completion workflow;
* SQLite durably stores already validated results;
* presentation runs only after successful persistence.

SQLite is authoritative storage, but it is not simulation-rule authority.

## Time, scheduling, and randomness

Simulation time advances through resolved consequential actions rather than wall-clock time. When time advances, scheduled environmental, NPC, and System director activities may become eligible.

Eligibility selection is deterministic. Due activities are ordered by simulation time, phase, and stable insertion sequence. The initial scheduler contracts partition work but do not yet claim, execute, retry, or persist it; those responsibilities join the future atomic simulation-step boundary.

Randomness is permitted only through explicit rule checks. The arbiter receives an injected random source and records the request bounds, purpose, identity, and result. An LLM response is never a canonical random draw.

## LLM roles

LLMs assist the system through bounded roles:

* the player input interpreter proposes structured interpretations of explicit player text;
* an NPC decision policy may propose an action from bounded actor context;
* the System director proposes creative interventions only when an authored hook is eligible;
* the narrator turns committed player-visible facts into prose.

Functional roles return strict structured output with one repair attempt and safe failure. The narrator may return prose because narration is presentation rather than canonical authority.

Each role receives a purpose-built context envelope. Complete world state, unrelated history, private knowledge belonging to another actor, and planning-chat transcripts are not valid shortcuts for context assembly.

## Greybridge as the vertical slice

Storm at Greybridge is the first scenario used to exercise these boundaries. It combines a small location graph, incomplete information, objects, authored Use behavior, action-driven time, scheduled environmental pressure, NPC roles, and future System director hooks without requiring combat.

The current repository contains the deterministic package and kernel foundation, including a bound reinforcement Use mechanic. The complete flood, NPC execution, System direction, progression, persistence, and player interface remain future milestones. “Greybridge packages validate” therefore does not mean “Greybridge is fully playable.”

## How to explore the implementation

Start from the concept you need rather than loading every document:

1. Use the glossary for the canonical term.
2. Find its requirement IDs for exact accepted behavior.
3. Read named decisions only when rationale or authority matters.
4. Read the relevant high-level-design section for component ownership.
5. Trace the public symbol in `src/llm_system/` and its focused tests.

For delegated work, the Ready task brief performs this routing. README, this guide, completed task briefs, the roadmap, ideas, and review history are not default implementation context unless the task explicitly concerns them.
