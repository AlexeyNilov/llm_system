import sqlite3
from pathlib import Path
from typing import Literal
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.simulation import (
    ActorActionSubmission,
    ActorObservedEvent,
    BooleanWorldFactState,
    CharacterState,
    CompletedActorActionStepTrace,
    ConnectionState,
    EnvironmentalScheduledActivity,
    EventObserved,
    LocationObserved,
    LocationTarget,
    ObjectPossessedByCharacter,
    ObjectState,
    ObjectUsedEvent,
    PerceptionSnapshot,
    PlayerInterpreterActionSource,
    ScheduledActivityQueue,
    SucceededOutcome,
    UseActionProposal,
    WorldState,
    ObserveActionProposal,
    SurroundingsTarget,
)
from llm_system.application import (
    WorldPackageMismatchError,
    execute_actor_action_step,
)
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import (
    DuplicateSimulationStepIdentityError,
    PackageReference,
    SQLiteStore,
    StoredRecordDecodingError,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")
PROPOSAL_ID = UUID("00000000-0000-4000-8000-000000000002")
STEP_ID = UUID("00000000-0000-4000-8000-000000000003")
CONTEXT_ID = UUID("00000000-0000-4000-8000-000000000004")
OUTCOME_ID = UUID("00000000-0000-4000-8000-000000000005")
EVENT_ID = UUID("00000000-0000-4000-8000-000000000006")
ACTIVITY_ID = UUID("00000000-0000-4000-8000-000000000007")


def _packages() -> ValidatedGamePackages:
    rule = load_game_package(
        REPOSITORY_ROOT / "game_packages/rules/greybridge-rules/0.2.0"
    )
    scenario = load_game_package(
        REPOSITORY_ROOT / "game_packages/scenarios/storm-at-greybridge/0.2.0"
    )
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


def _state() -> WorldState:
    packages = _packages()
    scenario = packages.scenario_package
    return WorldState(
        simulation_time_seconds=120,
        characters=(
            CharacterState(character_id="player", location_id="greybridge-span"),
            CharacterState(
                character_id="injured-courier", location_id="greybridge-waystation"
            ),
            CharacterState(
                character_id="bridge-caretaker", location_id="greybridge-span"
            ),
        ),
        objects=(
            ObjectState(
                object_id="medicine",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character",
                    character_id="injured-courier",
                ),
            ),
            ObjectState(
                object_id="reinforcement-materials",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="player"
                ),
            ),
        ),
        connections=tuple(
            ConnectionState(connection_id=item.id, is_available=True)
            for item in scenario.definition.spatial_graph.connections
        ),
        boolean_world_facts=(
            BooleanWorldFactState(fact_id="bridge-reinforced", value=False),
        ),
    )


def _queue() -> ScheduledActivityQueue:
    return ScheduledActivityQueue(
        activities=(
            EnvironmentalScheduledActivity(
                activity_type="environmental",
                activity_id=ACTIVITY_ID,
                eligible_at_seconds=200,
                insertion_sequence=1,
                schedule_id="storm-intensifies",
            ),
        )
    )


def _store(tmp_path: Path) -> SQLiteStore:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    with store.unit_of_work() as unit:
        unit.worlds.create(
            world_id=WORLD_ID,
            rule_package=PackageReference(
                package_id=packages.rule_package.manifest.package_id,
                package_version=packages.rule_package.manifest.package_version,
            ),
            scenario_package=PackageReference(
                package_id=packages.scenario_package.manifest.package_id,
                package_version=packages.scenario_package.manifest.package_version,
            ),
            state=_state(),
            scheduled_queue=_queue(),
        )
        unit.commit()
    return store


def _submission(
    *,
    step_id: UUID = STEP_ID,
    proposal_id: UUID = PROPOSAL_ID,
    target_id: str = "greybridge-span",
) -> ActorActionSubmission:
    return ActorActionSubmission(
        proposal_id=proposal_id,
        simulation_step_id=step_id,
        decision_context_id=CONTEXT_ID,
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="player",
        proposal=UseActionProposal(
            operation="use",
            object_id="reinforcement-materials",
            target=LocationTarget(target_type="location", location_id=target_id),
        ),
    )


TraceMismatch = Literal[
    "step",
    "context",
    "proposal",
    "perception-actor",
    "perception-time",
    "feedback-actor",
    "feedback-time",
]


def _trace_with_mismatch(mismatch: TraceMismatch) -> CompletedActorActionStepTrace:
    proposal_id = UUID("10000000-0000-4000-8000-000000000001")
    step_id = UUID("20000000-0000-4000-8000-000000000001")
    context_id = UUID("30000000-0000-4000-8000-000000000001")
    outcome_id = UUID("40000000-0000-4000-8000-000000000001")
    event_id = UUID("50000000-0000-4000-8000-000000000001")
    submission = ActorActionSubmission(
        proposal_id=proposal_id,
        simulation_step_id=step_id,
        decision_context_id=context_id,
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="player",
        proposal=ObserveActionProposal(
            operation="observe",
            target=SurroundingsTarget(target_type="surroundings"),
        ),
    )
    event = ActorObservedEvent(
        event_type="actor_observed",
        event_id=event_id,
        outcome_id=outcome_id,
        occurred_at_seconds=10,
        actor_id="player",
        target=SurroundingsTarget(target_type="surroundings"),
    )
    outcome = SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=(
            UUID("10000000-0000-4000-8000-000000000002")
            if mismatch == "proposal"
            else proposal_id
        ),
        reason_code="observed",
        resolved_at_seconds=10,
        state_changes=(),
        events=(event,),
    )
    perception_actor = "other" if mismatch == "perception-actor" else "player"
    perception_time = 11 if mismatch == "perception-time" else 10
    perception = PerceptionSnapshot(
        observer_id=perception_actor,
        perceived_at_seconds=perception_time,
        observations=(
            LocationObserved(
                observation_type="location",
                source_type="current_state",
                observer_id=perception_actor,
                observed_at_seconds=perception_time,
                location_id="room",
            ),
        ),
    )
    feedback_actor = "other" if mismatch == "feedback-actor" else "player"
    feedback_time = 11 if mismatch == "feedback-time" else 10
    feedback = EventObserved(
        observation_type="event",
        source_type="canonical_event",
        observer_id=feedback_actor,
        observed_at_seconds=feedback_time,
        event=event,
    )
    return CompletedActorActionStepTrace(
        trace_schema_version=1,
        simulation_step_id=(
            UUID("20000000-0000-4000-8000-000000000002")
            if mismatch == "step"
            else step_id
        ),
        decision_context_id=(
            UUID("30000000-0000-4000-8000-000000000002")
            if mismatch == "context"
            else context_id
        ),
        submission=submission,
        outcome=outcome,
        current_perception=perception,
        self_event_feedback=(feedback,),
    )


