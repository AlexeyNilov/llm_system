from collections.abc import Iterator
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from pydantic import BaseModel

from llm_system.application import (
    CourierPolicyOutput,
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    ModelMessage,
    NpcDecisionContext,
    UnsupportedScheduledActivityError,
    coordinate_due_npc_activity,
    create_world,
)
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import SQLiteStore
from llm_system.simulation import (
    CourierScheduledActivityExecutionTrace,
    EnvironmentalScheduledActivity,
    NpcScheduledActivity,
    ScheduledActivityQueue,
    WaitActionProposal,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")
CARETAKER_ACTIVITY_ID = UUID("00000000-0000-4000-8000-000000000002")
SECOND_ACTIVITY_ID = UUID("00000000-0000-4000-8000-000000000003")


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


def _store(tmp_path: Path, queue: ScheduledActivityQueue) -> SQLiteStore:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, _packages(), world_id=WORLD_ID)
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        unit.worlds.replace(
            world_id=world.world_id,
            expected_revision=world.revision,
            state=world.state,
            scheduled_queue=queue,
        )
        unit.commit()
    return store


def _caretaker_activity() -> NpcScheduledActivity:
    return NpcScheduledActivity(
        activity_type="npc",
        activity_id=CARETAKER_ACTIVITY_ID,
        eligible_at_seconds=0,
        insertion_sequence=0,
        npc_id="bridge-caretaker",
    )


def _courier_activity() -> NpcScheduledActivity:
    return NpcScheduledActivity(
        activity_type="npc",
        activity_id=CARETAKER_ACTIVITY_ID,
        eligible_at_seconds=0,
        insertion_sequence=0,
        npc_id="injured-courier",
    )


class CourierGateway:
    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        result = FunctionalGenerationResult[CourierPolicyOutput](
            disposition=FunctionalGenerationDisposition.ACCEPTED,
            value=CourierPolicyOutput(
                proposal=WaitActionProposal(operation="wait", duration_seconds=60)
            ),
            initial_attempt=FunctionalGenerationAttempt(
                content='{"proposal":{"operation":"wait","duration_seconds":60}}',
                finish_reason="stop",
            ),
        )
        return cast(FunctionalGenerationResult[ResultT], result)


class FailedCourierGateway:
    def __init__(
        self, generation: FunctionalGenerationResult[CourierPolicyOutput]
    ) -> None:
        self.generation = generation

    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        return cast(FunctionalGenerationResult[ResultT], self.generation)


class RaisingCourierGateway:
    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        raise RuntimeError("unavailable")


def _identities() -> Iterator[UUID]:
    for number in range(10, 30):
        yield UUID(f"00000000-0000-4000-8000-{number:012d}")


def test_no_due_activity_is_a_typed_no_write_result(tmp_path: Path) -> None:
    future = NpcScheduledActivity(
        activity_type="npc",
        activity_id=CARETAKER_ACTIVITY_ID,
        eligible_at_seconds=1,
        insertion_sequence=0,
        npc_id="bridge-caretaker",
    )
    store = _store(tmp_path, ScheduledActivityQueue(activities=(future,)))

    result = coordinate_due_npc_activity(
        store,
        _packages(),
        CourierGateway(),
        identity_factory=lambda: (_ for _ in ()).throw(AssertionError("no id")),
    )

    assert result.result_type == "no_activity"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert world.scheduled_queue.activities == (future,)
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert unit.scheduled_activity_traces.list_for_world(WORLD_ID) == ()


def test_due_caretaker_activity_is_consumed_with_linked_action_and_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    second = NpcScheduledActivity(
        activity_type="npc",
        activity_id=SECOND_ACTIVITY_ID,
        eligible_at_seconds=0,
        insertion_sequence=1,
        npc_id="bridge-caretaker",
    )
    store = _store(
        tmp_path, ScheduledActivityQueue(activities=(_caretaker_activity(), second))
    )
    identities = _identities()
    contexts: list[NpcDecisionContext] = []

    def capture_context(context: NpcDecisionContext) -> object:
        contexts.append(context)
        from llm_system.simulation import WaitActionProposal

        return WaitActionProposal(operation="wait", duration_seconds=60)

    monkeypatch.setattr(
        "llm_system.application.scheduled_execution_coordinator.decide_greybridge_caretaker",
        capture_context,
    )

    result = coordinate_due_npc_activity(
        store, _packages(), CourierGateway(), identity_factory=lambda: next(identities)
    )

    assert result.result_type == "completed"
    assert result.completed_action.resulting_world_revision == 2
    assert len(contexts) == 1
    assert (
        contexts[0].decision_context_id
        == result.completed_action.trace.decision_context_id
    )
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.scheduled_queue.activities == (second,)
        traces = unit.scheduled_activity_traces.list_for_world(WORLD_ID)
        assert len(traces) == 1
        assert traces[0].trace.activity == _caretaker_activity()
        assert traces[0].trace.selected_at_seconds == 0
        assert (
            traces[0].trace.simulation_step_id
            == result.completed_action.trace.simulation_step_id
        )
        assert traces[0].resulting_world_revision == world.revision
        assert len(unit.traces.list_for_world(WORLD_ID)) == 1


