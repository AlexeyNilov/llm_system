import json

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    BooleanWorldFactChanged,
    CharacterLocationChanged,
    ConnectionAvailabilityChanged,
    ObjectAtLocation,
    ObjectPlacementChanged,
    ObjectPossessedByCharacter,
    SimulationTimeChanged,
    StateChange,
)


def test_state_change_discriminates_and_round_trips_all_delta_variants() -> None:
    adapter: TypeAdapter[StateChange] = TypeAdapter(StateChange)
    payloads = (
        {
            "change_type": "character_location",
            "character_id": "marin",
            "from_location_id": "market",
            "to_location_id": "dock",
        },
        {
            "change_type": "object_placement",
            "object_id": "medicine-kit",
            "from_placement": {"placement_type": "location", "location_id": "market"},
            "to_placement": {
                "placement_type": "possessed_by_character",
                "character_id": "marin",
            },
        },
        {
            "change_type": "connection_availability",
            "connection_id": "market-to-dock",
            "from_available": True,
            "to_available": False,
        },
        {
            "change_type": "boolean_world_fact",
            "fact_id": "bridge-safe",
            "from_value": False,
            "to_value": True,
        },
        {"change_type": "simulation_time", "from_seconds": 0, "to_seconds": 30},
    )

    changes = tuple(adapter.validate_python(payload) for payload in payloads)

    assert tuple(type(change) for change in changes) == (
        CharacterLocationChanged,
        ObjectPlacementChanged,
        ConnectionAvailabilityChanged,
        BooleanWorldFactChanged,
        SimulationTimeChanged,
    )
    for change, payload in zip(changes, payloads, strict=True):
        assert adapter.validate_json(json.dumps(payload)) == change
        assert adapter.dump_python(change, mode="json") == payload


def test_state_changes_reject_no_ops_invalid_scalars_and_unknown_fields() -> None:
    invalid = (
        (
            CharacterLocationChanged,
            {
                "change_type": "character_location",
                "character_id": "marin",
                "from_location_id": "market",
                "to_location_id": "market",
            },
        ),
        (
            ObjectPlacementChanged,
            {
                "change_type": "object_placement",
                "object_id": "medicine-kit",
                "from_placement": {
                    "placement_type": "location",
                    "location_id": "market",
                },
                "to_placement": {"placement_type": "location", "location_id": "market"},
            },
        ),
        (
            ConnectionAvailabilityChanged,
            {
                "change_type": "connection_availability",
                "connection_id": "market-to-dock",
                "from_available": True,
                "to_available": True,
            },
        ),
        (
            BooleanWorldFactChanged,
            {
                "change_type": "boolean_world_fact",
                "fact_id": "bridge-safe",
                "from_value": False,
                "to_value": False,
            },
        ),
        (
            BooleanWorldFactChanged,
            {
                "change_type": "boolean_world_fact",
                "fact_id": "bridge-safe",
                "from_value": 0,
                "to_value": True,
            },
        ),
        (
            ConnectionAvailabilityChanged,
            {
                "change_type": "connection_availability",
                "connection_id": "market-to-dock",
                "from_available": 1,
                "to_available": False,
            },
        ),
        (
            SimulationTimeChanged,
            {"change_type": "simulation_time", "from_seconds": 1, "to_seconds": 1},
        ),
        (
            SimulationTimeChanged,
            {"change_type": "simulation_time", "from_seconds": True, "to_seconds": 2},
        ),
        (
            CharacterLocationChanged,
            {
                "change_type": "character_location",
                "character_id": "Marin",
                "from_location_id": "market",
                "to_location_id": "dock",
                "reason": "walked",
            },
        ),
    )
    for model, payload in invalid:
        with pytest.raises(ValidationError):
            model.model_validate(payload)

    with pytest.raises(ValidationError):
        TypeAdapter(StateChange).validate_python({"change_type": "condition"})


def test_object_delta_reuses_placement_types_and_all_changes_are_immutable() -> None:
    change = ObjectPlacementChanged(
        change_type="object_placement",
        object_id="medicine-kit",
        from_placement=ObjectAtLocation(
            placement_type="location", location_id="market"
        ),
        to_placement=ObjectPossessedByCharacter(
            placement_type="possessed_by_character", character_id="marin"
        ),
    )

    assert isinstance(change.from_placement, ObjectAtLocation)
    assert isinstance(change.to_placement, ObjectPossessedByCharacter)
    with pytest.raises(ValidationError):
        change.object_id = "rope"
