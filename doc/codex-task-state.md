# Codex task state

## Current objective

Integrate TASK-039: a minimal FastAPI lifecycle and trusted structured player-turn boundary over the accepted M4 application services.

## Verified baseline

* TASK-038 is independently reviewed and accepted at project version `0.36.0`.
* Initial-world construction deterministically derives and validates complete time-zero overlays from validated packages.
* Creation explicitly commits revision 0; resume loads only exact recorded package versions and performs no authoritative write.
* Development reset requires an existing world and atomically replaces the complete world, event, and trace timeline.
* Parent verification passes: 14 focused tests, `make check` with 349 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

No blocker. Scheduled-activity execution, player text interpretation, narration, inspection, production authentication, deployment configuration, and Streamlit remain explicitly deferred.

## Exact next action

Commit the Ready TASK-039 planning artifacts, delegate the task to a fresh configured implementer, independently inspect the implementation and verification, resolve findings, mark Done, update the M4 roadmap and continuation state, and commit accepted work.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M4
4. `doc/high_level_design.md`: FastAPI application API and persistence flow
5. API, lifecycle, action-submission, and failure requirements and decisions
6. `src/llm_system/application/`, `src/llm_system/persistence/`, and `pyproject.toml`
