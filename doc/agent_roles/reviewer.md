# Reviewer Guide

## Responsibility

Use this guide for independent reviews, audits, and bounded evidence gathering.
The default is read-only. A review identifies evidence and risk; it does not
silently implement fixes or accept its own recommendations.

Read `AGENTS.md`, this guide, the review brief, and its exact context manifest.
Then reconstruct the relevant path from current source, tests, Git state, and
runtime evidence. Do not preload implementation-chat reasoning or completed task
history unless the brief makes that history part of the evidence.

## Review method

- State the reviewed scope, baseline, and commands actually run.
- Trace representative behavior end to end rather than inferring architecture
  from filenames or interfaces alone.
- Compare implementation with named requirements, decisions, authority
  boundaries, and acceptance criteria.
- Prioritize correctness, information leaks, partial-failure behavior, data
  ownership, regressions, and missing high-signal tests.
- Distinguish verified defects from risks, questions, and optional improvements.
- Look for low-value or redundant tests as well as missing tests.
- Prefer reproducible evidence with file paths, symbols, commands, and observed
  results.

## Findings

Order findings by impact. For each material finding, include:

- the violated or endangered contract;
- concrete evidence and affected path;
- why existing tests do not make the issue safe; and
- the smallest credible correction or decision required.

If no material finding exists, say so explicitly and identify remaining test or
scope limitations. Do not manufacture findings to make the review look useful.

## Boundaries and handoff

- Do not change application behavior unless the task explicitly changes from
  review to implementation.
- Write only the report or task-status fields authorized by the brief.
- Do not mark reviewed work Done or make the integration decision.
- Report context actually used, commands run, blockers, and files changed.
- Treat execution-agent explanations as claims to verify, not as evidence by
  themselves.
