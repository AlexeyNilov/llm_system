import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast
from uuid import UUID

from pydantic import BaseModel
import pytest

from llm_system.application import (
    ActionCompletedPlayerTurnResult,
    CompletedScheduledActivityResult,
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    PlayerInterpreterOutput,
    StaleScheduledActivityResult,
    coordinate_player_turn,
    create_world,
)
from llm_system.functional_generation import FunctionalModelGateway, ModelMessage
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import DuplicatePlayerInputIdentityError, SQLiteStore
from llm_system.player_input_traces import ActionLinkedCompletion
from llm_system.simulation import (
    MoveActionProposal,
    NpcScheduledActivity,
    ScheduledActivityQueue,
    WaitActionProposal,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")


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


class FakeGateway(FunctionalModelGateway):
    def __init__(self, output: PlayerInterpreterOutput) -> None:
        self._output = output
        self.calls: list[tuple[ModelMessage, ...]] = []

    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]:
        self.calls.append(messages)
        return FunctionalGenerationResult[ResultT](
            disposition=FunctionalGenerationDisposition.ACCEPTED,
            value=cast(ResultT, self._output),
            initial_attempt=FunctionalGenerationAttempt(
                content=json.dumps(self._output.model_dump(mode="json")),
                finish_reason="stop",
            ),
        )


class StaleMakingGateway(FakeGateway):
    def __init__(self, output: PlayerInterpreterOutput, store: SQLiteStore) -> None:
        super().__init__(output)
        self._store = store

    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]:
        result = super().generate_functional(messages, output_model)
        with self._store.unit_of_work() as unit:
            world = unit.worlds.get()
            assert world is not None
            unit.worlds.replace(
                world_id=world.world_id,
                expected_revision=world.revision,
                state=world.state,
                scheduled_queue=world.scheduled_queue,
            )
            unit.commit()
        return result


class FailedGateway(FunctionalModelGateway):
    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]:
        return FunctionalGenerationResult[ResultT](
            disposition=FunctionalGenerationDisposition.FAILED,
            initial_attempt=FunctionalGenerationAttempt(
                failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
            ),
        )


def _identities() -> Iterator[UUID]:
    for number in range(2, 20):
        yield UUID(f"00000000-0000-4000-8000-{number:012d}")


def test_thought_only_turn_persists_one_unchanged_revision_trace_after_gateway(
    tmp_path: Path,
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I should wait.",
            proposal=None,
            clarification=None,
        )
    )
    identities = _identities()

    result = coordinate_player_turn(
        store,
        packages,
        gateway,
        player_text="I should wait.",
        player_id="player",
        identity_factory=lambda: next(identities),
    )

    assert result.result_type == "thought_only"
    assert result.private_thought == "I should wait."
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 0
        traces = unit.player_input_traces.list_for_world(WORLD_ID)
    assert len(traces) == 1
    assert traces[0].observed_world_revision == 0
    assert traces[0].resulting_world_revision == 0
    assert traces[0].trace.interpretation.player_text == "I should wait."
    assert gateway.calls


def test_action_turn_commits_action_and_linked_input_trace_together(
    tmp_path: Path,
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I need a moment.",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
            clarification=None,
        )
    )
    identities = _identities()

    result = coordinate_player_turn(
        store,
        packages,
        gateway,
        player_text="I think I need a moment, so I wait.",
        player_id="player",
        identity_factory=lambda: next(identities),
    )

    assert result.result_type == "action_completed"
    assert result.private_thought == "I need a moment."
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        action_traces = unit.traces.list_for_world(WORLD_ID)
        input_traces = unit.player_input_traces.list_for_world(WORLD_ID)
    assert world.revision == 2
    assert len(action_traces) == 2
    assert len(input_traces) == 1
    completion = input_traces[0].trace.completion
    assert isinstance(completion, ActionLinkedCompletion)
    assert completion.simulation_step_id == next(
        trace.trace.simulation_step_id
        for trace in action_traces
        if trace.trace.submission.actor_id == "player"
    )


