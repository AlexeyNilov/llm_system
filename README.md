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
