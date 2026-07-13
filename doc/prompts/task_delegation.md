This is delegation only, not integration.

Delegate <READY_TASK_PATH> to a fresh subagent using the Agent configuration
specified by the task brief. `Default` means no custom-agent profile.
Do not pass prior chat history.

The task brief is the context router. Read only its exact pre-code selections,
then trace task-local source and tests. Do not preload README, the domain guide,
roadmap, ideas, reviews, completed tasks, or architect continuation state unless
the task explicitly names them. Report the context actually used in the handoff.

The execution agent may set the task to In progress, then Review or Blocked.
Neither the execution agent nor this parent task may mark it Done, review or
accept the result, update the roadmap or governance documents, stage files,
or commit changes.

Wait for the execution agent, then return its handoff and changed-file list
without adding an acceptance judgment. Integration will happen separately.
