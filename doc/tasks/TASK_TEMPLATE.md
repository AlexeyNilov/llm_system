# TASK-NNN: Short outcome title

**Status:** Planned | Ready | In progress | Review | Blocked | Done

Execution agents may set this task to In progress, Review, or Blocked. Only the architect or integrator may set Ready or Done.

**Owner:** Unassigned

**Role:** Explorer | Experimenter | Implementer | Scenario author | Reviewer

**Role guide:** `doc/agent_roles/implementer.md` | `doc/agent_roles/reviewer.md`

Use the implementer guide for implementation or scenario-authoring work. Use the reviewer guide for exploration, experiments, and independent review.

**Agent:** Named custom agent or `Default`

**Depends on:** Task IDs or `None`

## Objective

State one observable outcome. Explain why it is needed in no more than two short paragraphs.

## Context manifest

Read only the following project context before tracing task-local code:

* `AGENTS.md`
* the exact role guide named above
* `doc/glossary.md`: named entries
* `doc/requirements.md`: exact requirement IDs
* `doc/decisions.md`: exact decision titles
* `doc/high_level_design.md`: exact sections
* other task-specific artifacts

Name exact requirement IDs, decision titles, document sections, and initial source or test entrypoints. Do not name an entire canonical document when a bounded extract is sufficient.

Do not read README, the domain guide, roadmap, ideas, reviews, completed task briefs, architect continuation state, or planning-chat history unless this task explicitly depends on that artifact's responsibility.

## Context budget

Use the soft 8,000-word pre-code documentation limit from `doc/agent_workflow.md`.

| Context | Why required | Exact selection | Approximate words |
| --- | --- | --- | ---: |
| Repository rules | Durable execution constraints | `AGENTS.md` | Pending |
| Role guide | Rules for this responsibility | Exact guide named above | Pending |
| Task brief | Execution contract | This file | Pending |
| Canonical documentation | Behavior or authority | Named extracts above | Pending |
| Other pre-code context | Task-specific evidence | Named extracts above | Pending |
| **Total before source exploration** |  |  | **Pending** |

If the expected total exceeds the soft limit, explain why the task should not be narrowed. Do not count source and tests discovered while tracing the named path.

## Fixed assumptions

List only task-specific accepted facts the agent must not redesign. Reference stable project truth rather than copying full requirements or decisions.

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

**Context used:** Pending; list the documentation extracts and initially named source or test files actually consulted. Do not list every transitive implementation file.

**Deviations:** Pending

**Design gaps or follow-ups:** Pending
