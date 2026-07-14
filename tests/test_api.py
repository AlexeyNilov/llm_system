import sqlite3
import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute
from pydantic import BaseModel

from llm_system.application import (
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    NarrationStyleOutput,
    OperationalScheduledActivityResult,
    PlayerInterpreterOutput,
)
from llm_system.api import create_app
from llm_system.functional_generation import FunctionalModelGateway, ModelMessage
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.narration import (
    NarrationObserverError,
    NarrationStyleSection,
    NarrationStyleVoice,
)
from llm_system.persistence import SQLiteStore
from llm_system.simulation import (
    NpcScheduledActivity,
    ScheduledActivityQueue,
    WaitActionProposal,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "game_packages"
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")
PROPOSAL_ID = UUID("00000000-0000-4000-8000-000000000002")
STEP_ID = UUID("00000000-0000-4000-8000-000000000003")
CONTEXT_ID = UUID("00000000-0000-4000-8000-000000000004")
OUTCOME_ID = UUID("00000000-0000-4000-8000-000000000005")
EVENT_ID = UUID("00000000-0000-4000-8000-000000000006")
REPLACEMENT_WORLD_ID = UUID("00000000-0000-4000-8000-000000000007")


class FakeGateway(FunctionalModelGateway):
    def __init__(self, output: PlayerInterpreterOutput) -> None:
        self._output = output
        self.calls: list[tuple[ModelMessage, ...]] = []
        self.output_models: list[type[BaseModel]] = []

    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]:
        self.calls.append(messages)
        self.output_models.append(output_model)
        if output_model is NarrationStyleOutput:
            prompt_context = json.loads(messages[-1].content)
            sections = [NarrationStyleSection.LOCATION]
            if prompt_context["co_located_character_names"]:
                sections.append(NarrationStyleSection.CHARACTERS)
            if prompt_context["visible_object_names"]:
                sections.append(NarrationStyleSection.OBJECTS)
            sections.append(NarrationStyleSection.CONNECTIONS)
            style = NarrationStyleOutput(
                voice=NarrationStyleVoice.DIRECT, section_order=tuple(sections)
            )
            return FunctionalGenerationResult[ResultT](
                disposition=FunctionalGenerationDisposition.ACCEPTED,
                value=cast(ResultT, style),
                initial_attempt=FunctionalGenerationAttempt(
                    content=json.dumps(style.model_dump(mode="json")),
                    finish_reason="stop",
                ),
            )
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


class NarrationFailingGateway(FakeGateway):
    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]:
        if output_model is NarrationStyleOutput:
            self.calls.append(messages)
            self.output_models.append(output_model)
            return FunctionalGenerationResult[ResultT](
                disposition=FunctionalGenerationDisposition.FAILED,
                initial_attempt=FunctionalGenerationAttempt(
                    failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
                ),
            )
        return super().generate_functional(messages, output_model)


def _player_turn_identities() -> Iterator[UUID]:
    for number in range(1, 20):
        yield UUID(f"00000000-0000-4000-8000-{number:012d}")


def _packages() -> ValidatedGamePackages:
    rule = load_game_package(PACKAGE_ROOT / "rules/greybridge-rules/0.2.0")
    scenario = load_game_package(PACKAGE_ROOT / "scenarios/storm-at-greybridge/0.2.0")
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


class IdentityFactory:
    def __init__(self, *values: UUID) -> None:
        self._values = iter(values)
        self.calls = 0

    def __call__(self) -> UUID:
        self.calls += 1
        return next(self._values)


