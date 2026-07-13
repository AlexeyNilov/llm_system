from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator
from llm_system.simulation._types import AuthoredId, _StrictContract
from llm_system.simulation.state import NonNegativeSeconds

NonNegativeInsertionSequence = Annotated[int, Field(ge=0)]


class EnvironmentalScheduledActivity(_StrictContract):
    activity_type: Literal["environmental"]
    activity_id: UUID
    eligible_at_seconds: NonNegativeSeconds
    insertion_sequence: NonNegativeInsertionSequence
    schedule_id: AuthoredId


class NpcScheduledActivity(_StrictContract):
    activity_type: Literal["npc"]
    activity_id: UUID
    eligible_at_seconds: NonNegativeSeconds
    insertion_sequence: NonNegativeInsertionSequence
    npc_id: AuthoredId


class SystemDirectorScheduledActivity(_StrictContract):
    activity_type: Literal["system_director"]
    activity_id: UUID
    eligible_at_seconds: NonNegativeSeconds
    insertion_sequence: NonNegativeInsertionSequence
    hook_id: AuthoredId


ScheduledActivity = Annotated[
    EnvironmentalScheduledActivity
    | NpcScheduledActivity
    | SystemDirectorScheduledActivity,
    Field(discriminator="activity_type"),
]


class ScheduledActivityQueue(_StrictContract):
    activities: tuple[ScheduledActivity, ...]

    @field_validator("activities", mode="before")
    @classmethod
    def normalize_json_arrays_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("activities must be a list or tuple")

    @model_validator(mode="after")
    def reject_duplicate_activity_metadata(self) -> Self:
        activity_ids = [activity.activity_id for activity in self.activities]
        if len(activity_ids) != len(set(activity_ids)):
            raise ValueError("activities must have unique activity_id values")
        insertion_sequences = [
            activity.insertion_sequence for activity in self.activities
        ]
        if len(insertion_sequences) != len(set(insertion_sequences)):
            raise ValueError("activities must have unique insertion_sequence values")
        return self
