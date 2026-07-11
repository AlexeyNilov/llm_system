# TASK-002: Create the Python project scaffold

**Status:** Ready

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Implementer

**Agent:** Default

**Depends on:** None

## Objective

Create a reproducible, installable Python 3.12 project whose package can be imported and whose complete initial quality suite can be run through stable Make targets. This foundation is required before domain schemas and simulation behavior can be delegated safely.

## Context manifest

Read only the following project context before tracing task-local files:

* `AGENTS.md`
* `doc/requirements.md`: `DEV-001` through `DEV-006`
* `doc/decisions.md`: “Standardize the initial Python project foundation”
* `doc/high_level_design.md`: “Testing strategy”
* `README.md`: project overview and current local services

Do not read unrelated planning, scenario, experiment, or idea documents.

## Fixed assumptions

* The supported runtime is Python 3.12.x, expressed as `>=3.12,<3.13`.
* `uv` owns environment creation and dependency locking; `uv.lock` is committed.
* The distribution is named `llm-system`, the import package is `llm_system`, and the initial version is `0.1.0`.
* Hatchling is the build backend and packages code from `src/llm_system`.
* The initial project has no runtime dependencies.
* The development dependency set is limited to `pytest`, `ruff`, and `mypy` unless a concrete scaffold verification failure proves another dependency necessary.
* Normal tests and quality checks must not call any local model, embedding, Qdrant, FastAPI, or Streamlit service.

## In scope

* Add `.python-version`, `pyproject.toml`, the `src/llm_system` package, and a focused package smoke test under `tests/`.
* Generate and commit `uv.lock` from the accepted project metadata.
* Configure pytest, Ruff, and mypy in `pyproject.toml` for Python 3.12 and the `src` layout.
* Add the accepted Make targets: `install`, `test`, `format`, `format-check`, `lint`, `mypy`, and `check`.
* Document the actual setup and verification commands in `README.md` without removing the existing architecture-document or local-service information.
* Update this task's status and handoff report as permitted by `doc/agent_workflow.md`.

## Out of scope

* Domain models, game-package loading, the simulation kernel, persistence, APIs, user interfaces, or LLM integration.
* Pydantic, PyYAML, FastAPI, Streamlit, database helpers, LLM clients, or any other anticipated runtime dependency.
* CI configuration, containerization, publishing configuration, application entry points, or multi-version Python testing.
* Changes to `AGENTS.md`, `doc/requirements.md`, `doc/decisions.md`, `doc/high_level_design.md`, `doc/roadmap.md`, `doc/glossary.md`, `doc/initial_scenario.md`, or `doc/ideas.md`.

## Expected contracts and files

* `.python-version` contains `3.12`.
* `pyproject.toml` declares `llm-system` version `0.1.0`, Python `>=3.12,<3.13`, Hatchling, the `src` package layout, no runtime dependencies, and one development dependency group containing pytest, Ruff, and mypy.
* `src/llm_system/__init__.py` makes `llm_system` importable. Do not invent domain exports.
* `tests/test_package.py` verifies the installed package boundary rather than framework behavior or a trivial internal getter.
* `Makefile` provides the accepted target names. `check` runs non-mutating formatting verification, linting, mypy, and tests; `format` is the only quality target that intentionally rewrites source files.
* `README.md` states the Python and `uv` prerequisites and uses the Make targets as the canonical commands.

## Acceptance criteria

1. Given Python 3.12 and `uv`, `uv sync --locked` reconstructs the declared development environment from committed metadata and `uv.lock` (`DEV-001`, `DEV-002`).
2. After synchronization, the installed `llm_system` package can be imported from the `src` layout and its installed distribution metadata reports version `0.1.0` (`DEV-003`, `DEV-004`).
3. Project metadata contains no runtime dependencies and its development dependency group contains only pytest, Ruff, and mypy (`DEV-004`).
4. Every Make target named by `DEV-005` exists and invokes tools through `uv run` where an environment tool is required.
5. `make check` succeeds without a running external service and performs formatting verification, linting, strict static type checking, and the package test (`DEV-006`).
6. The README setup instructions are sufficient to install and verify the scaffold using the declared Make interface.

## Required verification

* Before adding the package implementation, add the package-boundary test and capture its expected failure because `llm_system` is not importable or installed yet.
* `uv sync --locked`
* `make test`
* `make format`
* `make format-check`
* `make lint`
* `make mypy`
* `make check`
* `git diff --check`

Record the initial failing test and final command results in the handoff. Do not claim TDD solely from the final green state.

## Stop conditions

Stop and report a design gap if the accepted dependency set cannot implement the scaffold, if `uv` or Hatchling cannot represent the fixed package contract, if a supported Python version other than 3.12 becomes necessary, or if verification requires a product behavior or external service outside this task.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
