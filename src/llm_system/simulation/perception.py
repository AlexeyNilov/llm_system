from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from llm_system.simulation._types import AuthoredId, _StrictContract
from llm_system.simulation.events import CanonicalEvent
from llm_system.simulation.state import NonNegativeSeconds, ObjectPlacement


class _Observation(_StrictContract):
    observer_id: AuthoredId
    observed_at_seconds: NonNegativeSeconds


class LocationObserved(_Observation):
    observation_type: Literal["location"]
    source_type: Literal["current_state"]
    location_id: AuthoredId


class ConnectionObserved(_Observation):
    observation_type: Literal["connection"]
    source_type: Literal["current_state"]
    connection_id: AuthoredId
    is_available: bool


class CharacterObserved(_Observation):
    observation_type: Literal["character"]
    source_type: Literal["current_state"]
    character_id: AuthoredId


class ObjectObserved(_Observation):
    observation_type: Literal["object"]
    source_type: Literal["current_state"]
    object_id: AuthoredId
    placement: ObjectPlacement


class EventObserved(_Observation):
    observation_type: Literal["event"]
    source_type: Literal["canonical_event"]
    event: CanonicalEvent

    @model_validator(mode="after")
    def reject_future_event(self) -> Self:
        if self.event.occurred_at_seconds > self.observed_at_seconds:
            raise ValueError("event occurrence time cannot follow observation time")
        return self


Observation = Annotated[
    LocationObserved
    | ConnectionObserved
    | CharacterObserved
    | ObjectObserved
    | EventObserved,
    Field(discriminator="observation_type"),
]


class PerceptionSnapshot(_StrictContract):
    observer_id: AuthoredId
    perceived_at_seconds: NonNegativeSeconds
    observations: tuple[Observation, ...]

    @field_validator("observations", mode="before")
    @classmethod
    def normalize_json_arrays_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("snapshot observations must be lists or tuples")

    @model_validator(mode="after")
    def require_consistent_envelope(self) -> Self:
        for observation in self.observations:
            if observation.observer_id != self.observer_id:
                raise ValueError("observation observer must match snapshot observer")
            if observation.observed_at_seconds != self.perceived_at_seconds:
                raise ValueError("observation time must match snapshot time")
        return self
