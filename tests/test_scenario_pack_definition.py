import pytest
from pydantic import ValidationError

from llm_system.game_packages import (
    BooleanWorldFactDefinition,
    EntityCollectionDefinition,
    InitialNpcActivityDefinition,
    ObjectUseBindingDefinition,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
)


def test_scenario_pack_parses_only_ordered_initial_npc_activity_declarations() -> None:
    definition = ScenarioPackDefinition.model_validate(
        {
            "schema_version": 1,
            "spatial_graph": {"locations": [], "connections": []},
            "entity_collection": {"entities": []},
            "initial_npc_activities": [
                {"eligible_at_seconds": 0, "npc_id": "caretaker"},
                {"eligible_at_seconds": 10, "npc_id": "courier"},
            ],
        }
    )

    assert definition.initial_npc_activities == (
        InitialNpcActivityDefinition(eligible_at_seconds=0, npc_id="caretaker"),
        InitialNpcActivityDefinition(eligible_at_seconds=10, npc_id="courier"),
    )

    for invalid_declaration in (
        {"eligible_at_seconds": -1, "npc_id": "caretaker"},
        {"eligible_at_seconds": 0, "npc_id": "caretaker", "activity_id": "x"},
        {"eligible_at_seconds": 0, "npc_id": "caretaker", "insertion_sequence": 0},
        {"eligible_at_seconds": 0, "npc_id": "caretaker", "policy_id": "rule"},
    ):
        with pytest.raises(ValidationError):
            ScenarioPackDefinition.model_validate(
                {
                    "schema_version": 1,
                    "spatial_graph": {"locations": [], "connections": []},
                    "entity_collection": {"entities": []},
                    "initial_npc_activities": [invalid_declaration],
                }
            )


def test_scenario_pack_parses_strict_ordered_authored_use_catalogs() -> None:
    definition = ScenarioPackDefinition.model_validate(
        {
            "schema_version": 1,
            "spatial_graph": {"locations": [], "connections": []},
            "entity_collection": {"entities": []},
            "boolean_world_facts": [
                {"id": "bridge-safe", "name": "Bridge Safe", "initial_value": False}
            ],
            "object_use_bindings": [
                {
                    "id": "reinforce-bridge",
                    "mechanic_id": "reinforce",
                    "object_id": "materials",
                    "target_location_id": "bridge",
                    "fact_id": "bridge-safe",
                    "fact_value": True,
                }
            ],
        }
    )

    assert isinstance(definition.boolean_world_facts[0], BooleanWorldFactDefinition)
    assert isinstance(definition.object_use_bindings[0], ObjectUseBindingDefinition)
    assert definition.boolean_world_facts[0].initial_value is False
    assert definition.object_use_bindings[0].fact_value is True
    with pytest.raises(ValidationError):
        definition.object_use_bindings = ()


@pytest.mark.parametrize("value", [0, 1, "true"])
def test_authored_boolean_fact_values_are_strict(value: object) -> None:
    with pytest.raises(ValidationError):
        BooleanWorldFactDefinition.model_validate(
            {"id": "bridge-safe", "name": "Bridge Safe", "initial_value": value}
        )
    with pytest.raises(ValidationError):
        ObjectUseBindingDefinition.model_validate(
            {
                "id": "reinforce-bridge",
                "mechanic_id": "reinforce",
                "object_id": "materials",
                "target_location_id": "bridge",
                "fact_id": "bridge-safe",
                "fact_value": value,
            }
        )


def test_scenario_pack_parses_its_typed_nested_aggregates() -> None:
    definition = ScenarioPackDefinition.model_validate(
        {
            "schema_version": 1,
            "spatial_graph": {"locations": [], "connections": []},
            "entity_collection": {"entities": []},
        }
    )

    assert definition.schema_version == 1
    assert definition.spatial_graph.locations == ()
    assert definition.entity_collection.entities == ()
    assert definition.boolean_world_facts == ()
    assert definition.object_use_bindings == ()
    assert definition.initial_npc_activities == ()


