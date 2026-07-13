import pytest

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    ConnectionDefinition,
    DecisionPolicyDefinition,
    EntityCollectionDefinition,
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationDefinition,
    NpcCharacterDefinition,
    ObjectArchetypeDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    ValidatedGamePackages,
    validate_game_packages,
)
from llm_system.game_packages.entities import (
    DecisionPolicyReference,
    GoalDefinition,
    LocationPlacementDefinition,
    PossessedPlacementDefinition,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    CharacterObserved,
    CharacterState,
    ConnectionObserved,
    ConnectionState,
    LocationObserved,
    ObjectAtLocation,
    ObjectObserved,
    ObjectPossessedByCharacter,
    ObjectState,
    PerceptionObserverNotFoundError,
    ValidatedWorldState,
    WorldState,
    project_current_perception,
    validate_world_state,
)


def _npc(identifier: str, location_id: str) -> NpcCharacterDefinition:
    return NpcCharacterDefinition(
        entity_type="npc_character",
        id=identifier,
        name=identifier.title(),
        character_archetype_id="person",
        initial_location_id=location_id,
        identity_summary="A person.",
        goals=(GoalDefinition(id="remain", description="Remain present."),),
        decision_policy=DecisionPolicyReference(
            policy_type="rule", policy_id="routine"
        ),
    )


def _object(
    identifier: str,
    placement: LocationPlacementDefinition | PossessedPlacementDefinition,
) -> ObjectDefinition:
    return ObjectDefinition(
        entity_type="object",
        id=identifier,
        name=identifier.title(),
        object_archetype_id="item",
        initial_placement=placement,
    )


def _packages() -> ValidatedGamePackages:
    rules = LoadedRulePackage(
        manifest=RulePackageManifest(
            schema_version=1,
            package_id="rules",
            package_version="1.0.0",
            package_type="rule",
            title="Rules",
            entrypoint="content.yaml",
        ),
        definition=RulePackDefinition(
            schema_version=1,
            object_archetypes=(ObjectArchetypeDefinition(id="item", name="Item"),),
            character_archetypes=(
                CharacterArchetypeDefinition(id="person", name="Person"),
            ),
            decision_policies=(
                DecisionPolicyDefinition(
                    id="routine", name="Routine", policy_type="rule"
                ),
            ),
        ),
    )
    scenario = LoadedScenarioPackage(
        manifest=ScenarioPackageManifest(
            schema_version=1,
            package_id="scenario",
            package_version="1.0.0",
            package_type="scenario",
            title="Scenario",
            entrypoint="content.yaml",
            required_rule_pack=RequiredRulePack(
                package_id="rules", package_version="1.0.0"
            ),
        ),
        definition=ScenarioPackDefinition(
            schema_version=1,
            spatial_graph=SpatialGraphDefinition(
                locations=(
                    LocationDefinition(id="room", name="Room"),
                    LocationDefinition(id="hall", name="Hall"),
                    LocationDefinition(id="remote", name="Remote"),
                ),
                connections=(
                    ConnectionDefinition(
                        id="room-to-hall",
                        name="Room to hall",
                        source_location_id="room",
                        destination_location_id="hall",
                        base_traversal_seconds=1,
                    ),
                    ConnectionDefinition(
                        id="incoming-only",
                        name="Incoming only",
                        source_location_id="remote",
                        destination_location_id="room",
                        base_traversal_seconds=1,
                    ),
                    ConnectionDefinition(
                        id="room-to-remote",
                        name="Room to remote",
                        source_location_id="room",
                        destination_location_id="remote",
                        base_traversal_seconds=1,
                    ),
                ),
            ),
            entity_collection=EntityCollectionDefinition(
                entities=(
                    PlayerCharacterDefinition(
                        entity_type="player_character",
                        id="marin",
                        name="Marin",
                        character_archetype_id="person",
                        initial_location_id="room",
                    ),
                    _object(
                        "own-first",
                        PossessedPlacementDefinition(
                            placement_type="possessed", character_id="marin"
                        ),
                    ),
                    _npc("sela", "room"),
                    _object(
                        "other-held",
                        PossessedPlacementDefinition(
                            placement_type="possessed", character_id="sela"
                        ),
                    ),
                    _npc("remote-person", "remote"),
                    _object(
                        "direct-later",
                        LocationPlacementDefinition(
                            placement_type="location", location_id="room"
                        ),
                    ),
                    _npc("brin", "room"),
                    _object(
                        "own-later",
                        PossessedPlacementDefinition(
                            placement_type="possessed", character_id="marin"
                        ),
                    ),
                    _object(
                        "remote-object",
                        LocationPlacementDefinition(
                            placement_type="location", location_id="remote"
                        ),
                    ),
                )
            ),
        ),
    )
    return validate_game_packages(rules, scenario)


