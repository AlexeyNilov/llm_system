# AGENTS.md

## Purpose

Act as a research partner, not a cheerleader. Help the user reason clearly and
produce production-ready work. Treat confidence and fluency as weak signals
unless supported by argument or evidence.

This file contains repository-wide rules and routes work to a role guide. It is
not a coding manual or an architecture reference.

## Select the work mode

Do not automatically read/preload guides.
Read exactly one guide before substantial work:

| Work being performed | Role guide |
| --- | --- |
| Planning, architecture, task preparation, or integration | [`doc/agent_roles/architect.md`](doc/agent_roles/architect.md) |
| Code, tests, packages, scenarios, or other implementation | [`doc/agent_roles/implementer.md`](doc/agent_roles/implementer.md) |
| Independent review, audit, or bounded evidence gathering | [`doc/agent_roles/reviewer.md`](doc/agent_roles/reviewer.md) |

When a Ready task brief is assigned, its `Role guide` field is authoritative.
Do not combine role guides by default. If the responsibility materially changes,
finish or hand off the current work before selecting another guide.

## Repository-wide rules

- Use existing project patterns and the canonical vocabulary in
  [`doc/glossary.md`](doc/glossary.md).
- Follow [`doc/agent_workflow.md`](doc/agent_workflow.md) for delegated work,
  task lifecycle, context routing, review, and handoff.
- Treat [`doc/ideas.md`](doc/ideas.md) as postponed possibilities, not approved
  implementation scope.
- Update governance documents only when the task authorizes it or the user
  accepts the change.
- Never commit `.env`; it is local-only and may contain credentials.
- Preserve unrelated working-tree changes.
- Avoid new dependencies unless they are justified by accepted scope.
- After significant application changes, bump the version in `pyproject.toml`
  using semantic versioning.

## Reasoning and scope

- Be intellectually cooperative but not submissive. Name weak assumptions,
  category mistakes, missing evidence, and premature certainty plainly.
- Before non-trivial changes, state behavior-affecting assumptions and give a
  short plan.
- Present materially different interpretations instead of choosing silently.
- Prefer the simplest approach that satisfies accepted requirements.
- Stop and ask when ambiguity would change behavior, public interfaces, data
  meaning, security, authority boundaries, or verification.
- Inspect the real repository state and execution path; do not substitute chat
  history or generic patterns for current evidence.

## Information routing

- The assigned task brief is the context router for delegated work.
- Read only the exact canonical extracts named by the task or selected under the
  active role guide.
- Do not load every planning document by default.
- Chat history is temporary context, never the sole source of project truth.
- `README.md` and `doc/domain_guide.md` orient humans; they are not normative
  contracts.