def test_create_world_assigns_identity_and_returns_only_lifecycle_metadata(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = IdentityFactory(WORLD_ID)
    app = create_app(
        store=store,
        package_root=PACKAGE_ROOT,
        initial_packages=_packages(),
        identity_factory=identities,
    )

    with store.unit_of_work() as unit:
        assert unit.worlds.get() is None

    response = TestClient(app).post("/world")

    assert response.status_code == 200
    assert response.json() == {
        "world_id": str(WORLD_ID),
        "revision": 0,
        "simulation_time_seconds": 0,
        "rule_package": {
            "package_id": "greybridge-rules",
            "package_version": "0.2.0",
        },
        "scenario_package": {
            "package_id": "storm-at-greybridge",
            "package_version": "0.2.0",
        },
    }


def test_lifecycle_errors_and_resume_are_bounded_and_non_mutating(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    identities = IdentityFactory(WORLD_ID, REPLACEMENT_WORLD_ID)
    app = create_app(
        store=store,
        package_root=PACKAGE_ROOT,
        initial_packages=_packages(),
        identity_factory=identities,
    )
    client = TestClient(app)

    missing = client.get("/world")
    disabled_reset = client.post("/development/reset")
    created = client.post("/world")
    duplicate = client.post("/world")
    reopened = TestClient(
        create_app(
            store=SQLiteStore.open(database),
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
        )
    ).get("/world")

    assert missing.status_code == 404
    assert missing.json() == {"code": "world-not-found"}
    assert disabled_reset.status_code == 403
    assert disabled_reset.json() == {"code": "development-reset-disabled"}
    assert created.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json() == {"code": "world-already-exists"}
    assert reopened.json() == created.json()
    assert identities.calls == 2
    with SQLiteStore.open(database).unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.world_id == WORLD_ID
        assert world.revision == 0
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert unit.traces.list_for_world(WORLD_ID) == ()


def test_turn_owns_trusted_metadata_and_returns_player_safe_completion(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = IdentityFactory(
        WORLD_ID,
        PROPOSAL_ID,
        STEP_ID,
        CONTEXT_ID,
        OUTCOME_ID,
        EVENT_ID,
    )
    app = create_app(
        store=store,
        package_root=PACKAGE_ROOT,
        initial_packages=_packages(),
        identity_factory=identities,
    )
    client = TestClient(app)
    assert client.post("/world").status_code == 200

    response = client.post(
        "/turn",
        json={"proposal": {"operation": "wait", "duration_seconds": 5}},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "world_id",
        "resulting_world_revision",
        "simulation_step_id",
        "outcome_status",
        "reason_code",
        "current_perception",
        "self_event_feedback",
    }
    assert body["world_id"] == str(WORLD_ID)
    assert body["resulting_world_revision"] == 1
    assert UUID(body["simulation_step_id"])
    assert body["outcome_status"] == "succeeded"
    assert body["reason_code"] == "wait-completed"
    assert body["current_perception"]["observer_id"] == "player"
    assert body["current_perception"]["perceived_at_seconds"] == 5
    assert len(body["self_event_feedback"]) == 1
    assert identities.calls == 6

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        traces = unit.traces.list_for_world(WORLD_ID)
        events = unit.events.list_for_world(WORLD_ID)
    assert world.revision == 1
    assert world.state.simulation_time_seconds == 5
    assert len(traces) == 1
    trace = traces[0].trace
    assert trace.submission.proposal_id == PROPOSAL_ID
    assert trace.submission.simulation_step_id == STEP_ID
    assert trace.submission.decision_context_id == CONTEXT_ID
    assert trace.submission.actor_id == "player"
    assert trace.submission.source.source_type == "player_interpreter"
    assert trace.submission.source.interpreter_id == "structured-api"
    assert trace.outcome.outcome_id == OUTCOME_ID
    assert len(events) == 1
    assert events[0].event.event_id == EVENT_ID


def test_rejected_turn_is_a_durable_http_success(tmp_path: Path) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = IdentityFactory(
        WORLD_ID,
        PROPOSAL_ID,
        STEP_ID,
        CONTEXT_ID,
        OUTCOME_ID,
        EVENT_ID,
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=identities,
        )
    )
    client.post("/world")

    response = client.post(
        "/turn",
        json={
            "proposal": {
                "operation": "move",
                "connection_id": "far-bank-to-span",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["outcome_status"] == "rejected"
    assert response.json()["reason_code"] == "actor-not-at-connection-source"
    assert response.json()["resulting_world_revision"] == 1
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert len(unit.traces.list_for_world(WORLD_ID)) == 1


PROPOSALS = (
    {"operation": "observe", "target": {"target_type": "surroundings"}},
    {"operation": "move", "connection_id": "waystation-to-span"},
    {"operation": "speak", "character_id": "injured-courier", "utterance": "Hello"},
    {"operation": "take", "object_id": "reinforcement-materials"},
    {
        "operation": "use",
        "object_id": "reinforcement-materials",
        "target": {"target_type": "location", "location_id": "greybridge-span"},
    },
    {"operation": "help", "character_id": "injured-courier"},
    {"operation": "wait", "duration_seconds": 1},
)


@pytest.mark.parametrize("proposal", PROPOSALS)
def test_each_proposal_variant_validates_before_missing_world_mapping(
    tmp_path: Path, proposal: dict[str, object]
) -> None:
    identities = IdentityFactory(PROPOSAL_ID)
    client = TestClient(
        create_app(
            store=SQLiteStore.open(tmp_path / "world.sqlite3"),
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=identities,
        )
    )

    response = client.post("/turn", json={"proposal": proposal})

    assert response.status_code == 404
    assert response.json() == {"code": "world-not-found"}
    assert identities.calls == 0


@pytest.mark.parametrize(
    "body",
    [
        {"proposal": {"operation": "unknown"}},
        {"proposal": {"operation": "wait", "duration_seconds": 0}},
        {"proposal": {"operation": "wait", "duration_seconds": 1, "extra": True}},
        {
            "proposal": {"operation": "wait", "duration_seconds": 1},
            "actor_id": "player",
        },
        {
            "proposal": {"operation": "wait", "duration_seconds": 1},
            "proposal_id": str(PROPOSAL_ID),
        },
    ],
)
def test_turn_rejects_malformed_or_trusted_client_fields(
    tmp_path: Path, body: dict[str, object]
) -> None:
    client = TestClient(
        create_app(
            store=SQLiteStore.open(tmp_path / "world.sqlite3"),
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
        )
    )

    assert client.post("/turn", json=body).status_code == 422


def test_turn_openapi_exposes_only_the_discriminated_proposal_union(
    tmp_path: Path,
) -> None:
    schema = create_app(
        store=SQLiteStore.open(tmp_path / "world.sqlite3"),
        package_root=PACKAGE_ROOT,
        initial_packages=_packages(),
    ).openapi()

    turn_request = schema["components"]["schemas"]["TurnRequest"]
    assert set(turn_request["properties"]) == {"proposal"}
    proposal = turn_request["properties"]["proposal"]
    assert proposal["discriminator"]["propertyName"] == "operation"
    assert set(proposal["discriminator"]["mapping"]) == {
        "observe",
        "move",
        "speak",
        "take",
        "use",
        "help",
        "wait",
    }
    encoded = str(turn_request)
    for forbidden in (
        "actor_id",
        "source",
        "proposal_id",
        "simulation_step_id",
        "decision_context_id",
        "outcome_id",
        "event_id",
    ):
        assert forbidden not in encoded


@pytest.mark.parametrize(
    ("output", "expected_type", "expected_status"),
    [
        (
            PlayerInterpreterOutput(
                result_type="interpreted",
                private_thought="I should consider this.",
                proposal=None,
                clarification=None,
            ),
            "thought_only",
            200,
        ),
        (
            PlayerInterpreterOutput(
                result_type="clarification",
                private_thought=None,
                proposal=None,
                clarification="Which direction do you mean?",
            ),
            "clarification",
            200,
        ),
        (
            PlayerInterpreterOutput(
                result_type="interpreted",
                private_thought="I will wait.",
                proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                clarification=None,
            ),
            "action_completed",
            200,
        ),
    ],
)
def test_player_turn_maps_each_committed_coordinator_result(
    tmp_path: Path,
    output: PlayerInterpreterOutput,
    expected_type: str,
    expected_status: int,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=FakeGateway(output),
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I act."})

    assert response.status_code == expected_status
    assert response.json()["result_type"] == expected_type
    if expected_type == "action_completed":
        assert set(response.json()) == {
            "result_type",
            "world_id",
            "resulting_world_revision",
            "simulation_step_id",
            "outcome_status",
            "reason_code",
            "current_perception",
            "self_event_feedback",
            "private_thought",
            "narration",
        }
        assert response.json()["outcome_status"] == "succeeded"


def test_player_turn_action_completion_returns_final_player_state(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I will wait.",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
            clarification=None,
        )
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=gateway,
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I wait."})

    assert response.status_code == 200
    assert response.json()["result_type"] == "action_completed"
    assert response.json()["resulting_world_revision"] == 2
    assert response.json()["current_perception"]["perceived_at_seconds"] == 61
    assert gateway.output_models.count(PlayerInterpreterOutput) == 1


def test_player_turn_keeps_committed_result_when_narration_context_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()

    def raise_context_error(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise NarrationObserverError("forced narration context failure")

    monkeypatch.setattr(
        "llm_system.api.build_player_narration_context", raise_context_error
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=FakeGateway(
                PlayerInterpreterOutput(
                    result_type="interpreted",
                    private_thought="I will wait.",
                    proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                    clarification=None,
                )
            ),
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I wait."})

    assert response.status_code == 200
    body = response.json()
    assert body["result_type"] == "action_completed"
    assert body["world_id"] == str(WORLD_ID)
    assert body["resulting_world_revision"] == 2
    assert UUID(body["simulation_step_id"])
    assert body["outcome_status"] == "succeeded"
    assert body["reason_code"] == "wait-completed"
    assert body["private_thought"] == "I will wait."
    assert body["narration"] == "World description unavailable."
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 2


def test_player_turn_keeps_committed_result_when_style_generation_fails(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    gateway = NarrationFailingGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I will wait.",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
            clarification=None,
        )
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=gateway,
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I wait."})

    assert response.status_code == 200
    body = response.json()
    assert body["result_type"] == "action_completed"
    assert body["resulting_world_revision"] == 2
    assert body["narration"] == (
        "You are at Greybridge Waystation. Nearby: Injured Courier, Bridge Caretaker. "
        "Visible objects: Reinforcement Materials. Exits: Waystation to Span (available)."
    )
    assert gateway.output_models == [PlayerInterpreterOutput, NarrationStyleOutput]


def test_player_turn_pending_progress_exposes_only_committed_action_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    monkeypatch.setattr(
        "llm_system.application.player_turn_coordinator.coordinate_due_npc_activity",
        lambda *args, **kwargs: OperationalScheduledActivityResult(
            result_type="operational_failure"
        ),
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=FakeGateway(
                PlayerInterpreterOutput(
                    result_type="interpreted",
                    private_thought="I will wait.",
                    proposal=WaitActionProposal(operation="wait", duration_seconds=1),
                    clarification=None,
                )
            ),
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I wait."})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "result_type",
        "world_id",
        "resulting_world_revision",
        "simulation_step_id",
        "outcome_status",
        "reason_code",
        "current_perception",
        "self_event_feedback",
        "private_thought",
        "narration",
    }
    assert body["result_type"] == "action_progress_pending"
    assert body["resulting_world_revision"] == 1
    for scheduler_internal in (
        "activity_id",
        "npc_id",
        "scheduled_queue",
        "selected_at_seconds",
        "scheduled_activity",
    ):
        assert scheduler_internal not in body


def test_player_turn_settles_pending_progress_before_interpreting_later_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I will wait.",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
            clarification=None,
        )
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=gateway,
        )
    )
    assert client.post("/world").status_code == 200
    assert (
        client.post("/player-turn", json={"player_text": "I wait."}).json()[
            "result_type"
        ]
        == "action_completed"
    )
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

    response = client.post("/player-turn", json={"player_text": "discard this"})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "result_type",
        "world_id",
        "resulting_world_revision",
        "current_perception",
        "narration",
    }
    assert body["result_type"] == "scheduled_progress_completed"
    assert body["resulting_world_revision"] == 4
    assert body["current_perception"]["perceived_at_seconds"] == 121
    assert gateway.output_models.count(PlayerInterpreterOutput) == 1
    with store.unit_of_work() as unit:
        assert len(unit.player_input_traces.list_for_world(WORLD_ID)) == 1


def test_player_turn_reports_pending_progress_without_interpreting_later_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    gateway = FakeGateway(
        PlayerInterpreterOutput(
            result_type="interpreted",
            private_thought="I will wait.",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
            clarification=None,
        )
    )
    monkeypatch.setattr(
        "llm_system.application.player_turn_coordinator.coordinate_due_npc_activity",
        lambda *args, **kwargs: OperationalScheduledActivityResult(
            result_type="operational_failure"
        ),
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=gateway,
        )
    )
    assert client.post("/world").status_code == 200
    assert (
        client.post("/player-turn", json={"player_text": "I wait."}).json()[
            "result_type"
        ]
        == "action_progress_pending"
    )

    response = client.post("/player-turn", json={"player_text": "discard this"})

    assert response.status_code == 200
    assert response.json() == {"result_type": "scheduled_progress_pending"}
    assert gateway.output_models.count(PlayerInterpreterOutput) == 1
    with store.unit_of_work() as unit:
        assert len(unit.player_input_traces.list_for_world(WORLD_ID)) == 1


def test_player_turn_stale_is_bounded_and_does_not_claim_completion(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
            gateway=StaleMakingGateway(
                PlayerInterpreterOutput(
                    result_type="interpreted",
                    private_thought="I should wait.",
                    proposal=None,
                    clarification=None,
                ),
                store,
            ),
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I wait."})

    assert response.status_code == 409
    assert response.json() == {"code": "player-turn-stale"}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"player_text": "   "},
        {"player_text": "I wait.", "actor_id": "player"},
        {"player_text": "I wait.", "revision": 0},
    ],
)
def test_player_turn_rejects_malformed_or_trusted_client_fields(
    tmp_path: Path, body: dict[str, object]
) -> None:
    client = TestClient(
        create_app(
            store=SQLiteStore.open(tmp_path / "world.sqlite3"),
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
        )
    )

    assert client.post("/player-turn", json=body).status_code == 422


def test_player_turn_without_a_gateway_returns_the_safe_clarification(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = _player_turn_identities()
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=lambda: next(identities),
        )
    )
    assert client.post("/world").status_code == 200

    response = client.post("/player-turn", json={"player_text": "I wait."})

    assert response.status_code == 200
    assert response.json() == {
        "result_type": "clarification",
        "clarification": "I couldn't interpret that safely. Please clarify your intended thought or action.",
    }


