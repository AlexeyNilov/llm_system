# Codex task state

## Current objective

Execute and integrate TASK-041: the bounded NPC decision context and rule-driven Greybridge caretaker policy.

## Verified baseline

* TASK-040 is independently reviewed and accepted at project version `0.38.0`; M4 is complete.
* The player page communicates only through FastAPI using a five-second bounded HTTP client and validates every recognized response against existing API models.
* It exposes all seven typed proposal forms, deterministic lifecycle/result presentation, confirmation-gated development reset, and session-only committed-turn history.
* HTTP/application failures remain distinct from completed domain outcomes and do not append or clear history incorrectly. Owned HTTP resources close on every rerun path.
* The page starts no API process and performs no package, SQLite, application-service, simulation-resolution, LLM, narration, or inspection work.
* Parent verification passes: 57 focused tests, `make check` with 406 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

No known blocker. Executing scheduled NPC activity through the coordinator remains a later M5 increment that needs this policy contract and an actor runtime first. Free-form player interpretation, local model integration, narration, and the memory-free courier remain separate M5 tasks.

## Exact next action

Delegate the Ready TASK-041 to a fresh `implementer`, then independently review its diff and verification against the bounded context, pure proposal-only policy, deterministic priority sequence, and 60-second fallback.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/tasks/TASK-041-rule-driven-caretaker-policy.md`
4. TASK-041's exact context manifest
5. The implementation diff and handoff evidence
