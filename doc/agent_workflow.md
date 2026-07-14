# Agent Workflow

## Purpose

Use agents without turning one long conversation into the project's source of truth. Durable decisions live in repository artifacts. Each delegated agent receives the smallest sufficient context for one bounded task and returns inspectable evidence.

This workflow applies to subagents in one Codex task, agents in separate chats, and developers using Codex against the same repository.

## Information hierarchy

Do not automatically read/preload artifacts.
Use each artifact for one kind of information:

| Artifact | Purpose |
| --- | --- |
| `AGENTS.md` | Compact repository-wide rules and work-mode router |
| `doc/agent_roles/` | Detailed rules selected for one active responsibility |
| `README.md` | Human landing page for purpose, status, setup, and navigation |
| `doc/domain_guide.md` | Non-normative human orientation to stable domain relationships |
| `doc/glossary.md` | Canonical domain vocabulary |
| `doc/requirements.md` | Accepted observable behavior and constraints |
| `doc/decisions.md` | Accepted architectural choices and rationale |
| `doc/high_level_design.md` | Consolidated architecture and information flows |
| `doc/initial_scenario.md` | Accepted initial playable content |
| `doc/ideas.md` | Postponed possibilities, not approved scope |
| `doc/roadmap.md` | Milestone priority and outcomes, technical dependency order, task readiness, and factual delivery results |
| `doc/tasks/TASK-*.md` | Temporary contracts and handoff records for active work; removed after integration |
| `doc/reviews/` | Independent evidence and recommendations, subject to integrator disposition |
| `doc/codex-task-state.md` | Compact continuation state for the architect or integrator chat |
| Chat history | Temporary discussion only; never the sole source of a requirement |

If conversation and repository artifacts disagree, stop and resolve the discrepancy before delegation.

## Codex customization layers

Use the smallest mechanism matching the scope:

The current product references are [Codex customization](https://learn.chatgpt.com/docs/customization/overview) and [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents). Treat product-specific paths and configuration as version-sensitive and recheck those references before introducing new custom-agent configuration.

### `AGENTS.md`

Use for durable repository conventions, safety boundaries, and routing to one role guide. Keep it compact. Put responsibility-specific planning, implementation, or review procedure in `doc/agent_roles/`, not in the root file.

### Role guide

Use one role guide for the active responsibility. The root `AGENTS.md` routes product direction and delivery-flow stewardship to the scrum-master guide, technical planning and integration to the architect guide, implementation and content work to the implementer guide, and independent evaluation to the reviewer guide. A Ready task names its guide explicitly.

Do not preload all role guides. If work changes responsibility materially, complete or hand off the current responsibility before selecting another guide. A role guide defines procedure; it does not supply task-specific domain context.

### Task brief

Use for one bounded outcome. A task brief contains the context manifest, scope, acceptance criteria, and handoff format. Most specialization should begin here.

### Custom agent

Use `.codex/agents/*.toml` only when the same role repeatedly benefits from stable model, reasoning, sandbox, tool, or behavioral settings. Prefer read-only custom agents for exploration and review. Do not create a custom agent merely to give one task a name.

Current project custom agents:

| Agent | Use |
| --- | --- |
| `experimenter` | Ready evidence and preflight tasks that authorize a report file |
| `implementer` | Ready implementation, coding, and testing tasks with task-authorized writes |
| `reviewer` | Ready independent review, audit, and bounded evidence tasks with task-authorized report writes |

The custom agent supplies role and runtime configuration, not task context. It must still receive a Ready task brief.
Use `implementer` for Ready implementation or scenario-authoring tasks unless a task brief has a reason to specify `Default` or another named custom agent.
Use `reviewer` for Ready independent review or audit tasks unless a task brief has a reason to specify `Default` or another named custom agent.

### Skill

Use a repo-local `.agents/skills/<skill-name>/SKILL.md` when a repeatable project workflow has stable triggers and procedures. Skills may add scripts, references, or assets through progressive disclosure. Do not use a skill to carry one task's changing context or duplicate repository documentation.

Create a skill only when at least one of these is true:

* the procedure has been executed successfully more than once;
* agents repeatedly need the same non-obvious sequence or validation steps;
* a deterministic helper script would replace repeated generated code; or
* a stable package or scenario-authoring workflow has emerged.

### MCP or connector

Use when work requires live external systems or private shared data. It is a capability boundary, not a substitute for task scope.

## Roles

Roles describe responsibility. They do not require custom-agent files initially.

### Scrum master

Detailed procedure: [`agent_roles/scrum_master.md`](agent_roles/scrum_master.md).

* Facilitates alignment between the stakeholder, `doc/goal.md`, and the roadmap.
* Maintains milestone outcomes, priority, current focus, feedback disposition,
  and delivery-flow improvements with stakeholder authority.
* Makes blockers visible, routes them to an accountable owner, and drives an
  explicit next action without taking over another role's decisions.
* Gives the architect one bounded prioritized outcome and adapts from returned
  feasibility and integrated-result evidence.

### Architect and integrator

Detailed procedure: [`agent_roles/architect.md`](agent_roles/architect.md).

* Maintains requirements, decisions, glossary, high-level design, technical
  roadmap decomposition, dependencies, readiness, and factual task outcomes.
* Resolves ambiguity before implementation is delegated.
* Writes or approves task briefs.
* Integrates reviewed work and handles cross-task consequences.
* Uses a stronger model or higher reasoning effort for architecture-sensitive work.

### Explorer or experimenter

* Gathers evidence without changing application behavior.
* Traces real code paths, APIs, model behavior, or environment constraints.
* Produces a concise evidence artifact for a later implementation task.
* Uses read-only access unless the task explicitly authorizes one report file.

### Implementer

Detailed procedure: [`agent_roles/implementer.md`](agent_roles/implementer.md).

* Implements one ready task through TDD.
* Preserves named contracts and stays inside explicit scope.
* Does not change governance artifacts unless the task authorizes it.
* Reports a design gap instead of inventing architecture.

### Reviewer

Detailed procedure: [`agent_roles/reviewer.md`](agent_roles/reviewer.md).

* Reviews a task against its brief, diff, requirements, decisions, and tests.
* Prioritizes correctness, authority boundaries, information leaks, regressions, and missing tests.
* Remains read-only and independent from the implementation approach where possible.

## Product-to-delivery loop

The stakeholder retains product authority. The scrum master facilitates product
direction and maintains accepted milestone priority; the architect owns the
technical path from one prioritized outcome to Ready tasks and integrated
evidence.

1. The stakeholder and scrum master compare feedback and current evidence with
   `doc/goal.md`.
2. The scrum master records an accepted current milestone outcome, priority,
   constraints, and exclusions in `doc/roadmap.md`.
3. The architect tests feasibility and returns hidden dependencies, scope risks,
   or strategic questions rather than silently changing the outcome.
4. Once technically unambiguous, the architect prepares and delegates
   just-in-time Ready tasks.
5. Implementers, reviewers, and the integrator produce and verify inspectable
   outcome evidence.
6. The scrum master brings that evidence and resulting feedback back to the
   stakeholder and adapts the roadmap.

Hand off one current outcome rather than pushing the entire roadmap as execution
context. If work changes from product stewardship to technical planning or back,
finish or explicitly hand off the active responsibility before selecting the
other guide.

## Task lifecycle

Use these statuses:

1. **Planned**: Roadmap item exists, but unresolved dependencies or contracts prevent delegation.
2. **Ready**: Task brief is complete and contains no material design ambiguity.
3. **In progress**: One agent owns the task in one branch or worktree.
4. **Review**: Implementation and task-local verification are complete.
5. **Blocked**: A named external condition or unresolved design gap prevents progress.
6. **Done**: Review findings are resolved, the integrator has accepted the result,
   and its task brief has been deleted from `doc/tasks/`.

Only the architect or integrator promotes a task to Ready or Done. The scrum
master may propose or maintain milestone priority and current focus but does not
change task readiness or accept implementation. An execution agent may move a
Ready task to In progress and then to Review or Blocked; it must never mark its
own work Done.

Task briefs are working artifacts, not permanent project history. Before deleting
an accepted brief, the integrator must record any durable outcome, deviation, or
follow-up in its owning canonical artifact. The roadmap records the completed
task identifier and outcome without linking to a task file; Git history provides
the detailed audit trail.

Delete every completed task brief from `doc/tasks/` in the same integration
commit that marks it Done. Do not archive, retain, or relabel completed briefs
there. Keep only `TASK_TEMPLATE.md` and briefs that are Planned, Ready, In
progress, Review, or Blocked. Delete explicitly cancelled briefs as well, after
recording any durable cancellation rationale or follow-up in the owning canonical
artifact.

## Writing a task brief

Start from [`tasks/TASK_TEMPLATE.md`](tasks/TASK_TEMPLATE.md). A ready task must contain:

* one outcome stated in behavioral terms;
* stable requirement IDs and decision references;
* exactly one role guide matching the assigned responsibility;
* a context manifest listing exact files and sections;
* a context budget showing why each documentation source is required;
* fixed assumptions that the agent must not revisit;
* explicit in-scope and out-of-scope boundaries;
* expected contracts and likely files;
* acceptance criteria that can be verified;
* required test and quality commands;
* permissions for governance-document changes; and
* the required handoff report.

Reference stable requirements and decisions instead of copying their full text into fixed assumptions or acceptance criteria. Restate only the task-specific consequence needed to remove ambiguity.

Do not include brainstorm history, rejected alternatives already captured in decisions, unrelated future ideas, the parent agent's hidden reasoning, or general orientation material that does not affect execution.

## Context routing

The task brief is the context router.

### Context budget

Use a soft limit of 8,000 words for the task brief plus documentation that must be read before task-local source exploration. This is a diagnostic threshold, not a reason to omit necessary authority. If the expected context exceeds it, justify each broad source and consider narrowing the task.

The budget excludes source and tests discovered while tracing the named implementation path. It includes the task brief, glossary extracts, requirement ranges, decisions, design sections, scenario extracts, and other pre-code documents. Approximate word counts are sufficient; exact tokenizer-specific accounting is unnecessary.

### Always read

* repository `AGENTS.md`;
* the role guide named by the task brief;
* the assigned task brief; and
* the glossary entries named by the task brief.

### Read only when listed

* exact requirement ID ranges;
* named decision entries;
* specific high-level-design sections;
* the initial scenario;
* package schemas or code contracts; and
* relevant source and test files discovered while tracing the real path.

Read named sections and requirement IDs, not the entire containing document. Use heading or identifier searches to locate those extracts before opening surrounding lines.

Do not load README, the domain guide, roadmap, ideas, architect continuation state, reviews, completed task briefs, or planning-chat history for implementation unless the task explicitly depends on that artifact's responsibility. Do not read all project documents merely because they exist.

README and the domain guide orient humans; they are not substitutes for requirements, decisions, or design. A task that changes public setup or onboarding may authorize README work without making the rest of README a behavioral contract.

If no task brief exists for non-trivial delegated work, create or request one before implementation.

## Execution rules

1. Confirm the task status is Ready.
2. Read the context manifest before broad repository exploration.
3. Restate only assumptions that affect behavior, public interfaces, data, security, or verification.
4. Inspect the actual code path and working tree.
5. Write a failing behavioral test before implementation logic.
6. Make the smallest change satisfying the acceptance criteria.
7. Run task-local checks, then the required repository checks.
8. Update only task-authorized artifacts.
9. Fill in the handoff report without rewriting the original task contract.
10. Record the documentation extracts and initially named source or test files actually used; do not enumerate every file reached by normal transitive code tracing.

### Design gaps

A design gap exists when implementation requires a behavior, public contract, data meaning, authority boundary, or dependency choice not fixed by the task's accepted context.

When a design gap appears:

* stop the affected implementation path;
* describe the concrete choice and why it matters;
* list the smallest credible alternatives;
* mark the task Blocked if no safe work remains; and
* return the choice to the architect instead of updating requirements or decisions independently.

## Branches, worktrees, and parallelism

Use one branch or worktree per write-capable task. Use a name such as `task/TASK-003-location-graph`.

Parallelize primarily:

* read-only exploration;
* independent experiments;
* review categories;
* test-gap analysis; and
* content authoring after schemas stabilize.

Avoid parallel agents editing the same files or adjacent contracts. Parallel write-heavy work creates merge conflicts and hidden design divergence even when Git can merge the text.

The scrum master controls accepted milestone priority with the stakeholder. The
integrator controls merge order according to the roadmap's technical
dependencies and reports any resulting priority conflict rather than overriding
either boundary silently.

## Review and integration

Independent review is selective rather than automatic for every implementation task. Use it for milestone gates, authority or persistence boundaries, security or privacy changes, public compatibility, cross-cutting refactors, disputed results, and reviews explicitly requested by the user or roadmap. The integrator may review smaller bounded changes directly when that is proportionate to risk.

When independent review is required, create a separate Ready review task that names `agent_roles/reviewer.md` and the `reviewer` agent. Do not reassign the implementation task brief to the reviewer: its one named role guide remains authoritative for the implementation responsibility. The review task references the implementation task and routes the exact diff, contracts, verification evidence, and context-used record needed for independent reconstruction.

Give the reviewer:

* the task brief;
* the implementation diff;
* linked requirements and decisions;
* verification results; and
* the execution agent's concise context-used record.

Do not preload the reviewer with the implementer's justification beyond the concise handoff report. Independent reconstruction reduces anchoring.

The integrator:

1. resolves review findings;
2. runs the full available verification suite;
3. checks compatibility with already integrated tasks;
4. records task status and material deviations;
5. updates architecture artifacts only for accepted changes; and
6. deletes the accepted task brief from `doc/tasks/` and removes any durable
   links to it; and
7. performs semantic version bumps at meaningful implementation milestones.

## Handoff between chats

Start a fresh implementation chat with a short instruction:

```text
This is delegation only, not integration.

Delegate <READY_TASK_PATH> to a fresh subagent using the Agent configuration
specified by the task brief. `Default` means no custom-agent profile.
Do not pass prior chat history.

The task brief is the context router. Read only its exact pre-code selections,
including its one named role guide, then trace task-local source and tests. Do
not preload other role guides, README, the domain guide, roadmap, ideas, reviews,
completed tasks, or architect continuation state unless the task explicitly
names them.

The execution agent may set the task to In progress, then Review or Blocked.
Neither the execution agent nor this parent task may mark it Done, review or
accept the result, update the roadmap or governance documents, stage files,
or commit changes.

Wait for the execution agent, then return its handoff and changed-file list
without adding an acceptance judgment. Integration will happen separately.
```

The task file, repository state, and resulting diff carry the context. The planning transcript does not.

## Evolving specialization

Begin with built-in default, worker, and explorer capabilities plus task briefs. After real tasks reveal repetition:

1. identify instructions repeated across successful tasks;
2. decide whether they are repository rules, a role configuration, or a workflow skill;
3. create the smallest corresponding artifact;
4. validate it on a fresh task without leaking the intended answer; and
5. revise or remove it when it causes unnecessary context or rigidity.

Likely future skills include game-package authoring, simulation-boundary review, and vertical-slice verification. They should not be created before their schemas and procedures stabilize.
