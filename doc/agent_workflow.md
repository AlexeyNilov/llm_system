# Agent Workflow

## Purpose

Use agents without turning one long conversation into the project's source of truth. Durable decisions live in repository artifacts. Each delegated agent receives the smallest sufficient context for one bounded task and returns inspectable evidence.

This workflow applies to subagents in one Codex task, agents in separate chats, and developers using Codex against the same repository.

## Information hierarchy

Use each artifact for one kind of information:

| Artifact | Purpose |
| --- | --- |
| `AGENTS.md` | Small set of durable rules that apply across the repository |
| `doc/glossary.md` | Canonical domain vocabulary |
| `doc/requirements.md` | Accepted observable behavior and constraints |
| `doc/decisions.md` | Accepted architectural choices and rationale |
| `doc/high_level_design.md` | Consolidated architecture and information flows |
| `doc/initial_scenario.md` | Accepted initial playable content |
| `doc/ideas.md` | Postponed possibilities, not approved scope |
| `doc/roadmap.md` | Dependency order, milestones, and task readiness |
| `doc/tasks/TASK-*.md` | Bounded work contracts and handoff records |
| Chat history | Temporary discussion only; never the sole source of a requirement |

If conversation and repository artifacts disagree, stop and resolve the discrepancy before delegation.

## Codex customization layers

Use the smallest mechanism matching the scope:

The current product references are [Codex customization](https://learn.chatgpt.com/docs/customization/overview) and [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents). Treat product-specific paths and configuration as version-sensitive and recheck those references before introducing new custom-agent configuration.

### `AGENTS.md`

Use for durable repository conventions, safety boundaries, test expectations, and task-routing rules. Keep it compact. Do not copy detailed architecture or task instructions into it.

### Task brief

Use for one bounded outcome. A task brief contains the context manifest, scope, acceptance criteria, and handoff format. Most specialization should begin here.

### Custom agent

Use `.codex/agents/*.toml` only when the same role repeatedly benefits from stable model, reasoning, sandbox, tool, or behavioral settings. Prefer read-only custom agents for exploration and review. Do not create a custom agent merely to give one task a name.

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

### Architect and integrator

* Maintains requirements, decisions, glossary, high-level design, and roadmap.
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

* Implements one ready task through TDD.
* Preserves named contracts and stays inside explicit scope.
* Does not change governance artifacts unless the task authorizes it.
* Reports a design gap instead of inventing architecture.

### Scenario author

* Authors content against stable rule and scenario package schemas.
* Does not add unsupported mechanics to make the scenario convenient.
* Treats package validation and scenario acceptance tests as the contract.

### Reviewer

* Reviews a task against its brief, diff, requirements, decisions, and tests.
* Prioritizes correctness, authority boundaries, information leaks, regressions, and missing tests.
* Remains read-only and independent from the implementation approach where possible.

## Task lifecycle

Use these statuses:

1. **Planned**: Roadmap item exists, but unresolved dependencies or contracts prevent delegation.
2. **Ready**: Task brief is complete and contains no material design ambiguity.
3. **In progress**: One agent owns the task in one branch or worktree.
4. **Review**: Implementation and task-local verification are complete.
5. **Blocked**: A named external condition or unresolved design gap prevents progress.
6. **Done**: Review findings are resolved and the integrator has accepted the result.

Only the architect or integrator promotes a task to Ready or Done.

## Writing a task brief

Start from [`tasks/TASK_TEMPLATE.md`](tasks/TASK_TEMPLATE.md). A ready task must contain:

* one outcome stated in behavioral terms;
* stable requirement IDs and decision references;
* a context manifest listing exact files and sections;
* fixed assumptions that the agent must not revisit;
* explicit in-scope and out-of-scope boundaries;
* expected contracts and likely files;
* acceptance criteria that can be verified;
* required test and quality commands;
* permissions for governance-document changes; and
* the required handoff report.

Do not include brainstorm history, rejected alternatives already captured in decisions, unrelated future ideas, or the parent agent's hidden reasoning.

## Context routing

The task brief is the context router.

### Always read

* repository `AGENTS.md`;
* the assigned task brief; and
* the glossary entries named by the task brief.

### Read only when listed

* exact requirement ID ranges;
* named decision entries;
* specific high-level-design sections;
* the initial scenario;
* package schemas or code contracts; and
* relevant source and test files discovered while tracing the real path.

Do not load `doc/ideas.md` for implementation unless the task explicitly concerns promoting an idea. Do not read all project documents merely because they exist.

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

The integrator controls merge order according to `doc/roadmap.md` dependencies.

## Review and integration

Give the reviewer:

* the task brief;
* the implementation diff;
* linked requirements and decisions; and
* verification results.

Do not preload the reviewer with the implementer's justification beyond the concise handoff report. Independent reconstruction reduces anchoring.

The integrator:

1. resolves review findings;
2. runs the full available verification suite;
3. checks compatibility with already integrated tasks;
4. records task status and material deviations;
5. updates architecture artifacts only for accepted changes; and
6. performs semantic version bumps at meaningful implementation milestones.

## Handoff between chats

Start a fresh implementation chat with a short instruction:

```text
Execute doc/tasks/TASK-001-structured-output-preflight.md.
Follow AGENTS.md and the task's context manifest.
Do not broaden scope or change governance documents.
Return the required handoff report when complete.
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