def test_action_turn_settles_one_due_activity_before_returning_final_perception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    activity = NpcScheduledActivity(
        activity_type="npc",
        activity_id=UUID("00000000-0000-4000-8000-000000000099"),
        eligible_at_seconds=0,
        insertion_sequence=0,
        npc_id="bridge-caretaker",
    )
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        unit.worlds.replace(
            world_id=world.world_id,
            expected_revision=world.revision,
            state=world.state,
            scheduled_queue=ScheduledActivityQueue(activities=(activity,)),
        )
        unit.commit()

    monkeypatch.setattr(
        "llm_system.application.scheduled_execution_coordinator.decide_greybridge_caretaker",
        lambda context: WaitActionProposal(operation="wait", duration_seconds=60),
    )
    result = coordinate_player_turn(
        store,
        packages,
        FakeGateway(
            PlayerInterpreterOutput(
                result_type="interpreted",
                private_thought=None,
                proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                clarification=None,
            )
        ),
        player_text="I wait.",
        player_id="player",
        identity_factory=_identities().__next__,
    )

    assert result.result_type == "action_completed"
    assert result.resulting_world_revision == 3
    assert result.current_perception.perceived_at_seconds == 61
    with store.unit_of_work() as unit:
        assert len(unit.player_input_traces.list_for_world(WORLD_ID)) == 1
        assert len(unit.scheduled_activity_traces.list_for_world(WORLD_ID)) == 1


def test_action_turn_returns_pending_after_stale_scheduled_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    monkeypatch.setattr(
        "llm_system.application.player_turn_coordinator.coordinate_due_caretaker_activity",
        lambda *args, **kwargs: StaleScheduledActivityResult(result_type="stale"),
    )

    result = coordinate_player_turn(
        store,
        packages,
        FakeGateway(
            PlayerInterpreterOutput(
                result_type="interpreted",
                private_thought="I wait.",
                proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                clarification=None,
            )
        ),
        player_text="I wait.",
        player_id="player",
        identity_factory=_identities().__next__,
    )

    assert result.result_type == "action_progress_pending"
    assert result.completed_action.resulting_world_revision == 1
    with store.unit_of_work() as unit:
        assert len(unit.player_input_traces.list_for_world(WORLD_ID)) == 1


def test_pending_activity_completes_before_interpreting_later_player_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="unreached",
            proposal=None,
            clarification=None,
        )
    )
    prior_result = coordinate_player_turn(
        store,
        packages,
        FakeGateway(
            PlayerInterpreterOutput(
                result_type="interpreted",
                private_thought=None,
                proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                clarification=None,
            )
        ),
        player_text="I wait.",
        player_id="player",
        identity_factory=_identities().__next__,
    )
    assert isinstance(prior_result, ActionCompletedPlayerTurnResult)
    completed = CompletedScheduledActivityResult(
        result_type="completed",
        completed_action=prior_result.completed_action,
    )
    monkeypatch.setattr(
        "llm_system.application.player_turn_coordinator.coordinate_due_caretaker_activity",
        lambda *args, **kwargs: completed,
    )

    result = coordinate_player_turn(
        store,
        packages,
        gateway,
        player_text="discard this",
        player_id="player",
        identity_factory=lambda: (_ for _ in ()).throw(AssertionError("no identity")),
    )

    assert result.result_type == "scheduled_progress_completed"
    assert gateway.calls == []
    with store.unit_of_work() as unit:
        assert len(unit.player_input_traces.list_for_world(WORLD_ID)) == 1


