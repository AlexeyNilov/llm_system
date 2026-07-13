from typing import Annotated, Literal, Self, assert_never
from uuid import UUID

from pydantic import Field, field_validator, model_validator
from llm_system.simulation._types import AuthoredId, _StrictContract
from llm_system.simulation.state import NonNegativeSeconds
from llm_system.simulation.validation import ValidatedWorldState

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


def _phase_rank(activity: ScheduledActivity) -> int:
    if isinstance(activity, EnvironmentalScheduledActivity):
        return 0
    if isinstance(activity, NpcScheduledActivity):
        return 1
    if isinstance(activity, SystemDirectorScheduledActivity):
        return 2
    assert_never(activity)


def _scheduler_order(activity: ScheduledActivity) -> tuple[int, int, int]:
    return (
        activity.eligible_at_seconds,
        _phase_rank(activity),
        activity.insertion_sequence,
    )


class ScheduledActivitySelection(_StrictContract):
    selected_at_seconds: NonNegativeSeconds
    eligible_activities: tuple[ScheduledActivity, ...]
    remaining_queue: ScheduledActivityQueue

    @field_validator("eligible_activities", mode="before")
    @classmethod
    def normalize_json_arrays_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("eligible_activities must be a list or tuple")

    @model_validator(mode="after")
    def validate_partition(self) -> Self:
        if any(
            activity.eligible_at_seconds > self.selected_at_seconds
            for activity in self.eligible_activities
        ):
            raise ValueError("eligible activities must be due")
        if self.eligible_activities != tuple(
            sorted(self.eligible_activities, key=_scheduler_order)
        ):
            raise ValueError("eligible activities must be in scheduler order")
        if any(
            activity.eligible_at_seconds <= self.selected_at_seconds
            for activity in self.remaining_queue.activities
        ):
            raise ValueError("remaining activities must be future")
        combined = self.eligible_activities + self.remaining_queue.activities
        activity_ids = [activity.activity_id for activity in combined]
        if len(activity_ids) != len(set(activity_ids)):
            raise ValueError("activities must have unique activity_id values")
        insertion_sequences = [activity.insertion_sequence for activity in combined]
        if len(insertion_sequences) != len(set(insertion_sequences)):
            raise ValueError("activities must have unique insertion_sequence values")
        return self


def select_eligible_activities(
    world: ValidatedWorldState, queue: ScheduledActivityQueue
) -> ScheduledActivitySelection:
    selected_at_seconds = world.state.simulation_time_seconds
    eligible = tuple(
        activity
        for activity in queue.activities
        if activity.eligible_at_seconds <= selected_at_seconds
    )
    ordered_eligible = tuple(sorted(eligible, key=_scheduler_order))
    if not ordered_eligible:
        remaining_queue = queue
    else:
        remaining_queue = ScheduledActivityQueue(
            activities=tuple(
                activity
                for activity in queue.activities
                if activity.eligible_at_seconds > selected_at_seconds
            )
        )
    return ScheduledActivitySelection(
        selected_at_seconds=selected_at_seconds,
        eligible_activities=ordered_eligible,
        remaining_queue=remaining_queue,
    )
