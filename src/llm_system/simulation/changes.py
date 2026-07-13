from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from llm_system.simulation._types import AuthoredId, _StrictContract
from llm_system.simulation.state import NonNegativeSeconds, ObjectPlacement


class CharacterLocationChanged(_StrictContract):
    change_type: Literal["character_location"]
    character_id: AuthoredId
    from_location_id: AuthoredId
    to_location_id: AuthoredId

    @model_validator(mode="after")
    def require_location_change(self) -> Self:
        if self.from_location_id == self.to_location_id:
            raise ValueError("character location must change")
        return self


class ObjectPlacementChanged(_StrictContract):
    change_type: Literal["object_placement"]
    object_id: AuthoredId
    from_placement: ObjectPlacement
    to_placement: ObjectPlacement

    @model_validator(mode="after")
    def require_placement_change(self) -> Self:
        if self.from_placement == self.to_placement:
            raise ValueError("object placement must change")
        return self


class ConnectionAvailabilityChanged(_StrictContract):
    change_type: Literal["connection_availability"]
    connection_id: AuthoredId
    from_available: bool
    to_available: bool

    @model_validator(mode="after")
    def require_availability_change(self) -> Self:
        if self.from_available == self.to_available:
            raise ValueError("connection availability must change")
        return self


class BooleanWorldFactChanged(_StrictContract):
    change_type: Literal["boolean_world_fact"]
    fact_id: AuthoredId
    from_value: bool
    to_value: bool

    @model_validator(mode="after")
    def require_value_change(self) -> Self:
        if self.from_value == self.to_value:
            raise ValueError("boolean world fact must change")
        return self


class SimulationTimeChanged(_StrictContract):
    change_type: Literal["simulation_time"]
    from_seconds: NonNegativeSeconds
    to_seconds: NonNegativeSeconds

    @model_validator(mode="after")
    def require_time_to_advance(self) -> Self:
        if self.to_seconds <= self.from_seconds:
            raise ValueError("simulation time must advance")
        return self


StateChange = Annotated[
    CharacterLocationChanged
    | ObjectPlacementChanged
    | ConnectionAvailabilityChanged
    | BooleanWorldFactChanged
    | SimulationTimeChanged,
    Field(discriminator="change_type"),
]
