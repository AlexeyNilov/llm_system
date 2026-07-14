import json
import sqlite3
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.application import (
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    PlayerInterpretationResult,
    PlayerInterpreterOutput,
    create_world,
    execute_actor_action_step,
    reset_world_for_development,
)
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import (
    DuplicatePlayerInputIdentityError,
    PackageReference,
    SQLiteStore,
    StoredRecordDecodingError,
    UnitOfWorkFailedError,
    WorldIdentityMismatchError,
    WorldRevisionMismatchError,
)
from llm_system.player_input_traces import (
    ActionLinkedCompletion,
    ClarificationCompletion,
    PlayerInputStepTrace,
    ThoughtOnlyCompletion,
)
from llm_system.simulation import (
    CharacterState,
    ActorActionSubmission,
    LocationObserved,
    PerceptionSnapshot,
    PlayerInterpreterActionSource,
    ScheduledActivityQueue,
    WaitActionProposal,
    WorldState,
)
from llm_system.application.actor_action_step import CompletedActorActionStep

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "game_packages"


def _packages() -> ValidatedGamePackages:
    rule = load_game_package(PACKAGE_ROOT / "rules/greybridge-rules/0.2.0")
    scenario = load_game_package(PACKAGE_ROOT / "scenarios/storm-at-greybridge/0.2.0")
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


def _result() -> PlayerInterpretationResult:
    output = PlayerInterpreterOutput(
        result_type="interpreted",
        private_thought="Wait and listen.",
        proposal=None,
        clarification=None,
    )
    return PlayerInterpretationResult(
        player_text="I wait and listen.",
        perception=PerceptionSnapshot(
            observer_id="player",
            perceived_at_seconds=0,
            observations=(
                LocationObserved(
                    observation_type="location",
                    source_type="current_state",
                    observer_id="player",
                    observed_at_seconds=0,
                    location_id="waystation",
                ),
            ),
        ),
        output=output,
        generation=FunctionalGenerationResult[PlayerInterpreterOutput](
            disposition=FunctionalGenerationDisposition.ACCEPTED,
            value=output,
            initial_attempt=FunctionalGenerationAttempt(
                content=json.dumps(output.model_dump(mode="json")), finish_reason="stop"
            ),
        ),
    )


def _clarification_result() -> PlayerInterpretationResult:
    output = PlayerInterpreterOutput(
        result_type="clarification",
        private_thought=None,
        proposal=None,
        clarification="Which direction do you mean?",
    )
    return _result().model_copy(
        update={
            "output": output,
            "generation": FunctionalGenerationResult[PlayerInterpreterOutput](
                disposition=FunctionalGenerationDisposition.ACCEPTED,
                value=output,
                initial_attempt=FunctionalGenerationAttempt(
                    content=json.dumps(output.model_dump(mode="json")),
                    finish_reason="stop",
                ),
            ),
        }
    )


def _action_result() -> PlayerInterpretationResult:
    output = PlayerInterpreterOutput(
        result_type="interpreted",
        private_thought=None,
        proposal=WaitActionProposal(operation="wait", duration_seconds=1),
        clarification=None,
    )
    return _result().model_copy(
        update={
            "output": output,
            "generation": FunctionalGenerationResult[PlayerInterpreterOutput](
                disposition=FunctionalGenerationDisposition.ACCEPTED,
                value=output,
                initial_attempt=FunctionalGenerationAttempt(
                    content=json.dumps(output.model_dump(mode="json")),
                    finish_reason="stop",
                ),
            ),
        }
    )


def _complete_wait_step(store: SQLiteStore, world_id: UUID) -> CompletedActorActionStep:
    return execute_actor_action_step(
        store,
        _packages(),
        ActorActionSubmission(
            proposal_id=UUID("50000000-0000-4000-8000-000000000001"),
            simulation_step_id=UUID("50000000-0000-4000-8000-000000000002"),
            decision_context_id=UUID("50000000-0000-4000-8000-000000000003"),
            source=PlayerInterpreterActionSource(
                source_type="player_interpreter", interpreter_id="parser"
            ),
            actor_id="player",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
        ),
        outcome_id=UUID("50000000-0000-4000-8000-000000000004"),
        event_id=UUID("50000000-0000-4000-8000-000000000005"),
    )


