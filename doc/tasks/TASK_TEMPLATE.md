# TASK-NNN: Short outcome title

**Status:** Planned | Ready | In progress | Review | Blocked | Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Explorer | Experimenter | Implementer | Scenario author | Reviewer

**Agent:** Named custom agent or `Default`

**Depends on:** Task IDs or `None`

## Objective

State one observable outcome. Explain why it is needed in no more than two short paragraphs.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* `doc/glossary.md`: named entries
* `doc/requirements.md`: exact requirement IDs
* `doc/decisions.md`: exact decision titles
* `doc/high_level_design.md`: exact sections
* other task-specific artifacts

Do not read unrelated planning or idea documents.

## Fixed assumptions

List accepted facts the agent must not redesign.

## In scope

* Included behavior or artifact.

## Out of scope

* Explicitly excluded adjacent work.
* Governance-document changes unless specifically authorized.

## Expected contracts and files

List interfaces that must remain stable and files likely to be created or changed. This is routing guidance, not permission to ignore the actual code path.

## Acceptance criteria

1. State externally verifiable behavior.
2. Reference requirement IDs where applicable.
3. Include relevant failure behavior.

## Required verification

* Failing behavioral test written before implementation logic, when code changes are involved.
* Task-specific test commands.
* `make format`
* `make lint`
* `make mypy`
* `git diff --check`

If a command is unavailable because scaffolding does not yet exist, record that fact rather than inventing a replacement silently.

## Stop conditions

Stop and report a design gap when the task requires an unaccepted behavior, public contract, data meaning, dependency, or authority change.

## Handoff report

Fill this section without rewriting the task contract.

**Result:** Pending

**Changed files:** Pending

**Verification:** Pending

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