def test_application_registers_exactly_the_five_accepted_http_operations(
    tmp_path: Path,
) -> None:
    app = create_app(
        store=SQLiteStore.open(tmp_path / "world.sqlite3"),
        package_root=PACKAGE_ROOT,
        initial_packages=_packages(),
    )

    operations = {
        (route.path, method)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods or set()
    }

    assert operations == {
        ("/world", "POST"),
        ("/world", "GET"),
        ("/development/reset", "POST"),
        ("/turn", "POST"),
        ("/player-turn", "POST"),
    }
    assert app.openapi()["paths"].keys() == {
        "/world",
        "/development/reset",
        "/turn",
        "/player-turn",
    }


def test_enabled_reset_assigns_identity_and_clears_the_timeline(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    identities = IdentityFactory(
        WORLD_ID,
        PROPOSAL_ID,
        STEP_ID,
        CONTEXT_ID,
        OUTCOME_ID,
        EVENT_ID,
        REPLACEMENT_WORLD_ID,
    )
    client = TestClient(
        create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=_packages(),
            identity_factory=identities,
            development_reset_enabled=True,
        )
    )
    client.post("/world")
    client.post(
        "/turn", json={"proposal": {"operation": "wait", "duration_seconds": 1}}
    )

    response = client.post("/development/reset")

    assert response.status_code == 200
    assert response.json()["world_id"] == str(REPLACEMENT_WORLD_ID)
    assert response.json()["revision"] == 0
    assert response.json()["simulation_time_seconds"] == 0
    with store.unit_of_work() as unit:
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert unit.traces.list_for_world(WORLD_ID) == ()
        replacement = unit.worlds.get()
        assert replacement is not None
        assert replacement.world_id == REPLACEMENT_WORLD_ID