def test_stale_turn_assigns_no_identity_or_player_input_trace(tmp_path: Path) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    gateway = StaleMakingGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I should wait.",
            proposal=None,
            clarification=None,
        ),
        store,
    )

    result = coordinate_player_turn(
        store,
        packages,
        gateway,
        player_text="I should wait.",
        player_id="player",
        identity_factory=lambda: (_ for _ in ()).throw(AssertionError("no identity")),
    )

    assert result.result_type == "stale"
    with store.unit_of_work() as unit:
        assert unit.player_input_traces.list_for_world(WORLD_ID) == ()


def test_gateway_fallback_clarification_is_durable_without_provider_details(
    tmp_path: Path,
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    identities = _identities()

    result = coordinate_player_turn(
        store,
        packages,
        FailedGateway(),
        player_text="Try something.",
        player_id="player",
        identity_factory=lambda: next(identities),
    )

    assert result.result_type == "clarification"
    assert "service-error" not in result.clarification
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        traces = unit.player_input_traces.list_for_world(WORLD_ID)
    assert world.revision == 0
    assert len(traces) == 1
    assert traces[0].trace.completion.completion_type == "clarification"
    assert traces[0].trace.interpretation.generation.initial_attempt.failure_kind is (
        FunctionalModelFailureKind.SERVICE_ERROR
    )


def test_accepted_clarification_is_durable_at_the_unchanged_revision(
    tmp_path: Path,
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    identities = _identities()
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="clarification",
            private_thought=None,
            proposal=None,
            clarification="Which direction do you mean?",
        )
    )

    result = coordinate_player_turn(
        store,
        packages,
        gateway,
        player_text="Go that way.",
        player_id="player",
        identity_factory=lambda: next(identities),
    )

    assert result.result_type == "clarification"
    assert result.clarification == "Which direction do you mean?"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        traces = unit.player_input_traces.list_for_world(WORLD_ID)
    assert world.revision == 0
    assert len(traces) == 1
    assert traces[0].observed_world_revision == traces[0].resulting_world_revision == 0
    assert traces[0].trace.completion.completion_type == "clarification"


def test_rejected_action_remains_atomic_before_later_scheduled_progress(
    tmp_path: Path,
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    identities = _identities()
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought=None,
            proposal=MoveActionProposal(operation="move", connection_id="missing"),
            clarification=None,
        )
    )

    result = coordinate_player_turn(
        store,
        packages,
        gateway,
        player_text="I go along the missing route.",
        player_id="player",
        identity_factory=lambda: next(identities),
    )

    assert result.result_type == "action_completed"
    assert result.completed_action.trace.outcome.status == "rejected"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        action_traces = unit.traces.list_for_world(WORLD_ID)
        input_traces = unit.player_input_traces.list_for_world(WORLD_ID)
        events = unit.events.list_for_world(WORLD_ID)
    assert world.revision == 2
    assert len(action_traces) == 2
    assert len(input_traces) == 1
    assert len(events) == 1


def test_action_trace_conflict_rolls_back_actor_completion_and_world_replacement(
    tmp_path: Path,
) -> None:
    packages = _packages()
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, packages, world_id=WORLD_ID)
    duplicate_id = UUID("00000000-0000-4000-8000-000000000099")
    coordinate_player_turn(
        store,
        packages,
        FakeGateway(
            PlayerInterpreterOutput(
                result_type="interpreted",
                private_thought="I should wait.",
                proposal=None,
                clarification=None,
            )
        ),
        player_text="I should wait.",
        player_id="player",
        identity_factory=lambda: duplicate_id,
    )
    identities = iter((duplicate_id, *_identities()))

    with pytest.raises(DuplicatePlayerInputIdentityError):
        coordinate_player_turn(
            store,
            packages,
            FakeGateway(
                PlayerInterpreterOutput(
                    result_type="interpreted",
                    private_thought=None,
                    proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                    clarification=None,
                )
            ),
            player_text="I wait.",
            player_id="player",
            identity_factory=lambda: next(identities),
        )

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 0
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert len(unit.player_input_traces.list_for_world(WORLD_ID)) == 1