def test_scenario_pack_exposes_existing_typed_aggregate_models() -> None:
    definition = ScenarioPackDefinition.model_validate(
        {
            "schema_version": 1,
            "spatial_graph": {
                "locations": [{"id": "field-clinic", "name": "Field Clinic"}],
                "connections": [],
            },
            "entity_collection": {
                "entities": [
                    {
                        "entity_type": "player_character",
                        "id": "marin",
                        "name": "Marin",
                        "character_archetype_id": "scout",
                        "initial_location_id": "field-clinic",
                    }
                ]
            },
        }
    )

    assert isinstance(definition.spatial_graph, SpatialGraphDefinition)
    assert isinstance(definition.entity_collection, EntityCollectionDefinition)


def test_scenario_pack_is_deeply_immutable_and_forbids_unknown_fields() -> None:
    definition = ScenarioPackDefinition.model_validate(
        {
            "schema_version": 1,
            "spatial_graph": {
                "locations": [{"id": "field-clinic", "name": "Field Clinic"}],
                "connections": [],
            },
            "entity_collection": {"entities": []},
        }
    )

    with pytest.raises(ValidationError):
        definition.spatial_graph = SpatialGraphDefinition(locations=(), connections=())
    with pytest.raises(ValidationError):
        definition.spatial_graph.locations[0].name = "Changed"
    with pytest.raises(ValidationError):
        ScenarioPackDefinition.model_validate(
            {
                "schema_version": 1,
                "spatial_graph": {"locations": [], "connections": []},
                "entity_collection": {"entities": []},
                "scheduled_activities": [],
            }
        )


@pytest.mark.parametrize("schema_version", [True, "1", 2, None])
def test_scenario_pack_rejects_non_integer_or_unsupported_schema_versions(
    schema_version: object,
) -> None:
    with pytest.raises(ValidationError):
        ScenarioPackDefinition.model_validate(
            {
                "schema_version": schema_version,
                "spatial_graph": {"locations": [], "connections": []},
                "entity_collection": {"entities": []},
            }
        )


@pytest.mark.parametrize(
    "data",
    [
        {
            "spatial_graph": {"locations": [], "connections": []},
            "entity_collection": {"entities": []},
        },
        {
            "schema_version": 1,
            "entity_collection": {"entities": []},
        },
        {
            "schema_version": 1,
            "spatial_graph": {"locations": [], "connections": []},
        },
    ],
)
def test_scenario_pack_requires_each_root_section(data: object) -> None:
    with pytest.raises(ValidationError):
        ScenarioPackDefinition.model_validate(data)


@pytest.mark.parametrize(
    "spatial_graph, entity_collection",
    [
        ([], {"entities": []}),
        ({"locations": [], "connections": []}, []),
        ({"locations": "field-clinic", "connections": []}, {"entities": []}),
        ({"locations": [], "connections": []}, {"entities": "marin"}),
    ],
)
def test_scenario_pack_rejects_malformed_aggregate_sections(
    spatial_graph: object, entity_collection: object
) -> None:
    with pytest.raises(ValidationError):
        ScenarioPackDefinition.model_validate(
            {
                "schema_version": 1,
                "spatial_graph": spatial_graph,
                "entity_collection": entity_collection,
            }
        )


def test_scenario_pack_defers_relational_validation() -> None:
    definition = ScenarioPackDefinition.model_validate(
        {
            "schema_version": 1,
            "spatial_graph": {
                "locations": [],
                "connections": [
                    {
                        "id": "missing-to-missing",
                        "name": "Missing Path",
                        "source_location_id": "missing-source",
                        "destination_location_id": "missing-destination",
                        "base_traversal_seconds": 1,
                    }
                ],
            },
            "entity_collection": {
                "entities": [
                    {
                        "entity_type": "object",
                        "id": "kit",
                        "name": "Kit",
                        "object_archetype_id": "missing-object-archetype",
                        "initial_placement": {
                            "placement_type": "possessed",
                            "character_id": "missing-character",
                        },
                    },
                    {
                        "entity_type": "npc_character",
                        "id": "sela",
                        "name": "Sela",
                        "character_archetype_id": "missing-character-archetype",
                        "initial_location_id": "missing-location",
                        "identity_summary": "A medic.",
                        "goals": [{"id": "help", "description": "Help people."}],
                        "decision_policy": {
                            "policy_type": "rule",
                            "policy_id": "missing-policy",
                        },
                    },
                ]
            },
        }
    )

    assert (
        definition.spatial_graph.connections[0].source_location_id == "missing-source"
    )
    assert len(definition.entity_collection.entities) == 2
