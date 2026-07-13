from typing import Annotated, Literal

from pydantic import Field, field_validator

from llm_system.simulation._types import AuthoredId, _StrictContract

NonNegativeSeconds = Annotated[int, Field(ge=0)]


class CharacterState(_StrictContract):
    character_id: AuthoredId
    location_id: AuthoredId


class ObjectAtLocation(_StrictContract):
    placement_type: Literal["location"]
    location_id: AuthoredId


class ObjectPossessedByCharacter(_StrictContract):
    placement_type: Literal["possessed_by_character"]
    character_id: AuthoredId


ObjectPlacement = Annotated[
    ObjectAtLocation | ObjectPossessedByCharacter,
    Field(discriminator="placement_type"),
]


class ObjectState(_StrictContract):
    object_id: AuthoredId
    placement: ObjectPlacement


class ConnectionState(_StrictContract):
    connection_id: AuthoredId
    is_available: bool


class BooleanWorldFactState(_StrictContract):
    fact_id: AuthoredId
    value: bool


class WorldState(_StrictContract):
    simulation_time_seconds: NonNegativeSeconds
    characters: tuple[CharacterState, ...]
    objects: tuple[ObjectState, ...]
    connections: tuple[ConnectionState, ...]
    boolean_world_facts: tuple[BooleanWorldFactState, ...] = ()

    @field_validator(
        "characters", "objects", "connections", "boolean_world_facts", mode="before"
    )
    @classmethod
    def normalize_json_arrays_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("runtime state collections must be lists or tuples")