@pytest.mark.parametrize(
    ("mismatch", "message"),
    [
        ("step", "simulation step identity"),
        ("context", "decision context identity"),
        ("proposal", "outcome proposal identity"),
        ("perception-actor", "current perception actor"),
        ("perception-time", "current perception time"),
        ("feedback-actor", "self-event feedback actor"),
        ("feedback-time", "self-event feedback time"),
    ],
)
def test_completed_trace_rejects_incoherent_evidence(
    mismatch: TraceMismatch, message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        _trace_with_mismatch(mismatch)


def test_greybridge_step_commits_world_event_trace_and_preserves_due_queue(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    packages = _packages()
    submission = _submission()

    completed = execute_actor_action_step(
        store,
        packages,
        submission,
        outcome_id=OUTCOME_ID,
        event_id=EVENT_ID,
    )

    assert completed.world_id == WORLD_ID
    assert completed.resulting_world_revision == 1
    assert completed.trace.submission is submission
    assert completed.trace.outcome.status == "succeeded"
    assert completed.trace.outcome.resolved_at_seconds == 420
    assert len(completed.trace.self_event_feedback) == 1
    feedback_event = completed.trace.self_event_feedback[0].event
    assert isinstance(feedback_event, ObjectUsedEvent)
    assert feedback_event.event_id == EVENT_ID

    reopened = SQLiteStore.open(tmp_path / "world.sqlite3")
    with reopened.unit_of_work() as unit:
        world = unit.worlds.get()
        events = unit.events.list_for_world(WORLD_ID)
        traces = unit.traces.list_for_world(WORLD_ID)
    assert world is not None
    assert world.revision == 1
    assert world.state.simulation_time_seconds == 420
    assert world.state.boolean_world_facts[0].value is True
    assert world.scheduled_queue == _queue()
    assert [record.event.event_id for record in events] == [EVENT_ID]
    assert len(traces) == 1
    assert traces[0].trace == completed.trace


def test_rejected_step_advances_revision_without_state_event_or_queue_change(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)

    completed = execute_actor_action_step(
        store,
        _packages(),
        _submission(target_id="far-bank"),
        outcome_id=OUTCOME_ID,
        event_id=EVENT_ID,
    )

    assert completed.resulting_world_revision == 1
    assert completed.trace.outcome.status == "rejected"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.state == _state()
        assert world.scheduled_queue == _queue()
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert len(unit.traces.list_for_world(WORLD_ID)) == 1


def test_duplicate_trace_rolls_back_successful_step_atomically(tmp_path: Path) -> None:
    store = _store(tmp_path)
    packages = _packages()
    execute_actor_action_step(
        store,
        packages,
        _submission(target_id="far-bank"),
        outcome_id=OUTCOME_ID,
        event_id=EVENT_ID,
    )

    with pytest.raises(DuplicateSimulationStepIdentityError):
        execute_actor_action_step(
            store,
            packages,
            _submission(proposal_id=UUID("00000000-0000-4000-8000-000000000008")),
            outcome_id=UUID("00000000-0000-4000-8000-000000000009"),
            event_id=UUID("00000000-0000-4000-8000-000000000010"),
        )

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert world.state == _state()
        assert world.scheduled_queue == _queue()
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert len(unit.traces.list_for_world(WORLD_ID)) == 1


def test_package_mismatch_fails_before_resolution_without_writes(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    packages = _packages()
    mismatched = packages.model_copy(
        update={
            "rule_package": packages.rule_package.model_copy(
                update={
                    "manifest": packages.rule_package.manifest.model_copy(
                        update={"package_version": "9.9.9"}
                    )
                }
            )
        }
    )

    with pytest.raises(WorldPackageMismatchError):
        execute_actor_action_step(
            store,
            mismatched,
            _submission(),
            outcome_id=OUTCOME_ID,
            event_id=EVENT_ID,
        )

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 0
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert unit.traces.list_for_world(WORLD_ID) == ()


def test_trace_history_strictly_cross_checks_explicit_metadata(tmp_path: Path) -> None:
    store = _store(tmp_path)
    execute_actor_action_step(
        store,
        _packages(),
        _submission(),
        outcome_id=OUTCOME_ID,
        event_id=EVENT_ID,
    )
    with sqlite3.connect(tmp_path / "world.sqlite3") as connection:
        connection.execute(
            "UPDATE simulation_step_traces SET outcome_status = 'failed'"
        )

    with store.unit_of_work() as unit:
        with pytest.raises(StoredRecordDecodingError):
            unit.traces.list_for_world(WORLD_ID)
