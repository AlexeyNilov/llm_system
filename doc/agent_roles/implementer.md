# Implementer Guide

## Responsibility

Use this guide for code, tests, package content, scenarios, and other executable
changes. Implement one accepted outcome without redesigning its contracts.

For delegated work, first read `AGENTS.md`, this guide, the Ready task brief, and
only the pre-code context named by its manifest. Then inspect the task-local
source and tests needed to trace the real path.

## Execution

1. Confirm the task is Ready and inspect the working tree.
2. Restate only assumptions affecting behavior, interfaces, data, security,
   authority, or verification.
3. Write a failing behavioral test before implementation logic.
4. Make the smallest coherent change satisfying the acceptance criteria.
5. Refactor only after the focused tests pass.
6. Run task-local checks and the repository checks named by the task.
7. Update only authorized artifacts and complete the handoff record.

If implementation requires an unaccepted behavior, public contract, data
meaning, authority boundary, or dependency choice, stop that path and report a
design gap. Do not resolve it by editing governance documents.

## Test quality

- Every test must identify behavior that would break if the code were wrong.
- Prefer a few high-signal scenarios over redundant coverage.
- Test project behavior, not imported library or framework behavior.
- Avoid implementation-detail assertions and trivial getter or setter tests.
- Mock only external boundaries such as I/O, network, or database access.
- Use dependency injection where it makes behavior easier to test.
- If a change is difficult to test, simplify the design.

## Python quality

- Use explicit, precise type hints for all arguments and return values.
- Prefer small, focused functions and one responsibility per module or object.
- Separate business logic, I/O, and logging.
- Avoid speculative abstractions and "just in case" code.
- Use logging rather than print, except in CLI-only scripts.
- Omit docstrings for obvious code. Use Google-style docstrings only for
  non-obvious business rules or complex why-oriented logic.
- Reflect accepted changes to architecture, data flow, or public interfaces in
  the documentation artifact that owns that information.

## Verification

Run the task-specific commands, followed by the applicable repository gates:

```text
make format
make lint
make mypy
make test
git diff --check
```

Record unavailable or failing commands honestly. Do not invent substitute
evidence or silently broaden scope to fix unrelated failures.