def test_due_courier_activity_commits_linked_generation_evidence(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path, ScheduledActivityQueue(activities=(_courier_activity(),)))

    result = coordinate_due_npc_activity(
        store,
        _packages(),
        CourierGateway(),
        identity_factory=_identities().__next__,
    )

    assert result.result_type == "completed"
    with store.unit_of_work() as unit:
        traces = unit.scheduled_activity_traces.list_for_world(WORLD_ID)
        assert len(traces) == 1
        assert traces[0].trace.activity == _courier_activity()
        assert isinstance(traces[0].trace, CourierScheduledActivityExecutionTrace)
        assert (
            traces[0].trace.result.proposal
            == result.completed_action.trace.submission.proposal
        )
        assert (
            traces[0].trace.decision_context_id
            == result.completed_action.trace.decision_context_id
        )


def test_failed_courier_generation_commits_wait_fallback_and_exact_evidence(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path, ScheduledActivityQueue(activities=(_courier_activity(),)))
    generation = FunctionalGenerationResult[CourierPolicyOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(
            failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
        ),
    )

    result = coordinate_due_npc_activity(
        store,
        _packages(),
        FailedCourierGateway(generation),
        identity_factory=_identities().__next__,
    )

    assert result.result_type == "completed"
    assert result.completed_action.trace.submission.proposal == WaitActionProposal(
        operation="wait", duration_seconds=60
    )
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.scheduled_queue.activities == ()
        traces = unit.scheduled_activity_traces.list_for_world(WORLD_ID)
        assert len(traces) == 1
        assert isinstance(traces[0].trace, CourierScheduledActivityExecutionTrace)
        assert traces[0].trace.result.generation == generation


def test_courier_gateway_exception_leaves_every_persistent_record_unchanged(
    tmp_path: Path,
) -> None:
    activity = _courier_activity()
    store = _store(tmp_path, ScheduledActivityQueue(activities=(activity,)))

    result = coordinate_due_npc_activity(
        store,
        _packages(),
        RaisingCourierGateway(),
        identity_factory=_identities().__next__,
    )

    assert result.result_type == "operational_failure"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert world.scheduled_queue.activities == (activity,)
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert unit.scheduled_activity_traces.list_for_world(WORLD_ID) == ()


def test_unsupported_first_due_activity_fails_without_consuming_or_skipping(
    tmp_path: Path,
) -> None:
    unsupported = EnvironmentalScheduledActivity(
        activity_type="environmental",
        activity_id=CARETAKER_ACTIVITY_ID,
        eligible_at_seconds=0,
        insertion_sequence=0,
        schedule_id="storm-intensifies",
    )
    store = _store(
        tmp_path,
        ScheduledActivityQueue(
            activities=(
                unsupported,
                NpcScheduledActivity(
                    activity_type="npc",
                    activity_id=SECOND_ACTIVITY_ID,
                    eligible_at_seconds=0,
                    insertion_sequence=1,
                    npc_id="bridge-caretaker",
                ),
            )
        ),
    )

    with pytest.raises(UnsupportedScheduledActivityError):
        coordinate_due_npc_activity(
            store,
            _packages(),
            CourierGateway(),
            identity_factory=lambda: (_ for _ in ()).throw(AssertionError("no id")),
        )

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert world.scheduled_queue.activities == (
            unsupported,
            NpcScheduledActivity(
                activity_type="npc",
                activity_id=SECOND_ACTIVITY_ID,
                eligible_at_seconds=0,
                insertion_sequence=1,
                npc_id="bridge-caretaker",
            ),
        )
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert unit.scheduled_activity_traces.list_for_world(WORLD_ID) == ()


def test_stale_due_selection_assigns_no_submission_identities_or_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(
        tmp_path, ScheduledActivityQueue(activities=(_caretaker_activity(),))
    )

    def make_stale(context: object) -> object:
        with store.unit_of_work() as unit:
            world = unit.worlds.get()
            assert world is not None
            unit.worlds.replace(
                world_id=world.world_id,
                expected_revision=world.revision,
                state=world.state,
                scheduled_queue=world.scheduled_queue,
            )
            unit.commit()
        from llm_system.simulation import WaitActionProposal

        return WaitActionProposal(operation="wait", duration_seconds=60)

    monkeypatch.setattr(
        "llm_system.application.scheduled_execution_coordinator.decide_greybridge_caretaker",
        make_stale,
    )

    result = coordinate_due_npc_activity(
        store,
        _packages(),
        CourierGateway(),
        identity_factory=iter((UUID("00000000-0000-4000-8000-000000000010"),)).__next__,
    )

    assert result.result_type == "stale"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 2
        assert world.scheduled_queue.activities == (_caretaker_activity(),)
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert unit.scheduled_activity_traces.list_for_world(WORLD_ID) == ()


def test_operational_policy_failure_preserves_the_due_activity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(
        tmp_path, ScheduledActivityQueue(activities=(_caretaker_activity(),))
    )

    def fail_policy(context: object) -> object:
        raise RuntimeError("unavailable")

    monkeypatch.setattr(
        "llm_system.application.scheduled_execution_coordinator.decide_greybridge_caretaker",
        fail_policy,
    )

    result = coordinate_due_npc_activity(
        store, _packages(), CourierGateway(), identity_factory=_identities().__next__
    )

    assert result.result_type == "operational_failure"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert world.scheduled_queue.activities == (_caretaker_activity(),)
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert unit.scheduled_activity_traces.list_for_world(WORLD_ID) == ()
