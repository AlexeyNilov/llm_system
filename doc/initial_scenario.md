# Initial Scenario: Storm at Greybridge

**Status:** Accepted concept for the initial vertical slice. Exact names, prose, timing, and numerical balance remain package-authoring details.

## Purpose

Storm at Greybridge is a compact non-combat situation designed to validate the complete initial architecture. It creates time pressure, asymmetric perception, conflicting priorities, object interaction, uncertain checks, optional System director intervention, and several valid outcomes across three locations.

The scenario must remain playable without episodic memory, mutable beliefs, prior chat history, or Qdrant.

## Premise

Floodwater is rising around a remote waystation and its aging bridge. An injured courier carries medicine needed beyond the far bank. The bridge caretaker can currently see structural damage that is not visible from the waystation. A coming surge may make the crossing dangerous or close the route entirely.

The player is not assigned a mandatory solution. They may help the courier, move the medicine separately, inspect or reinforce the bridge, cross alone, wait, or abandon the situation.

## Location graph

```mermaid
flowchart LR
    Waystation[Greybridge waystation]
    Bridge[Greybridge span]
    FarBank[Far bank]

    Waystation <-->|short approach| Bridge
    Bridge <-->|conditional crossing| FarBank
```

### Greybridge waystation

The player and courier begin here. Useful reinforcement materials and basic supplies are present as structured objects. The player can perceive the storm and the courier's visible condition but cannot initially inspect the damaged bridge support.

### Greybridge span

The caretaker begins here and can perceive the structural damage. The location exposes bridge condition, rising water, and reinforcement opportunities to characters who can currently observe them.

### Far bank

Reaching this location counts as crossing the threatened route. The scenario does not initially simulate the distant settlement; the courier, medicine, and player can independently end up here.

Connections carry explicit traversal duration, requirements, and current availability. Exact durations and Fieldcraft thresholds belong to the rule and scenario packages.

## Actors

### Player character

The human owns sensemaking and intent. The application supplies only the player's current perception and interprets explicitly entered thoughts, speech, and attempted actions.

### Injured courier

**Decision policy:** LLM-assisted.

**Initial location:** Greybridge waystation.

**Current goals:** Get the medicine across the bridge; avoid worsening the injury.

**Initial plan:** Attempt to find help and cross before the route closes.

The courier receives identity, current goals, current plan, and current perception. The courier does not receive prior conversation turns as hidden memory, and the scenario cannot depend on conversational recall across turns.

### Bridge caretaker

**Decision policy:** Rule-driven.

**Initial location:** Greybridge span.

**Behavior priorities:** Protect people from an unsafe crossing; preserve the bridge when feasible; protect critical supplies; move to safety when reinforcement is no longer viable.

The caretaker reacts from current perception and a limited action repertoire. Individual behavior is expressed as priorities and conditions rather than simulated low intelligence.

## Initial information boundaries

| Information | Canonical | Player | Courier | Caretaker |
| --- | --- | --- | --- | --- |
| A storm and rising water threaten the area | Yes | Observed | Observed | Observed |
| The courier is visibly injured | Yes | Observed | Observed | Not initially observed |
| The courier possesses medicine | Yes | Observed according to package state | Observed | Not initially observed |
| A bridge support is structurally damaged | Yes | Not initially observed | Not initially observed | Observed |
| A flood surge is scheduled | Yes | Not directly known | Not directly known | Not directly known as a schedule |

The scheduled surge is canonical future activity, not a belief held by a character. Characters may perceive warning signs without receiving the event time.

## Time pressure and System director intervention

The scenario package schedules one flood surge at an explicit simulation time. Its resolved effect depends on current bridge state: an untouched bridge may become impassable, while successful reinforcement may preserve or extend crossing availability according to the rule pack.

A rate-limited world-creation System director hook receives curated scenario context and may submit an action proposal for an optional objective: help the courier or medicine cross before the route closes. The simulation arbiter validates the proposal, and the System interface presents an accepted objective. Declining or opposing it remains valid play.

## Supported interactions

The scenario exercises the initial supported actions:

* **Observe:** inspect the current location, courier, medicine, water, bridge, or materials when perceptible.
* **Move:** traverse an available connection at its simulation-time cost.
* **Speak:** address a character currently able to hear the player.
* **Take:** attempt to acquire medicine, materials, or another accessible object subject to possession rules.
* **Use:** apply reinforcement materials or another supported object operation.
* **Help:** assist the courier or caretaker through a supported action.
* **Wait:** advance simulation time and allow scheduled activities to resolve.

Unsupported free-form attempts produce clarification or rejection rather than invented mechanics.

## Fieldcraft and progression

Fieldcraft is the initial lightweight skill. The rule pack may use it to inspect structural damage, choose reinforcement, assist a difficult crossing, or recognize environmental risk.

Checks use arbiter-controlled recorded randomness only where the rule pack explicitly requests uncertainty. At least one meaningful successful use produces an arbiter-confirmed Fieldcraft progression event and a player-visible System notification.

Exact check formulas, thresholds, progression conditions, and notification text remain package-authoring details.

## Valid outcome branches

The scenario must support materially different persistent states, including:

* the courier and medicine reach the far bank;
* the medicine reaches the far bank without the courier;
* the player crosses alone;
* the bridge is reinforced and remains available;
* the route closes before anyone crosses; or
* the player ignores or leaves the immediate problem unresolved.

These are examples, not a scripted branch tree. The world continues after a local success or failure unless a loaded rule explicitly ends it.

## Architecture coverage

| Concern | Scenario evidence |
| --- | --- |
| Canonical truth | Bridge condition, locations, possessions, flood state |
| Location graph | Three nodes and conditional connections |
| Asymmetric perception | Only the caretaker initially observes structural damage |
| Rule-driven NPC | Caretaker priorities and limited action set |
| LLM-assisted NPC | Courier selects a structured action proposal from bounded context |
| Action-driven time | Movement, helping, reinforcement, and waiting have durations |
| Deterministic scheduling | Flood event, NPC activity, and System director hook ordering |
| Seeded uncertainty | Fieldcraft checks with recorded arbiter draws |
| System director | Rate-limited optional-objective proposal |
| System interface | Confirmed objective and Fieldcraft progression notifications |
| Persistence | Restart resumes exact time, state, events, and scheduled activity |
| Safe LLM boundary | Invalid courier or System director output repairs once, then fails safely |

## Explicit exclusions

The initial scenario does not require:

* combat, health depletion, or death rules;
* episodic memory or Qdrant;
* mutable belief state or belief revision;
* prior chat history in NPC context;
* real-time or offline progression;
* multiple worlds or players; or
* a single canonical winning path.
