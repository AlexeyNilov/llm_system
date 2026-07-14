import json
import sqlite3
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest

from llm_system.persistence import (
    DuplicateEventIdentityError,
    ExistingWorldError,
    PackageReference,
    SQLiteStore,
    StaleWorldRevisionError,
    StoredRecordDecodingError,
    UnitOfWorkFailedError,
    UnsupportedSchemaVersionError,
    WorldRevisionMismatchError,
)
from llm_system.application import (
    CourierPolicyOutput,
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    FunctionalModelGateway,
    coordinate_due_npc_activity,
    create_world,
)
from llm_system.courier_decision import CourierPolicyResult
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.simulation import (
    ActorMovedEvent,
    ActorWaitedEvent,
    CharacterState,
    NpcScheduledActivity,
    CourierScheduledActivityExecutionTrace,
    ScheduledActivityQueue,
    WaitActionProposal,
    WorldState,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORLD_ID = UUID("10000000-0000-4000-8000-000000000001")
MOVE_EVENT_ID = UUID("20000000-0000-4000-8000-000000000001")
WAIT_EVENT_ID = UUID("20000000-0000-4000-8000-000000000002")
OUTCOME_ID = UUID("30000000-0000-4000-8000-000000000001")
ACTIVITY_ID = UUID("40000000-0000-4000-8000-000000000001")
RULE_PACKAGE = PackageReference(package_id="core-rules", package_version="1.2.0")
SCENARIO_PACKAGE = PackageReference(
    package_id="harbor-scenario", package_version="2.0.1"
)


def _world(time_seconds: int, location_id: str = "market") -> WorldState:
    return WorldState(
        simulation_time_seconds=time_seconds,
        characters=(CharacterState(character_id="marin", location_id=location_id),),
        objects=(),
        connections=(),
    )


def _events() -> tuple[ActorMovedEvent, ActorWaitedEvent]:
    return (
        ActorMovedEvent(
            event_type="actor_moved",
            event_id=MOVE_EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=30,
            actor_id="marin",
            connection_id="market-to-dock",
            from_location_id="market",
            to_location_id="dock",
        ),
        ActorWaitedEvent(
            event_type="actor_waited",
            event_id=WAIT_EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=30,
            actor_id="marin",
            duration_seconds=5,
        ),
    )


def _replacement_queue() -> ScheduledActivityQueue:
    return ScheduledActivityQueue(
        activities=(
            NpcScheduledActivity(
                activity_type="npc",
                activity_id=ACTIVITY_ID,
                eligible_at_seconds=45,
                insertion_sequence=7,
                npc_id="sela",
            ),
        )
    )


def _create_world(store: SQLiteStore) -> None:
    with store.unit_of_work() as unit:
        created = unit.worlds.create(
            world_id=WORLD_ID,
            rule_package=RULE_PACKAGE,
            scenario_package=SCENARIO_PACKAGE,
            state=_world(0),
            scheduled_queue=ScheduledActivityQueue(activities=()),
        )
        assert created.revision == 0
        unit.commit()


def _greybridge_packages() -> ValidatedGamePackages:
    rule = load_game_package(
        REPOSITORY_ROOT / "game_packages/rules/greybridge-rules/0.2.0"
    )
    scenario = load_game_package(
        REPOSITORY_ROOT / "game_packages/scenarios/storm-at-greybridge/0.2.0"
    )
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


class _UnusedGateway:
    def generate_functional(self, messages: object, output_model: object) -> object:
        raise AssertionError("caretaker execution must not invoke the gateway")


def test_bootstrap_reopen_and_reject_unsupported_schema_without_modification(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    SQLiteStore.open(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (5,)
        connection.execute("PRAGMA user_version = 6")

    with pytest.raises(UnsupportedSchemaVersionError):
        SQLiteStore.open(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (6,)


def test_v1_world_and_event_migrate_to_v5_without_record_changes(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)
    with store.unit_of_work() as unit:
        unit.events.append(
            world_id=WORLD_ID,
            resulting_world_revision=0,
            events=(_events()[0],),
        )
        unit.commit()
    with sqlite3.connect(database) as connection:
        world_before = connection.execute("SELECT * FROM current_world").fetchone()
        event_before = connection.execute("SELECT * FROM canonical_events").fetchone()
        connection.execute("DROP TABLE simulation_step_traces")
        connection.execute("DROP TABLE player_input_step_traces")
        connection.execute("DROP TABLE scheduled_activity_execution_traces")
        connection.execute("PRAGMA user_version = 1")

    migrated = SQLiteStore.open(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (5,)
        assert (
            connection.execute("SELECT * FROM current_world").fetchone() == world_before
        )
        assert (
            connection.execute("SELECT * FROM canonical_events").fetchone()
            == event_before
        )
    with migrated.unit_of_work() as unit:
        assert unit.worlds.get() is not None
        assert [record.event for record in unit.events.list_for_world(WORLD_ID)] == [
            _events()[0]
        ]
        assert unit.traces.list_for_world(WORLD_ID) == ()


def test_v2_migrates_trace_histories_without_record_changes(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)
    with store.unit_of_work() as unit:
        unit.events.append(
            world_id=WORLD_ID,
            resulting_world_revision=0,
            events=(_events()[0],),
        )
        unit.commit()
    with sqlite3.connect(database) as connection:
        world_before = connection.execute("SELECT * FROM current_world").fetchone()
        event_before = connection.execute("SELECT * FROM canonical_events").fetchone()
        connection.execute("DROP TABLE player_input_step_traces")
        connection.execute("DROP TABLE scheduled_activity_execution_traces")
        connection.execute("PRAGMA user_version = 2")

    SQLiteStore.open(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (5,)
        assert (
            connection.execute("SELECT * FROM current_world").fetchone() == world_before
        )
        assert (
            connection.execute("SELECT * FROM canonical_events").fetchone()
            == event_before
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM simulation_step_traces"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM scheduled_activity_execution_traces"
        ).fetchone() == (0,)


def test_v3_migrates_scheduled_activity_history_without_record_changes(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)
    with sqlite3.connect(database) as connection:
        world_before = connection.execute("SELECT * FROM current_world").fetchone()
        connection.execute("DROP TABLE scheduled_activity_execution_traces")
        connection.execute("PRAGMA user_version = 3")

    SQLiteStore.open(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (5,)
        assert (
            connection.execute("SELECT * FROM current_world").fetchone() == world_before
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM scheduled_activity_execution_traces"
        ).fetchone() == (0,)


def test_v4_migrates_without_rewriting_scheduled_activity_records(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    packages = _greybridge_packages()
    create_world(store, packages, world_id=WORLD_ID)
    identities = iter(
        UUID(f"10000000-0000-4000-8000-{number:012d}") for number in range(10, 20)
    )
    completed = coordinate_due_npc_activity(
        store,
        packages,
        cast(FunctionalModelGateway, _UnusedGateway()),
        identity_factory=identities.__next__,
    )
    assert completed.result_type == "completed"
    with sqlite3.connect(database) as connection:
        scheduled_before = connection.execute(
            "SELECT * FROM scheduled_activity_execution_traces"
        ).fetchall()
        connection.execute("PRAGMA user_version = 4")

    SQLiteStore.open(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (5,)
        assert (
            connection.execute(
                "SELECT * FROM scheduled_activity_execution_traces"
            ).fetchall()
            == scheduled_before
        )
    with SQLiteStore.open(database).unit_of_work() as unit:
        traces = unit.scheduled_activity_traces.list_for_world(WORLD_ID)
        assert len(traces) == 1
        assert traces[0].trace.trace_schema_version == 1


def test_courier_trace_mismatch_with_linked_actor_trace_rolls_back_append(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    packages = _greybridge_packages()
    create_world(store, packages, world_id=WORLD_ID)
    identities = iter(
        UUID(f"20000000-0000-4000-8000-{number:012d}") for number in range(10, 25)
    )
    completed = coordinate_due_npc_activity(
        store,
        packages,
        cast(FunctionalModelGateway, _UnusedGateway()),
        identity_factory=identities.__next__,
    )
    assert completed.result_type == "completed"
    bad_trace = CourierScheduledActivityExecutionTrace(
        trace_schema_version=2,
        activity=NpcScheduledActivity(
            activity_type="npc",
            activity_id=UUID("40000000-0000-4000-8000-000000000002"),
            eligible_at_seconds=0,
            insertion_sequence=1,
            npc_id="injured-courier",
        ),
        selected_at_seconds=0,
        decision_context_id=UUID("30000000-0000-4000-8000-000000000002"),
        simulation_step_id=completed.completed_action.trace.simulation_step_id,
        result=CourierPolicyResult(
            proposal=WaitActionProposal(operation="wait", duration_seconds=60),
            generation=FunctionalGenerationResult[CourierPolicyOutput](
                disposition=FunctionalGenerationDisposition.FAILED,
                initial_attempt=FunctionalGenerationAttempt(
                    failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
                ),
            ),
        ),
    )

    with pytest.raises(StoredRecordDecodingError, match="courier trace"):
        with store.unit_of_work() as unit:
            unit.scheduled_activity_traces.append(
                world_id=completed.completed_action.world_id,
                resulting_world_revision=completed.completed_action.resulting_world_revision,
                trace=bad_trace,
            )
            unit.commit()

    with store.unit_of_work() as unit:
        assert len(unit.scheduled_activity_traces.list_for_world(WORLD_ID)) == 1


def test_create_is_singleton_and_uncommitted_exit_rolls_back(tmp_path: Path) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)

    with store.unit_of_work() as unit:
        assert unit.worlds.get() is None
        unit.worlds.create(
            world_id=WORLD_ID,
            rule_package=RULE_PACKAGE,
            scenario_package=SCENARIO_PACKAGE,
            state=_world(0),
            scheduled_queue=ScheduledActivityQueue(activities=()),
        )

    with store.unit_of_work() as unit:
        assert unit.worlds.get() is None

    _create_world(store)
    with store.unit_of_work() as unit:
        loaded = unit.worlds.get()
        assert loaded is not None
        assert loaded.world_id == WORLD_ID
        assert loaded.revision == 0
        assert loaded.rule_package == RULE_PACKAGE
        assert loaded.scenario_package == SCENARIO_PACKAGE
        assert loaded.state == _world(0)
        assert loaded.scheduled_queue == ScheduledActivityQueue(activities=())
        with pytest.raises(ExistingWorldError):
            unit.worlds.create(
                world_id=UUID("10000000-0000-4000-8000-000000000002"),
                rule_package=RULE_PACKAGE,
                scenario_package=SCENARIO_PACKAGE,
                state=_world(1),
                scheduled_queue=ScheduledActivityQueue(activities=()),
            )


def test_replace_and_same_time_events_recover_in_durable_order(tmp_path: Path) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)

    with store.unit_of_work() as unit:
        replacement = unit.worlds.replace(
            world_id=WORLD_ID,
            expected_revision=0,
            state=_world(30, "dock"),
            scheduled_queue=_replacement_queue(),
        )
        stored_events = unit.events.append(
            world_id=WORLD_ID,
            resulting_world_revision=replacement.revision,
            events=_events(),
        )
        assert [record.insertion_sequence for record in stored_events] == [1, 2]
        unit.commit()

    reopened = SQLiteStore.open(database)
    with reopened.unit_of_work() as unit:
        recovered = unit.worlds.get()
        history = unit.events.list_for_world(WORLD_ID)

    assert recovered is not None
    assert recovered.revision == 1
    assert recovered.rule_package == RULE_PACKAGE
    assert recovered.scenario_package == SCENARIO_PACKAGE
    assert recovered.state == _world(30, "dock")
    assert recovered.scheduled_queue == _replacement_queue()
    recovered_activity = recovered.scheduled_queue.activities[0]
    assert isinstance(recovered_activity, NpcScheduledActivity)
    assert recovered_activity.activity_type == "npc"
    assert recovered_activity.activity_id == ACTIVITY_ID
    assert recovered_activity.eligible_at_seconds == 45
    assert recovered_activity.insertion_sequence == 7
    assert recovered_activity.npc_id == "sela"
    assert [record.event for record in history] == list(_events())
    assert [record.insertion_sequence for record in history] == [1, 2]


def test_failure_rolls_back_world_replacement_and_event_batch(tmp_path: Path) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)

    with pytest.raises(DuplicateEventIdentityError):
        with store.unit_of_work() as unit:
            replacement = unit.worlds.replace(
                world_id=WORLD_ID,
                expected_revision=0,
                state=_world(30, "dock"),
                scheduled_queue=ScheduledActivityQueue(activities=()),
            )
            duplicate = (_events()[0], _events()[0])
            unit.events.append(
                world_id=WORLD_ID,
                resulting_world_revision=replacement.revision,
                events=duplicate,
            )
            unit.commit()

    with store.unit_of_work() as unit:
        recovered = unit.worlds.get()
        assert recovered is not None
        assert recovered.revision == 0
        assert unit.events.list_for_world(WORLD_ID) == ()


def test_stale_or_wrong_event_revision_marks_unit_of_work_for_rollback(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)

    with store.unit_of_work() as unit:
        unit.worlds.replace(
            world_id=WORLD_ID,
            expected_revision=0,
            state=_world(10),
            scheduled_queue=ScheduledActivityQueue(activities=()),
        )
        with pytest.raises(StaleWorldRevisionError):
            unit.worlds.replace(
                world_id=WORLD_ID,
                expected_revision=0,
                state=_world(20),
                scheduled_queue=ScheduledActivityQueue(activities=()),
            )
        with pytest.raises(UnitOfWorkFailedError, match="failed unit of work"):
            unit.commit()

    with store.unit_of_work() as unit:
        recovered = unit.worlds.get()
        assert recovered is not None
        assert recovered.revision == 0
        with pytest.raises(WorldRevisionMismatchError):
            unit.events.append(
                world_id=WORLD_ID,
                resulting_world_revision=1,
                events=_events(),
            )


def test_invalid_or_inconsistent_stored_data_fails_strict_decoding(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE current_world SET state_json = ?",
            (json.dumps({"simulation_time_seconds": "0"}),),
        )

    with store.unit_of_work() as unit:
        with pytest.raises(StoredRecordDecodingError):
            unit.worlds.get()

    database = tmp_path / "events.sqlite3"
    store = SQLiteStore.open(database)
    _create_world(store)
    with store.unit_of_work() as unit:
        unit.events.append(
            world_id=WORLD_ID,
            resulting_world_revision=0,
            events=(_events()[0],),
        )
        unit.commit()
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE canonical_events SET event_type = 'actor_waited'")

    with store.unit_of_work() as unit:
        with pytest.raises(StoredRecordDecodingError):
            unit.events.list_for_world(WORLD_ID)
