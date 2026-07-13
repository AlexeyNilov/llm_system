# Architect and Integrator Guide

## Responsibility

Use this guide for planning, architecture, task preparation, governance, and
integration. The objective is to remove material ambiguity before execution and
keep durable project truth coherent.

## Context selection

Start from the current objective, then select only the canonical sections needed
to decide it. Do not automatically read every governance document.

Use each source for its owned information:

- `doc/glossary.md`: vocabulary;
- `doc/requirements.md`: accepted behavior and constraints;
- `doc/decisions.md`: accepted choices and rationale;
- `doc/high_level_design.md`: components and information flow;
- `doc/initial_scenario.md`: accepted Greybridge content;
- `doc/roadmap.md`: dependency order and readiness;
- `doc/ideas.md`: postponed possibilities only; and
- `doc/codex-task-state.md`: compact continuation state when resuming work.

Consult Git state, source, tests, or review evidence when the decision depends on
what is actually implemented. README and the domain guide may help orientation,
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
- Ask consequential design questions separately when their answers affect later
  choices.

## Task preparation

- Use `doc/tasks/TASK_TEMPLATE.md` and `doc/agent_workflow.md`.
- Make the task behaviorally complete and free of material design choices.
- Select one execution role guide and exact canonical extracts.
- Keep fixed assumptions task-specific; reference stable truth instead of
  copying it.
- Estimate the pre-code context budget and narrow broad selections.
- Define acceptance criteria, permitted governance changes, verification, and
  stop conditions before setting a task Ready.

## Integration

- Independently inspect the task brief, diff, tests, handoff, and review findings.
- Distinguish an agent-reported result from parent verification.
- Resolve findings and cross-task consequences before marking a task Done.
- Update roadmap or governance only for accepted outcomes.
- Run verification proportionate to the integrated risk.
- Do not require TDD for planning-only documentation changes; require behavioral
  evidence whenever application behavior changes.
