import pytest
from pydantic import ValidationError

from llm_system.game_packages import (
    ConnectionDefinition,
    LocationDefinition,
    SpatialGraphDefinition,
)


def test_location_definition_accepts_a_valid_record() -> None:
    location = LocationDefinition(id="forest-clearing", name="Forest Clearing")

    assert location.id == "forest-clearing"
    assert location.name == "Forest Clearing"


def test_location_definition_rejects_invalid_fields_and_is_immutable() -> None:
    with pytest.raises(ValidationError):
        LocationDefinition.model_validate(
            {"id": "Forest_Clearing", "name": "Forest Clearing"}
        )
    with pytest.raises(ValidationError):
        LocationDefinition.model_validate({"id": "forest-clearing", "name": "   "})
    with pytest.raises(ValidationError):
        LocationDefinition.model_validate(
            {"id": "forest-clearing", "name": "Forest Clearing", "extra": True}
        )
    with pytest.raises(ValidationError):
        LocationDefinition.model_validate({"id": 1, "name": "Forest Clearing"})

    location = LocationDefinition(id="forest-clearing", name="Forest Clearing")

    with pytest.raises(ValidationError):
        location.name = "Changed"


def test_connection_definition_requires_strict_positive_integer_duration() -> None:
    connection = ConnectionDefinition(
        id="clearing-to-cave",
        name="Cave Path",
        source_location_id="forest-clearing",
        destination_location_id="cave-entrance",
        base_traversal_seconds=45,
    )

    assert connection.base_traversal_seconds == 45
    with pytest.raises(ValidationError):
        connection.name = "Changed"

    for duration in (True, 1.5, "45", 0, -1):
        with pytest.raises(ValidationError):
            ConnectionDefinition.model_validate(
                {
                    "id": "clearing-to-cave",
                    "name": "Cave Path",
                    "source_location_id": "forest-clearing",
                    "destination_location_id": "cave-entrance",
                    "base_traversal_seconds": duration,
                }
            )

    with pytest.raises(ValidationError):
        ConnectionDefinition.model_validate(
            {
                "id": "clearing-to-cave",
                "name": "Cave Path",
                "source_location_id": "forest-clearing",
                "destination_location_id": "cave-entrance",
                "base_traversal_seconds": 45,
                "extra": True,
            }
        )
    with pytest.raises(ValidationError):
        ConnectionDefinition.model_validate(
            {
                "id": "clearing-to-cave",
                "name": "Cave Path",
                "source_location_id": 1,
                "destination_location_id": "cave-entrance",
                "base_traversal_seconds": 45,
            }
        )


def test_spatial_graph_preserves_yaml_list_order_as_immutable_tuples() -> None:
    graph = SpatialGraphDefinition.model_validate(
        {
            "locations": [
                {"id": "forest-clearing", "name": "Forest Clearing"},
                {"id": "cave-entrance", "name": "Cave Entrance"},
            ],
            "connections": [
                {
                    "id": "clearing-to-cave",
                    "name": "Cave Path",
                    "source_location_id": "forest-clearing",
                    "destination_location_id": "cave-entrance",
                    "base_traversal_seconds": 45,
                }
            ],
        }
    )

    assert isinstance(graph.locations, tuple)
    assert isinstance(graph.connections, tuple)
    assert [location.id for location in graph.locations] == [
        "forest-clearing",
        "cave-entrance",
    ]
    with pytest.raises(ValidationError):
        graph.locations = ()
    with pytest.raises(ValidationError):
        graph.locations[0].name = "Changed"
    with pytest.raises(ValidationError):
        SpatialGraphDefinition.model_validate(
            {"locations": [], "connections": [], "extra": True}
        )


@pytest.mark.parametrize(
    "collection", ["forest-clearing", {"id": "forest-clearing"}, 1]
)
@pytest.mark.parametrize("field_name", ["locations", "connections"])
def test_spatial_graph_rejects_non_list_or_tuple_collections(
    field_name: str, collection: object
) -> None:
    values: dict[str, object] = {"locations": [], "connections": []}
    values[field_name] = collection

    with pytest.raises(ValidationError):
        SpatialGraphDefinition.model_validate(values)


def test_spatial_graph_deliberately_allows_unvalidated_graph_semantics() -> None:
    graph = SpatialGraphDefinition.model_validate(
        {
            "locations": [
                {"id": "duplicate", "name": "First Duplicate"},
                {"id": "duplicate", "name": "Second Duplicate"},
            ],
            "connections": [
                {
                    "id": "loop",
                    "name": "Self Loop",
                    "source_location_id": "duplicate",
                    "destination_location_id": "duplicate",
                    "base_traversal_seconds": 1,
                },
                {
                    "id": "parallel-one",
                    "name": "Parallel One",
                    "source_location_id": "missing-location",
                    "destination_location_id": "duplicate",
                    "base_traversal_seconds": 1,
                },
                {
                    "id": "parallel-two",
                    "name": "Parallel Two",
                    "source_location_id": "missing-location",
                    "destination_location_id": "duplicate",
                    "base_traversal_seconds": 1,
                },
            ],
        }
    )

    assert len(graph.locations) == 2
    assert len(graph.connections) == 3
