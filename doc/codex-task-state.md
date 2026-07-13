# Codex task state

## Current objective

Plan the first actionable M5 increment: the rule-driven caretaker decision policy behind the existing proposal boundary.

## Verified baseline

* TASK-040 is independently reviewed and accepted at project version `0.38.0`; M4 is complete.
* The player page communicates only through FastAPI using a five-second bounded HTTP client and validates every recognized response against existing API models.
* It exposes all seven typed proposal forms, deterministic lifecycle/result presentation, confirmation-gated development reset, and session-only committed-turn history.
* HTTP/application failures remain distinct from completed domain outcomes and do not append or clear history incorrectly. Owned HTTP resources close on every rerun path.
* The page starts no API process and performs no package, SQLite, application-service, simulation-resolution, LLM, narration, or inspection work.
* Parent verification passes: 57 focused tests, `make check` with 406 tests, `uv lock --check`, and `git diff --check`.

## Blockers and unresolved questions

No blocker to planning the rule-driven caretaker policy itself. Executing scheduled NPC activity through the coordinator remains a later M5 increment that needs the policy contract and actor runtime first. Free-form player interpretation, local model integration, narration, and the memory-free courier remain separate M5 tasks.

## Exact next action

Inspect the accepted NPC decision-policy definitions, actor cognition loop, current perception and proposal contracts, and Greybridge caretaker goals. Settle the smallest deterministic policy input/output and safe fallback boundary, prepare TASK-041, commit automatically when Ready, delegate, review, and integrate accepted work.

## Files to re-read before continuing

1. `AGENTS.md`
2. `doc/agent_roles/architect.md`
3. `doc/roadmap.md`: M5
4. `doc/high_level_design.md`: actor runtime, rule-based policy, and actor cognition loop
5. NPC autonomy, policy, perception, action-proposal, and failure requirements and decisions
6. Decision-policy package definitions, actor/perception/action contracts, Greybridge caretaker content, and relevant tests
