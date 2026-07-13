import json

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    BooleanWorldFactState,
    CharacterState,
    ConnectionState,
    ObjectAtLocation,
    ObjectPlacement,
    ObjectPossessedByCharacter,
    ObjectState,
    WorldState,
)


def test_world_state_models_exact_runtime_overlay_facts() -> None:
    world = WorldState(
        simulation_time_seconds=30,
        characters=(CharacterState(character_id="marin", location_id="waystation"),),
        objects=(
            ObjectState(
                object_id="medicine-kit",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="waystation"
                ),
            ),
            ObjectState(
                object_id="rope",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
        ),
        connections=(
            ConnectionState(connection_id="waystation-to-span", is_available=True),
        ),
        boolean_world_facts=(
            BooleanWorldFactState(fact_id="bridge-safe", value=False),
        ),
    )

    assert world.model_dump(mode="json") == {
        "simulation_time_seconds": 30,
        "characters": [{"character_id": "marin", "location_id": "waystation"}],
        "objects": [
            {
                "object_id": "medicine-kit",
                "placement": {
                    "placement_type": "location",
                    "location_id": "waystation",
                },
            },
            {
                "object_id": "rope",
                "placement": {
                    "placement_type": "possessed_by_character",
                    "character_id": "marin",
                },
            },
        ],
        "connections": [
            {"connection_id": "waystation-to-span", "is_available": True},
        ],
        "boolean_world_facts": [{"fact_id": "bridge-safe", "value": False}],
    }


def test_object_placement_is_a_closed_discriminated_union() -> None:
    adapter: TypeAdapter[ObjectPlacement] = TypeAdapter(ObjectPlacement)

    assert isinstance(
        adapter.validate_python({"placement_type": "location", "location_id": "span"}),
        ObjectAtLocation,
    )
    assert isinstance(
        adapter.validate_python(
            {"placement_type": "possessed_by_character", "character_id": "sela"}
        ),
        ObjectPossessedByCharacter,
    )

    for invalid_placement in (
        {"location_id": "span"},
        {"placement_type": "location", "character_id": "sela"},
        {"placement_type": "unplaced"},
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid_placement)


def test_runtime_state_rejects_invalid_scalars_identifiers_and_unknown_fields() -> None:
    invalid_models = (
        (CharacterState, {"character_id": "Marin", "location_id": "waystation"}),
        (ConnectionState, {"connection_id": "span", "is_available": 1}),
        (
            WorldState,
            {
                "simulation_time_seconds": True,
                "characters": (),
                "objects": (),
                "connections": (),
            },
        ),
        (
            WorldState,
            {
                "simulation_time_seconds": 1.0,
                "characters": (),
                "objects": (),
                "connections": (),
            },
        ),
        (
            WorldState,
            {
                "simulation_time_seconds": -1,
                "characters": (),
                "objects": (),
                "connections": (),
            },
        ),
        (
            ObjectAtLocation,
            {
                "placement_type": "location",
                "location_id": "span",
                "character_id": "sela",
            },
        ),
    )
    for model, data in invalid_models:
        with pytest.raises(ValidationError):
            model.model_validate(data)


def test_world_state_normalizes_json_arrays_to_immutable_tuples() -> None:
    world = WorldState.model_validate_json(
        json.dumps(
            {
                "simulation_time_seconds": 0,
                "characters": [{"character_id": "marin", "location_id": "waystation"}],
                "objects": [],
                "connections": [],
                "boolean_world_facts": [{"fact_id": "bridge-safe", "value": False}],
            }
        )
    )

    assert isinstance(world.characters, tuple)
    assert isinstance(world.boolean_world_facts, tuple)
    assert world.model_dump(mode="json")["characters"] == [
        {"character_id": "marin", "location_id": "waystation"}
    ]
    with pytest.raises(ValidationError):
        world.simulation_time_seconds = 1


def test_structure_allows_empty_duplicate_and_unresolved_references() -> None:
    empty_world = WorldState(
        simulation_time_seconds=0, characters=(), objects=(), connections=()
    )
    unresolved_world = WorldState(
        simulation_time_seconds=0,
        characters=(CharacterState(character_id="unknown", location_id="missing"),) * 2,
        objects=(),
        connections=(),
    )

    assert empty_world.characters == ()
    assert len(unresolved_world.characters) == 2


@pytest.mark.parametrize("value", [0, 1, "false"])
def test_boolean_world_fact_state_rejects_non_boolean_values(value: object) -> None:
    with pytest.raises(ValidationError):
        BooleanWorldFactState.model_validate({"fact_id": "bridge-safe", "value": value})
