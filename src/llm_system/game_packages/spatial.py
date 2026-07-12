from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

RecordId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
PositiveTraversalSeconds = Annotated[int, Field(gt=0)]


def _validate_non_blank_name(value: str) -> str:
    if not value.strip():
        raise ValueError("name must not be blank")
    return value


NonBlankName = Annotated[
    str,
    Field(min_length=1),
    AfterValidator(_validate_non_blank_name),
]


class _SpatialDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class LocationDefinition(_SpatialDefinition):
    id: RecordId
    name: NonBlankName


class ConnectionDefinition(_SpatialDefinition):
    id: RecordId
    name: NonBlankName
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