def _world() -> ValidatedWorldState:
    state = WorldState(
        simulation_time_seconds=37,
        characters=(
            CharacterState(character_id="brin", location_id="room"),
            CharacterState(character_id="remote-person", location_id="remote"),
            CharacterState(character_id="marin", location_id="room"),
            CharacterState(character_id="sela", location_id="room"),
        ),
        objects=(
            ObjectState(
                object_id="remote-object",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="remote"
                ),
            ),
            ObjectState(
                object_id="own-later",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
            ObjectState(
                object_id="direct-later",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="room"
                ),
            ),
            ObjectState(
                object_id="other-held",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="sela"
                ),
            ),
            ObjectState(
                object_id="own-first",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
        ),
        connections=(
            ConnectionState(connection_id="room-to-remote", is_available=True),
            ConnectionState(connection_id="incoming-only", is_available=True),
            ConnectionState(connection_id="room-to-hall", is_available=False),
        ),
    )
    return validate_world_state(_packages(), state)


def test_projection_returns_exact_grouped_authored_order_snapshot_at_canonical_time() -> (
    None
):
    world = _world()

    snapshot = project_current_perception(world, "marin")

    assert snapshot.observer_id == "marin"
    assert snapshot.perceived_at_seconds == 37
    assert snapshot.observations == (
        LocationObserved(
            observation_type="location",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            location_id="room",
        ),
        ConnectionObserved(
            observation_type="connection",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            connection_id="room-to-hall",
            is_available=False,
        ),
        ConnectionObserved(
            observation_type="connection",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            connection_id="room-to-remote",
            is_available=True,
        ),
        CharacterObserved(
            observation_type="character",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            character_id="sela",
        ),
        CharacterObserved(
            observation_type="character",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            character_id="brin",
        ),
        ObjectObserved(
            observation_type="object",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            object_id="own-first",
            placement=ObjectPossessedByCharacter(
                placement_type="possessed_by_character", character_id="marin"
            ),
        ),
        ObjectObserved(
            observation_type="object",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            object_id="direct-later",
            placement=ObjectAtLocation(placement_type="location", location_id="room"),
        ),
        ObjectObserved(
            observation_type="object",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=37,
            object_id="own-later",
            placement=ObjectPossessedByCharacter(
                placement_type="possessed_by_character", character_id="marin"
            ),
        ),
    )


@pytest.mark.parametrize("observer_id", ["unknown-person", "own-first"])
def test_projection_rejects_identifiers_outside_character_state_namespace(
    observer_id: str,
) -> None:
    with pytest.raises(
        PerceptionObserverNotFoundError,
        match=rf"^perception observer not found: {observer_id}$",
    ) as error:
        project_current_perception(_world(), observer_id)

    assert error.value.observer_id == observer_id
    assert error.value.args == (f"perception observer not found: {observer_id}",)


def test_projection_is_deterministic_and_preserves_immutable_input_world() -> None:
    world = _world()
    before = world.model_dump()
    packages = world.packages
    state = world.state

    first = project_current_perception(world, "marin")
    second = project_current_perception(world, "marin")

    assert first == second
    assert world.model_dump() == before
    assert world.packages is packages
    assert world.state is state
    assert all(
        observation.source_type == "current_state" for observation in first.observations
    )
