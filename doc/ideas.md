# Ideas

This file is a parking lot for promising possibilities that are not part of the accepted scope. An idea must be promoted into `requirements.md` and, when architectural, `decisions.md` before implementation begins.

## Guidance

* Preserve the motivation, not just the proposed feature.
* State why the idea is postponed and what evidence should trigger reconsideration.
* Do not treat an idea as a commitment, requirement, or implementation instruction.
* Remove an entry when it is rejected; mark it promoted when it becomes accepted work.

## Entry template

```markdown
### IDEA-NNN: Title

**Status:** Backlog | Promoted

**Opportunity:** What could this enable?

**Why postponed:** Why should it not be implemented now?

**Revisit when:** What evidence or project milestone should bring it back for discussion?
```

## Backlog

### IDEA-001: Generate game packages from source material

**Status:** Backlog

**Opportunity:** Use an offline LLM-assisted workflow to extract claims, concepts, relationships, rules, exceptions, and scenario content from a LitRPG book or other source. Produce draft rule and scenario packs with provenance, confidence, ambiguities, and contradictions for human review.

**Why postponed:** Narrative text is incomplete and inconsistent as a formal specification. The package schemas and validation rules must exist before generated drafts have a reliable target.

**Revisit when:** A hand-authored rule pack and scenario pack can run a complete vertical slice and their information model has survived practical use.

### IDEA-002: Add GraphRAG for NPC knowledge

**Status:** Backlog

**Opportunity:** Represent and retrieve multi-hop relationships among NPCs, factions, places, events, beliefs, and knowledge.

**Why postponed:** The initial NPC retrieval questions are not yet known, and structured profiles plus episodic memory are simpler to validate.

**Revisit when:** Concrete NPC decisions repeatedly require relationship traversal that simple structured data and memory retrieval cannot answer well.

### IDEA-003: Simulate distant NPCs at lower fidelity

**Status:** Backlog

**Opportunity:** Let a larger world continue evolving without invoking an LLM for every NPC whenever simulation time advances.

**Why postponed:** The initial scenario is intentionally small, so separate active and background simulation modes would add unused complexity.

**Revisit when:** LLM cost or latency grows materially because the world contains NPCs outside the active scene.

### IDEA-004: Add real-time progression

**Status:** Backlog

**Opportunity:** Drive the existing simulation clock from wall-clock time to create a world that progresses while the player remains connected or away.

**Why postponed:** Real-time behavior complicates reproducibility, persistence, operations, and tolerance of local LLM latency.

**Revisit when:** Discrete action-driven time is stable and a concrete experience requires continuous or offline progression.

### IDEA-005: Support richer world lifecycles

**Status:** Backlog

**Opportunity:** Add multiple worlds, save slots, branching timelines, or multiplayer participation.

**Why postponed:** These features require identity, concurrency, compatibility, and lifecycle policies that do not help validate the initial single-world loop.

**Revisit when:** The single persistent world is reliable and a specific use case justifies one of these lifecycle models.

### IDEA-006: Use scenarios for experiential decision-making practice

**Status:** Backlog

**Opportunity:** Place participants in situations with incomplete information, competing priorities, social consequences, and no obvious correct answer. Use the simulation history to support reflection on what they perceived, chose, and caused.

**Why postponed:** A credible learning tool needs explicit learning goals, thoughtful debriefing, privacy boundaries, and evidence that its feedback is useful rather than merely persuasive narration.

**Revisit when:** The simulation can reliably preserve information boundaries, resolve consequences, and expose an inspectable decision and event history.

### IDEA-007: Generate location graphs from maps and imagery

**Status:** Backlog

**Opportunity:** Use visual-language and geospatial processing to identify candidate regions, landmarks, routes, barriers, and spatial relationships in an existing game map, conventional map, or satellite image. Produce a draft location graph with source references, confidence, and an editable visual representation.

**Why postponed:** Image interpretation is ambiguous, and useful extraction requires stable location and connection schemas plus measurable graph-validation criteria. Generated topology must not become canonical without review.

**Revisit when:** A hand-authored location graph supports the complete vertical slice and the project can validate connectivity, reachability, required metadata, and scenario compatibility.
