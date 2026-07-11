This is delegation only, not integration.

Delegate <READY_TASK_PATH> to the custom agent named by the task brief.
Do not pass prior chat history.

The execution agent may set the task to In progress, then Review or Blocked.
Neither the execution agent nor this parent task may mark it Done, review or
accept the result, update the roadmap or governance documents, stage files,
or commit changes.

Wait for the execution agent, then return its handoff and changed-file list
without adding an acceptance judgment. Integration will happen separately.