def test_thought_only_trace_requires_an_interpreted_thought_without_proposal() -> None:
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("10000000-0000-4000-8000-000000000001"),
        interpretation=_result(),
        completion=ThoughtOnlyCompletion(completion_type="thought_only"),
    )

    assert trace.completion.completion_type == "thought_only"
    with pytest.raises(ValidationError, match="action-linked"):
        PlayerInputStepTrace(
            trace_schema_version=1,
            player_input_id=UUID("10000000-0000-4000-8000-000000000002"),
            interpretation=_result(),
            completion=ActionLinkedCompletion(
                completion_type="action_linked",
                simulation_step_id=UUID("20000000-0000-4000-8000-000000000001"),
            ),
        )


def test_thought_only_trace_appends_in_order_and_duplicate_poison_rolls_back(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    world_id = UUID("30000000-0000-4000-8000-000000000001")
    with store.unit_of_work() as unit:
        unit.worlds.create(
            world_id=world_id,
            rule_package=PackageReference(package_id="rules", package_version="1.0.0"),
            scenario_package=PackageReference(
                package_id="scenario", package_version="1.0.0"
            ),
            state=WorldState(
                simulation_time_seconds=0,
                characters=(
                    CharacterState(character_id="player", location_id="waystation"),
                ),
                objects=(),
                connections=(),
            ),
            scheduled_queue=ScheduledActivityQueue(activities=()),
        )
        unit.commit()
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("40000000-0000-4000-8000-000000000001"),
        interpretation=_result(),
        completion=ThoughtOnlyCompletion(completion_type="thought_only"),
    )
    with store.unit_of_work() as unit:
        stored = unit.player_input_traces.append(
            world_id=world_id,
            observed_world_revision=0,
            resulting_world_revision=0,
            trace=trace,
        )
        assert stored.insertion_sequence == 1
        unit.commit()
    with pytest.raises(DuplicatePlayerInputIdentityError):
        with store.unit_of_work() as unit:
            unit.player_input_traces.append(
                world_id=world_id,
                observed_world_revision=0,
                resulting_world_revision=0,
                trace=trace,
            )
            with pytest.raises(UnitOfWorkFailedError):
                unit.commit()
    with store.unit_of_work() as unit:
        assert unit.player_input_traces.list_for_world(world_id) == (stored,)


def test_clarification_requires_equal_revisions_and_no_action_link(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    world_id = UUID("60000000-0000-4000-8000-000000000001")
    create_world(store, _packages(), world_id=world_id)
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("60000000-0000-4000-8000-000000000002"),
        interpretation=_clarification_result(),
        completion=ClarificationCompletion(completion_type="clarification"),
    )
    with store.unit_of_work() as unit:
        stored = unit.player_input_traces.append(
            world_id=world_id,
            observed_world_revision=0,
            resulting_world_revision=0,
            trace=trace,
        )
        unit.commit()
    assert stored.trace.completion.completion_type == "clarification"
    with pytest.raises(WorldRevisionMismatchError):
        with store.unit_of_work() as unit:
            unit.player_input_traces.append(
                world_id=world_id,
                observed_world_revision=0,
                resulting_world_revision=1,
                trace=trace,
            )


def test_action_link_requires_real_matching_actor_trace_and_rolls_back(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    world_id = UUID("70000000-0000-4000-8000-000000000001")
    create_world(store, _packages(), world_id=world_id)
    completed = _complete_wait_step(store, world_id)
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("70000000-0000-4000-8000-000000000002"),
        interpretation=_action_result(),
        completion=ActionLinkedCompletion(
            completion_type="action_linked",
            simulation_step_id=completed.trace.simulation_step_id,
        ),
    )
    with store.unit_of_work() as unit:
        stored = unit.player_input_traces.append(
            world_id=world_id,
            observed_world_revision=0,
            resulting_world_revision=1,
            trace=trace,
        )
        unit.commit()
    assert stored.trace == trace
    missing = trace.model_copy(
        update={
            "player_input_id": UUID("70000000-0000-4000-8000-000000000003"),
            "completion": ActionLinkedCompletion(
                completion_type="action_linked",
                simulation_step_id=UUID("70000000-0000-4000-8000-000000000004"),
            ),
        }
    )
    with pytest.raises(StoredRecordDecodingError, match="matching actor-action"):
        with store.unit_of_work() as unit:
            unit.player_input_traces.append(
                world_id=world_id,
                observed_world_revision=0,
                resulting_world_revision=1,
                trace=missing,
            )
    with store.unit_of_work() as unit:
        assert unit.player_input_traces.list_for_world(world_id) == (stored,)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("world_id", "other-world"),
        ("resulting_world_revision", 2),
    ],
)
def test_action_link_rejects_actor_trace_in_wrong_world_or_revision(
    tmp_path: Path, column: str, value: str | int
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    world_id = UUID("71000000-0000-4000-8000-000000000001")
    create_world(store, _packages(), world_id=world_id)
    completed = _complete_wait_step(store, world_id)
    with sqlite3.connect(database) as connection:
        connection.execute(f"UPDATE simulation_step_traces SET {column} = ?", (value,))
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("71000000-0000-4000-8000-000000000002"),
        interpretation=_action_result(),
        completion=ActionLinkedCompletion(
            completion_type="action_linked",
            simulation_step_id=completed.trace.simulation_step_id,
        ),
    )
    with pytest.raises(StoredRecordDecodingError, match="matching actor-action"):
        with store.unit_of_work() as unit:
            unit.player_input_traces.append(
                world_id=world_id,
                observed_world_revision=0,
                resulting_world_revision=1,
                trace=trace,
            )
    with store.unit_of_work() as unit:
        assert unit.player_input_traces.list_for_world(world_id) == ()


