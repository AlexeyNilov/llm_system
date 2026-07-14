# Project Vision and Development Goal

## Project vision

Build a persistent, inspectable, open-ended narrative simulation where a human player and autonomous NPCs inhabit the same evolving world.

The system should combine deterministic simulation with local LLM assistance:

- The simulation owns canonical truth, rules, state transitions, time, and persistence.
- LLMs interpret bounded information, form intentions, propose actions, and present confirmed results.
- Players and NPCs act from limited, role-specific knowledge rather than full world state.
- Every important step—from perception to decision, validation, resolution, persistence, and narration—is structured, inspectable, and testable.
- Game mechanics and scenarios should be replaceable through versioned packages without destabilizing the simulation kernel.

The long-term product is an extensible platform for experimenting with believable autonomous characters, information boundaries, local LLM integration, and emergent narrative gameplay.

## Primary development goal

Deliver a reliable first playable vertical slice of the simulation that demonstrates the complete core loop:

1. A player submits a free-form thought or attempted action.
2. The system interprets it into a structured action proposal.
3. The simulation arbiter validates and resolves the proposal.
4. Canonical world state, simulation time, outcomes, and events are updated atomically.
5. NPCs and scheduled activities can act through the same authority boundary.
6. Each character receives only the information they are entitled to perceive.
7. The player receives a narrative presentation of confirmed, perceptible consequences.
8. The world persists across restart and remains inspectable through development tooling.

The first scenario should be small but meaningful: one player, three connected locations, one rule-driven NPC, one LLM-assisted NPC, asymmetrical information, a scheduled environmental event, an optional objective, basic interactions, one skill check, and visible progression.

## Strategic principles

- Canonical world state must never be created or modified directly by an LLM.
- The simulation arbiter is the sole authority for state transitions.
- Generated text is presentation or proposal evidence, never canonical truth.
- NPC decision context must be bounded, explicit, and inspectable.
- Simulation time advances through accepted consequential actions or explicit waiting, not wall-clock time.
- Persistence must preserve current state, causal events, and useful execution traces.
- The initial implementation should favor simple, deterministic, testable mechanisms over speculative infrastructure.
- The system should remain open-ended rather than becoming a fixed plot or command-menu game.
- Combat, GraphRAG, multiple worlds, real-time progression, rich belief revision, and generated game packages should remain deferred until the core loop is validated.

## Planning-agent objective

Create an implementation roadmap that takes the repository from its current deterministic kernel and persistence/application foundation to the first validated playable vertical slice.

For each proposed task, define:

- the user-visible behavior;
- the owning architectural boundary;
- authoritative versus derived data;
- inputs, outputs, and failure behavior;
- required requirements or decisions;
- acceptance criteria;
- tests and verification evidence;
- permitted governance-document changes;
- dependencies and stop conditions.

Prioritize the smallest coherent vertical slice that proves the architecture end to end. Do not expand scope into deferred systems unless a concrete requirement demonstrates that they are necessary for the first playable experience.
