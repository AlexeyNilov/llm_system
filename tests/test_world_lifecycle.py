import shutil
import sqlite3
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.application import (
    ActiveWorld,
    build_initial_world,
    create_world,
    execute_actor_action_step,
    reset_world_for_development,
    resume_world,
)
from llm_system.game_packages import (
    GamePackageLoadError,
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import ExistingWorldError, MissingWorldError, SQLiteStore
from llm_system.simulation import (
    ActorActionSubmission,
    ObjectAtLocation,
    ObjectPossessedByCharacter,
    PlayerInterpreterActionSource,
    WaitActionProposal,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "game_packages"
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")
REPLACEMENT_WORLD_ID = UUID("00000000-0000-4000-8000-000000000002")


def _packages() -> ValidatedGamePackages:
    rule = load_game_package(PACKAGE_ROOT / "rules/greybridge-rules/0.2.0")
    scenario = load_game_package(PACKAGE_ROOT / "scenarios/storm-at-greybridge/0.2.0")
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


def _complete_wait_step(store: SQLiteStore) -> None:
    execute_actor_action_step(
        store,
        _packages(),
        ActorActionSubmission(
            proposal_id=UUID("10000000-0000-4000-8000-000000000001"),
            simulation_step_id=UUID("20000000-0000-4000-8000-000000000001"),
            decision_context_id=UUID("30000000-0000-4000-8000-000000000001"),
            source=PlayerInterpreterActionSource(
                source_type="player_interpreter", interpreter_id="parser"
            ),
            actor_id="player",
            proposal=WaitActionProposal(operation="wait", duration_seconds=1),
        ),
        outcome_id=UUID("40000000-0000-4000-8000-000000000001"),
        event_id=UUID("50000000-0000-4000-8000-000000000001"),
    )


def test_build_initial_greybridge_world_projects_authored_state() -> None:
    packages = _packages()
    original = packages.model_dump(mode="json")

    world = build_initial_world(packages)

    assert world.packages is packages
    assert world.state.simulation_time_seconds == 0
    assert [
        (item.character_id, item.location_id) for item in world.state.characters
    ] == [
        ("player", "greybridge-waystation"),
        ("injured-courier", "greybridge-waystation"),
        ("bridge-caretaker", "greybridge-span"),
    ]
    medicine, materials = world.state.objects
    assert medicine.object_id == "medicine"
    assert isinstance(medicine.placement, ObjectPossessedByCharacter)
    assert medicine.placement.character_id == "injured-courier"
    assert materials.object_id == "reinforcement-materials"
    assert isinstance(materials.placement, ObjectAtLocation)
    assert materials.placement.location_id == "greybridge-waystation"
    assert [item.connection_id for item in world.state.connections] == [
        "waystation-to-span",
        "span-to-waystation",
        "span-to-far-bank",
        "far-bank-to-span",
    ]
    assert all(item.is_available for item in world.state.connections)
    assert [(item.fact_id, item.value) for item in world.state.boolean_world_facts] == [
        ("bridge-reinforced", False)
    ]
    assert packages.model_dump(mode="json") == original


def test_create_commits_and_resume_recovers_exact_active_world(tmp_path: Path) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)

    created = create_world(store, _packages(), world_id=WORLD_ID)
    resumed = resume_world(SQLiteStore.open(database), PACKAGE_ROOT)

    assert created == resumed
    assert created.stored_world.world_id == WORLD_ID
    assert created.stored_world.revision == 0
    assert created.stored_world.scheduled_queue.activities == ()
    assert created.stored_world.state is created.validated_world.state
    assert created.validated_world.packages == _packages()

    with pytest.raises(ValidationError, match="state"):
        ActiveWorld(
            stored_world=created.stored_world.model_copy(
                update={
                    "state": created.stored_world.state.model_copy(
                        update={"simulation_time_seconds": 1}
                    )
                }
            ),
            validated_world=created.validated_world,
        )


def test_create_existing_world_fails_without_changing_it(tmp_path: Path) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    original = create_world(store, _packages(), world_id=WORLD_ID)

    with pytest.raises(ExistingWorldError):
        create_world(store, _packages(), world_id=REPLACEMENT_WORLD_ID)

    assert resume_world(store, PACKAGE_ROOT) == original


def test_resume_never_falls_back_to_an_available_package_version(
    tmp_path: Path,
) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    original = create_world(store, _packages(), world_id=WORLD_ID)
    alternate_root = tmp_path / "game_packages"
    shutil.copytree(
        PACKAGE_ROOT / "rules/greybridge-rules/0.1.0",
        alternate_root / "rules/greybridge-rules/0.1.0",
    )
    shutil.copytree(
        PACKAGE_ROOT / "scenarios/storm-at-greybridge/0.1.0",
        alternate_root / "scenarios/storm-at-greybridge/0.1.0",
    )

    with pytest.raises(GamePackageLoadError):
        resume_world(store, alternate_root)

    with store.unit_of_work() as unit:
        assert unit.worlds.get() == original.stored_world


def test_development_reset_replaces_and_clears_the_complete_timeline(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    create_world(store, _packages(), world_id=WORLD_ID)
    _complete_wait_step(store)

    replacement = reset_world_for_development(
        store, _packages(), world_id=REPLACEMENT_WORLD_ID
    )

    assert replacement.stored_world.world_id == REPLACEMENT_WORLD_ID
    assert replacement.stored_world.revision == 0
    assert replacement.stored_world.scheduled_queue.activities == ()
    reopened = SQLiteStore.open(database)
    assert resume_world(reopened, PACKAGE_ROOT) == replacement
    with reopened.unit_of_work() as unit:
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert unit.traces.list_for_world(WORLD_ID) == ()
        assert unit.events.list_for_world(REPLACEMENT_WORLD_ID) == ()
        assert unit.traces.list_for_world(REPLACEMENT_WORLD_ID) == ()


def test_failed_development_reset_restores_the_prior_complete_timeline(
    tmp_path: Path,
) -> None:
    database = tmp_path / "world.sqlite3"
    store = SQLiteStore.open(database)
    create_world(store, _packages(), world_id=WORLD_ID)
    _complete_wait_step(store)
    with store.unit_of_work() as unit:
        prior_world = unit.worlds.get()
        prior_events = unit.events.list_for_world(WORLD_ID)
        prior_traces = unit.traces.list_for_world(WORLD_ID)
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

    with pytest.raises(ExistingWorldError):
        reset_world_for_development(store, _packages(), world_id=REPLACEMENT_WORLD_ID)

    with store.unit_of_work() as unit:
        assert unit.worlds.get() == prior_world
        assert unit.events.list_for_world(WORLD_ID) == prior_events
        assert unit.traces.list_for_world(WORLD_ID) == prior_traces


def test_development_reset_requires_an_existing_world(tmp_path: Path) -> None:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")

    with pytest.raises(MissingWorldError, match="singleton world does not exist"):
        reset_world_for_development(store, _packages(), world_id=REPLACEMENT_WORLD_ID)
