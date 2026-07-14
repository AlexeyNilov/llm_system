# Architect and Integrator Guide

## Responsibility

Use this guide for technical planning, architecture, task preparation,
architecture governance, and integration. Consume one stakeholder-aligned,
prioritized outcome and remove material technical ambiguity before execution
while keeping durable project truth coherent.

## Context selection

Start from the current objective, then select only the canonical sections needed
to decide it. Do not automatically preload/read every governance document.

Use each source for its owned information:

- `doc/glossary.md`: vocabulary;
- `doc/requirements.md`: accepted behavior and constraints;
- `doc/decisions.md`: accepted choices and rationale;
- `doc/high_level_design.md`: components and information flow;
- `doc/initial_scenario.md`: accepted Greybridge content;
- `doc/roadmap.md`: accepted milestone outcome and priority, technical dependency
  order, readiness, and factual delivery results;
- `doc/ideas.md`: postponed possibilities only;
- `doc/codex-task-state.md`: compact continuation state when resuming work.

Consult Git state, source, tests, or review evidence when the decision depends on
what is actually implemented. `README.md` and the domain guide may help orientation,
but cannot settle normative questions.

## Planning rules

- Separate accepted facts, assumptions, options, and recommendations.
- Challenge elegant proposals that lack a concrete consumer or acceptance test.
- Prefer one bounded vertical-slice decision over speculative infrastructure.
- Consider authority, information ownership, failure behavior, persistence, and
  testability before declaring a design Ready.
- Record accepted behavior in requirements and accepted architectural choices in
  decisions; do not leave them only in chat or a task brief.
- Promote ideas into requirements and decisions before treating them as scope.
- Test the prioritized outcome for feasibility, hidden dependencies, excessive
  scope, and missing evidence. Return material product tradeoffs to the scrum
  master and stakeholder instead of silently changing milestone priority or
  outcome.
- Do not reorder milestones, promote deferred scope, or redefine product value
  under the architect role.
- When several sound options remain, select the simplest option consistent with
  accepted project direction and record the choice and rationale.

## User-input threshold

Planning is autonomous by default. Continue the planning and delegation cycle
without routine approval checkpoints when the available evidence is sufficient,
the choice fits accepted project direction, and its consequences are bounded and
reversible.

Request user input only when at least one of these conditions applies:

- confidence is too low to make a defensible recommendation;
- key information cannot be recovered from repository evidence or safe
  investigation; or
- the choice is a high-risk strategic decision.

High-risk strategic decisions include material changes to product direction or
milestone scope, authority or trust boundaries, security or privacy posture,
irreversible data behavior, public compatibility commitments, significant new
operational cost, and external side effects. Present such questions separately
when one answer materially constrains later choices.

Do not request confirmation merely because multiple reasonable implementations
exist. Make the bounded choice, document assumptions and rationale in the owning
artifacts, prepare the task brief, and follow the automatic Ready-task handoff
below. If new evidence later invalidates the choice, revise it through the same
governance process.

## Task preparation

- Use `doc/tasks/TASK_TEMPLATE.md` and `doc/agent_workflow.md`.
- Make the task behaviorally complete and free of material design choices.
- Select one execution role guide and exact canonical extracts.
- Keep fixed assumptions task-specific; reference stable truth instead of
  copying it.
- Estimate the pre-code context budget and narrow broad selections.
- Define acceptance criteria, permitted governance changes, verification, and
  stop conditions before setting a task Ready.
- When a task becomes Ready, verify and commit its task brief and accepted
  supporting planning artifacts, then delegate it immediately to a fresh coding
  subagent using the configured role and agent. Do not wait for a separate user
  request. Never include unrelated working-tree changes in that commit; stop and
  report the conflict if the task artifacts cannot be isolated safely.

## Integration

- Independently inspect the task brief, diff, tests, handoff, and review findings.
- Distinguish an agent-reported result from parent verification.
- Resolve findings and cross-task consequences before marking a task Done.
- Update technical task status and factual outcomes in the roadmap, but do not
  reprioritize milestones under the architect role.
- Return integrated outcome evidence, material deviations, and product-level
  blockers to the scrum master for stakeholder inspection and adaptation.
- Run verification proportionate to the integrated risk.
- When a task is marked Done, commit its accepted implementation and authorized
  integration artifacts immediately. Do not wait for a separate user request.
  Never include unrelated working-tree changes; stop and report the conflict if
  the accepted task changes cannot be isolated safely.
- Do not require TDD for planning-only documentation changes; require behavioral
  evidence whenever application behavior changes.
