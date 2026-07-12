# llm_system

An experimental persistent simulation in which a human player and autonomous NPCs perceive limited information, act through explicit rules, remember consequences, and interact through an LLM-assisted narrative interface.

The project is designed as a practical laboratory for information architecture, context engineering, agentic systems, and local LLM-assisted programming.

## Development setup

Prerequisites: Python 3.12 and [uv](https://docs.astral.sh/uv/).

Create the locked development environment:

```bash
make install
```

Use the Make interface for local verification:

```bash
make test
make format
make format-check
make lint
make mypy
make check
```

`make check` verifies formatting, linting, static types, and tests. It does not require any local model or service to be running.

## Game-package manifests

Versioned authored packages live outside Python code:

```text
game_packages/
  rules/<package-id>/<package-version>/manifest.yaml
  scenarios/<package-id>/<package-version>/manifest.yaml
```

Use `llm_system.game_packages.load_package_manifest()` to safely load the strict,
immutable rule or scenario manifest. It validates package identity against the
directory and verifies that the one YAML entrypoint remains a regular file inside
the package. Entrypoint content parsing and scenario dependency resolution are not
implemented yet.

## Scenario-pack definitions

`ScenarioPackDefinition` is the strict immutable content-schema-version-1 root
for scenario-pack entrypoints. It has exactly two explicit aggregate sections:
`spatial_graph` with authored `locations` and `connections`, and
`entity_collection` with authored `entities`. Empty aggregates are structurally
valid; they do not establish a playable scenario.

This contract does not load YAML entrypoints or perform relational validation.
Connection endpoints, entity placements, archetype and policy references,
uniqueness, graph invariants, and player-count requirements remain deferred to
semantic validation. It also does not define events, director hooks, objectives,
or mechanics.

## Rule-pack definitions

`RulePackDefinition` is the strict immutable content-schema-version-1 root for
rule-pack entrypoints. It contains authored-order catalogs of
`ObjectArchetypeDefinition`, `CharacterArchetypeDefinition`, and
`DecisionPolicyDefinition`. Archetypes currently declare only a stable ID and a
non-blank name; decision policies additionally declare their `rule`, `llm`, or
`hybrid` type.

These definitions are reference catalogs, not executable mechanics. Content
loading, duplicate-ID validation, scenario-reference resolution, policy
implementation lookup, policy execution, and mechanics such as actions,
abilities, effects, or settings remain outside this initial schema.

## Spatial definitions

`LocationDefinition` models an authored location node and
`ConnectionDefinition` models one authored directed edge. Reverse travel needs a
separate connection definition. Each connection has an explicit positive
integer-second `base_traversal_seconds` duration.

`SpatialGraphDefinition` stores authored location and connection order as
immutable collections. These package definitions describe stable topology only;
mutable availability, conditions, visibility, and other runtime state belong to
later state models. Spatial graph validation and scenario-content loading are not
implemented yet.

## Entity definitions

`EntityDefinition` is a strict immutable union of `ObjectDefinition`,
`PlayerCharacterDefinition`, and `NpcCharacterDefinition`. Objects reference an
object archetype and have one initial placement: either a location or a
possessing character, never both. Characters reference character archetypes and
start at a location.

NPC definitions additionally carry an identity summary, authored ordered goals,
an optional initial plan, and a rule, LLM, or hybrid decision-policy reference.
These are package definitions, not mutable runtime state. Duplicate identifiers,
player count, and location, possession, archetype, and policy-reference
resolution remain deferred to scenario validation.

## Documentation

* [High-level design](doc/high_level_design.md)
* [Domain glossary](doc/glossary.md)
* [Requirements](doc/requirements.md)
* [Architecture decisions](doc/decisions.md)
* [Initial scenario](doc/initial_scenario.md)
* [Agent workflow](doc/agent_workflow.md)
* [Roadmap](doc/roadmap.md)
* [Task template](doc/tasks/TASK_TEMPLATE.md)
* [Postponed ideas](doc/ideas.md)

## Local LLM setup: 
* QDRANT at http://localhost:6333 (in case we need RAG)
* EMBEDDINGS Model(v5-small-retrieval-Q8_0.gguf) at http://127.0.0.1:12346 (llama server)
* LLM_MODEL gemma-4-12b at http://127.0.0.1:12345 (another llama server)

## Fastapi and Streamlit chat example
* See /an/git/llmops/
* /home/lexa/an/git/llmops/src/llmops/use_cases/cognitive_map.py
