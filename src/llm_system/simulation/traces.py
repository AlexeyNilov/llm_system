from typing import Literal, Self
from uuid import UUID

from pydantic import field_validator, model_validator

from llm_system.simulation._types import _StrictContract
from llm_system.simulation.actions import ActorActionSubmission
from llm_system.simulation.outcomes import Outcome
from llm_system.simulation.perception import EventObserved, PerceptionSnapshot
from llm_system.simulation.scheduling import ScheduledActivity
from llm_system.simulation.state import NonNegativeSeconds


class CompletedActorActionStepTrace(_StrictContract):
    trace_schema_version: Literal[1]
    simulation_step_id: UUID
    decision_context_id: UUID
    submission: ActorActionSubmission
    outcome: Outcome
    current_perception: PerceptionSnapshot
    self_event_feedback: tuple[EventObserved, ...]

    @field_validator("trace_schema_version", mode="before")
    @classmethod
    def trace_schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("trace_schema_version must be an integer literal")
        return value

    @field_validator("self_event_feedback", mode="before")
    @classmethod
    def normalize_json_arrays_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("self-event feedback must be a list or tuple")

    @model_validator(mode="after")
    def require_coherent_step_evidence(self) -> Self:
        if self.simulation_step_id != self.submission.simulation_step_id:
            raise ValueError("simulation step identity must match submission")
        if self.decision_context_id != self.submission.decision_context_id:
            raise ValueError("decision context identity must match submission")
        if self.outcome.proposal_id != self.submission.proposal_id:
            raise ValueError("outcome proposal identity must match submission")
        if self.current_perception.observer_id != self.submission.actor_id:
            raise ValueError("current perception actor must match submission")
        if (
            self.current_perception.perceived_at_seconds
            != self.outcome.resolved_at_seconds
        ):
            raise ValueError(
                "current perception time must match committed outcome time"
            )
        for feedback in self.self_event_feedback:
            if feedback.observer_id != self.submission.actor_id:
                raise ValueError("self-event feedback actor must match submission")
            if feedback.observed_at_seconds != self.outcome.resolved_at_seconds:
                raise ValueError(
                    "self-event feedback time must match committed outcome time"
                )
        return self


class ScheduledActivityExecutionTrace(_StrictContract):
    trace_schema_version: Literal[1]
    activity: ScheduledActivity
    selected_at_seconds: NonNegativeSeconds
    simulation_step_id: UUID

    @field_validator("trace_schema_version", mode="before")
    @classmethod
    def trace_schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("trace_schema_version must be an integer literal")
        return value

    @model_validator(mode="after")
    def require_due_activity(self) -> Self:
        if self.activity.eligible_at_seconds > self.selected_at_seconds:
            raise ValueError("scheduled activity must be due at selection time")
        return self
