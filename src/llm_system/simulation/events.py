from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from llm_system.simulation._types import AuthoredId, _StrictContract
from llm_system.simulation.actions import (
    ActorActionOperation,
    NonBlankText,
    ObservationTarget,
    PositiveSeconds,
    UseTarget,
)
from llm_system.simulation.state import NonNegativeSeconds, ObjectPlacement


class _CanonicalEvent(_StrictContract):
    event_id: UUID
    outcome_id: UUID
    occurred_at_seconds: NonNegativeSeconds


class ActorObservedEvent(_CanonicalEvent):
    event_type: Literal["actor_observed"]
    actor_id: AuthoredId
    target: ObservationTarget


class ActorMovedEvent(_CanonicalEvent):
    event_type: Literal["actor_moved"]
    actor_id: AuthoredId
    connection_id: AuthoredId
    from_location_id: AuthoredId
    to_location_id: AuthoredId

    @model_validator(mode="after")
    def require_location_change(self) -> Self:
        if self.from_location_id == self.to_location_id:
            raise ValueError("actor location must change")
        return self


class ActorSpokeEvent(_CanonicalEvent):
    event_type: Literal["actor_spoke"]
    speaker_id: AuthoredId
    recipient_id: AuthoredId
    utterance: NonBlankText


class ObjectTakenEvent(_CanonicalEvent):
    event_type: Literal["object_taken"]
    actor_id: AuthoredId
    object_id: AuthoredId
    previous_placement: ObjectPlacement


class ObjectUsedEvent(_CanonicalEvent):
    event_type: Literal["object_used"]
    actor_id: AuthoredId
    object_id: AuthoredId
    target: UseTarget


class ActorHelpedEvent(_CanonicalEvent):
    event_type: Literal["actor_helped"]
    actor_id: AuthoredId
    assisted_character_id: AuthoredId


class ActorWaitedEvent(_CanonicalEvent):
    event_type: Literal["actor_waited"]
    actor_id: AuthoredId
    duration_seconds: PositiveSeconds


class ActorActionFailedEvent(_CanonicalEvent):
    event_type: Literal["actor_action_failed"]
    actor_id: AuthoredId
    attempted_operation: ActorActionOperation


CanonicalEvent = Annotated[
    ActorObservedEvent
    | ActorMovedEvent
    | ActorSpokeEvent
    | ObjectTakenEvent
    | ObjectUsedEvent
    | ActorHelpedEvent
    | ActorWaitedEvent
    | ActorActionFailedEvent,
    Field(discriminator="event_type"),
]