def test_reset_replacement_insert_failure_is_an_unmapped_500_and_rolls_back(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    identities = IdentityFactory(
        WORLD_ID,
        PROPOSAL_ID,
        STEP_ID,
        CONTEXT_ID,
        OUTCOME_ID,
        EVENT_ID,
        REPLACEMENT_WORLD_ID,
    )
    app = create_app(
        store=store,
        package_root=PACKAGE_ROOT,
        initial_packages=_packages(),
        identity_factory=identities,
        development_reset_enabled=True,
    )
    setup_client = TestClient(app)
    assert setup_client.post("/world").status_code == 200
    assert (
        setup_client.post(
            "/turn",
            json={"proposal": {"operation": "wait", "duration_seconds": 1}},
        ).status_code
        == 200
    )
    with store.unit_of_work() as unit:
        prior_world = unit.worlds.get()
        prior_events = unit.events.list_for_world(WORLD_ID)
        prior_traces = unit.traces.list_for_world(WORLD_ID)
    assert prior_world is not None
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_replacement_world
            BEFORE INSERT ON current_world
            BEGIN
                SELECT RAISE(ABORT, 'replacement rejected');
            END
            """
        )

    response = TestClient(app, raise_server_exceptions=False).post("/development/reset")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    with SQLiteStore.open(database).unit_of_work() as unit:
        assert unit.worlds.get() == prior_world
        assert unit.events.list_for_world(WORLD_ID) == prior_events
        assert unit.traces.list_for_world(WORLD_ID) == prior_traces
    resumed = TestClient(app).get("/world")
    assert resumed.status_code == 200
    assert resumed.json()["world_id"] == str(WORLD_ID)
    assert resumed.json()["revision"] == 1
    assert resumed.json()["simulation_time_seconds"] == 1


def test_unexpected_service_failure_uses_the_normal_server_error(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    app = create_app(
        store=store,
        package_root=tmp_path / "missing-packages",
        initial_packages=_packages(),
        identity_factory=IdentityFactory(WORLD_ID),
    )
    setup_client = TestClient(app)
    assert setup_client.post("/world").status_code == 200

    response = TestClient(app, raise_server_exceptions=False).get("/world")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
