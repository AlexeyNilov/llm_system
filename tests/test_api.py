import sqlite3
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute

from llm_system.api import create_app
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import SQLiteStore

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "game_packages"
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")
PROPOSAL_ID = UUID("00000000-0000-4000-8000-000000000002")
STEP_ID = UUID("00000000-0000-4000-8000-000000000003")
CONTEXT_ID = UUID("00000000-0000-4000-8000-000000000004")
OUTCOME_ID = UUID("00000000-0000-4000-8000-000000000005")
EVENT_ID = UUID("00000000-0000-4000-8000-000000000006")
REPLACEMENT_WORLD_ID = UUID("00000000-0000-4000-8000-000000000007")


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
    assert body["simulation_step_id"] == str(STEP_ID)
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


def test_application_registers_exactly_the_four_accepted_http_operations(
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
    }
    assert app.openapi()["paths"].keys() == {
        "/world",
        "/development/reset",
        "/turn",
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
