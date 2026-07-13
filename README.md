# llm_system

`llm_system` is an experimental persistent LitRPG-style simulation. A human player and autonomous NPCs perceive limited information, propose actions, and experience consequences through an LLM-assisted narrative interface.

The project is also a laboratory for information architecture, context engineering, deterministic agent boundaries, and local LLM-assisted programming.

> The simulation owns truth. LLMs interpret truth, propose actions, and narrate outcomes.

## Current status

The deterministic Python kernel is implemented and reviewed. It can:

* load and semantically validate versioned YAML rule and scenario packages;
* validate immutable runtime world snapshots against those packages;
* authorize typed player and NPC action submissions;
* resolve Observe, Move, Speak, Take, Use, and Wait without an LLM;
* commit typed state changes into replacement world snapshots;
* produce typed canonical events and selected perception projections;
* persist one revision-checked world, its scheduled queue, and ordered canonical
  events atomically in SQLite;
* coordinate a trusted actor action through authorization, resolution,
  commitment, perception, and one atomic world/event/trace transaction;
* create the singleton world from validated package-authored initial state,
  resume it from exact recorded package versions, and reset its complete
  development timeline atomically;
* expose lifecycle operations and typed structured player turns through a
  minimal FastAPI boundary with server-owned identities and provenance;
* exercise that boundary through a deterministic Streamlit player page with
  typed action controls and session-only committed-result history;
* migrate SQLite V1 worlds directly to V2 append-only completed-step trace
  history;
* partition scheduled activities deterministically; and
* validate caller-injected recorded integer draws.

Help resolution, scheduled-activity execution, player-text interpretation, NPC
execution, the System director, narration, and the complete Greybridge scenario
remain later work. See the [roadmap](doc/roadmap.md) for current delivery order.

## Development setup

Prerequisites:

* Python 3.12
* [uv](https://docs.astral.sh/uv/)

Create the locked development environment:

```bash
make install
```

Run the complete local quality gate:

```bash
make check
```

Individual targets are also available:

```bash
make test
make format
make format-check
make lint
make mypy
```

The deterministic test suite requires no LLM, embeddings service, Qdrant instance, FastAPI process, or Streamlit process.

## Deterministic player page

Start the FastAPI application and structured player page together:

```bash
make player-page
```

The target stores the development world in `.run/world.sqlite3` and stops the
FastAPI child process when Streamlit exits. To use an API at another address,
set `LLM_SYSTEM_API_URL` before running the target; in that case, stop the
separately launched API yourself.

## Architecture at a glance

The simulation separates creative interpretation from canonical authority:

```text
player or NPC policy
    -> untrusted action proposal
    -> trusted application submission
    -> authorization
    -> deterministic operation resolution
    -> typed outcome, state changes, and events
    -> arbiter commitment
    -> replacement canonical world
    -> actor-specific perception
    -> narration and interface presentation
```

Versioned game packages define stable rules and scenario content. Runtime state contains only changing facts linked to those definitions by stable identifiers. SQLite persists already validated domain results and completed actor-action traces; it does not interpret game rules or become a second simulation authority.

Read the [domain guide](doc/domain_guide.md) for the conceptual model and the [high-level design](doc/high_level_design.md) for component and information-flow boundaries.

## Game packages

Authored packages live outside Python code:

```text
game_packages/
  rules/<package-id>/<package-version>/
  scenarios/<package-id>/<package-version>/
```

The repository includes compatible Greybridge `0.1.0` packages and the `0.2.0` package pair containing the first executable authored Use mechanic.

Load and validate a pair through the public package boundary:

```python
from pathlib import Path

from llm_system.game_packages import load_game_package, validate_game_packages

root = Path("game_packages")
rules = load_game_package(root / "rules/greybridge-rules/0.2.0")
scenario = load_game_package(root / "scenarios/storm-at-greybridge/0.2.0")
packages = validate_game_packages(rules, scenario)
```

Package validation establishes structural and semantic consistency. It does not prove runtime-world readiness, implemented mechanic availability, persistence compatibility, or scenario playability.

## Repository map

| Path | Purpose |
| --- | --- |
| `src/llm_system/application/` | Atomic application coordination across simulation and persistence boundaries |
| `src/llm_system/api.py` | Minimal FastAPI lifecycle and structured player-turn boundary |
| `src/llm_system/player_page.py` | Deterministic Streamlit player interface |
| `src/llm_system/game_packages/` | Authored package models, loading, and semantic validation |
| `src/llm_system/simulation/` | Runtime state, authorization, resolution, commitment, scheduling, randomness, and perception |
| `src/llm_system/persistence/` | SQLite records, repositories, schema bootstrap, and unit of work |
| `game_packages/` | Versioned Greybridge rule and scenario content |
| `tests/` | Behavioral evidence for project-owned contracts |
| `doc/` | Domain, architecture, requirements, decisions, workflow, and planning artifacts |

## Documentation map

Each document has one primary responsibility:

| Need | Authoritative source |
| --- | --- |
| Learn the domain model | [Domain guide](doc/domain_guide.md) |
| Use canonical terminology | [Glossary](doc/glossary.md) |
| Find accepted behavior and constraints | [Requirements](doc/requirements.md) |
| Understand accepted choices and rationale | [Decisions](doc/decisions.md) |
| Understand components and information flow | [High-level design](doc/high_level_design.md) |
| Understand Greybridge content | [Initial scenario](doc/initial_scenario.md) |
| See delivery order and current milestone | [Roadmap](doc/roadmap.md) |
| See postponed possibilities | [Ideas](doc/ideas.md) |
| Delegate or review work | [Agent workflow](doc/agent_workflow.md) |

The domain guide and README are orientation surfaces, not competing specifications. When wording conflicts, the glossary, requirements, accepted decisions, and executable code/tests are the relevant authoritative evidence.

## Local LLMs

Local model integration is intentionally outside the deterministic kernel. The planned gateway will use OpenAI-compatible local endpoints and strict structured outputs for functional roles. Current unit and integration checks do not contact those endpoints.

Model-specific setup belongs in local configuration and infrastructure repositories rather than machine-specific paths in this README.
