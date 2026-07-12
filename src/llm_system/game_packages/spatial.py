from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from llm_system.game_packages._types import NonBlankText, RecordId

PositiveTraversalSeconds = Annotated[int, Field(gt=0)]


class _SpatialDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class LocationDefinition(_SpatialDefinition):
    id: RecordId
    name: NonBlankText


class ConnectionDefinition(_SpatialDefinition):
    id: RecordId
    name: NonBlankText
    source_location_id: RecordId
    destination_location_id: RecordId
    base_traversal_seconds: PositiveTraversalSeconds


class SpatialGraphDefinition(_SpatialDefinition):
    locations: tuple[LocationDefinition, ...]
    connections: tuple[ConnectionDefinition, ...]

    @field_validator("locations", "connections", mode="before")
    @classmethod
    def normalize_yaml_lists_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("spatial graph collections must be lists or tuples")
