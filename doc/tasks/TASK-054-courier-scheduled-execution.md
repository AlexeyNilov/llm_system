# TASK-054: Execute one scheduled courier decision with evidence

**Status:** Planned

**Objective:** Extend one-due scheduled NPC execution to the authored courier. A courier decision runs outside the write transaction, revision/queue selection is rechecked, and its resulting action plus functional-generation evidence are committed atomically.

**Required design before Ready:** define the typed scheduled-execution trace variant that retains courier generation evidence; define SQLite V5 migration; decide gateway injection from the player-turn scheduler caller; add initial courier eligibility after caretaker without queue draining.

**Out of scope:** retries, recurrence, queue draining, environmental/System activities, memory, narration, UI, and generic policy registry.