def test_player_input_trace_rejects_wrong_current_world_or_revision(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    world_id = UUID("80000000-0000-4000-8000-000000000001")
    create_world(store, _packages(), world_id=world_id)
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("80000000-0000-4000-8000-000000000002"),
        interpretation=_result(),
        completion=ThoughtOnlyCompletion(completion_type="thought_only"),
    )
    with pytest.raises(WorldIdentityMismatchError):
        with store.unit_of_work() as unit:
            unit.player_input_traces.append(
                world_id=UUID("80000000-0000-4000-8000-000000000003"),
                observed_world_revision=0,
                resulting_world_revision=0,
                trace=trace,
            )
    with pytest.raises(WorldRevisionMismatchError):
        with store.unit_of_work() as unit:
            unit.player_input_traces.append(
                world_id=world_id,
                observed_world_revision=0,
                resulting_world_revision=1,
                trace=trace,
            )


def test_player_input_payload_metadata_tampering_fails_strict_decoding(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    world_id = UUID("90000000-0000-4000-8000-000000000001")
    create_world(store, _packages(), world_id=world_id)
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("90000000-0000-4000-8000-000000000002"),
        interpretation=_result(),
        completion=ThoughtOnlyCompletion(completion_type="thought_only"),
    )
    with store.unit_of_work() as unit:
        unit.player_input_traces.append(
            world_id=world_id,
            observed_world_revision=0,
            resulting_world_revision=0,
            trace=trace,
        )
        unit.commit()
    with sqlite3.connect(tmp_path / "world.sqlite3") as connection:
        connection.execute(
            "UPDATE player_input_step_traces SET completion_kind = 'clarification'"
        )
    with pytest.raises(StoredRecordDecodingError, match="player-input"):
        with store.unit_of_work() as unit:
            unit.player_input_traces.list_for_world(world_id)


def test_development_reset_removes_player_input_history(tmp_path: Path) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    world_id = UUID("a0000000-0000-4000-8000-000000000001")
    replacement_id = UUID("a0000000-0000-4000-8000-000000000002")
    create_world(store, _packages(), world_id=world_id)
    trace = PlayerInputStepTrace(
        trace_schema_version=1,
        player_input_id=UUID("a0000000-0000-4000-8000-000000000003"),
        interpretation=_result(),
        completion=ThoughtOnlyCompletion(completion_type="thought_only"),
    )
    with store.unit_of_work() as unit:
        unit.player_input_traces.append(
            world_id=world_id,
            observed_world_revision=0,
            resulting_world_revision=0,
            trace=trace,
        )
        unit.commit()
    reset_world_for_development(store, _packages(), world_id=replacement_id)
    with store.unit_of_work() as unit:
        assert unit.player_input_traces.list_for_world(world_id) == ()


def test_v2_to_v3_migration_retains_real_actor_action_trace(tmp_path: Path) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    world_id = UUID("b0000000-0000-4000-8000-000000000001")
    create_world(store, _packages(), world_id=world_id)
    completed = _complete_wait_step(store, world_id)
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE player_input_step_traces")
        connection.execute("DROP TABLE scheduled_activity_execution_traces")
        connection.execute("PRAGMA user_version = 2")
    migrated = SQLiteStore.open(database)
    with migrated.unit_of_work() as unit:
        assert unit.traces.list_for_world(world_id)[0].trace == completed.trace
        assert unit.player_input_traces.list_for_world(world_id) == ()
