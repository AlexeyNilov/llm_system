from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from llm_system.player_interpretation import PlayerInterpretationResult
from llm_system.simulation._types import _StrictContract


class ThoughtOnlyCompletion(_StrictContract):
    completion_type: Literal["thought_only"]


class ClarificationCompletion(_StrictContract):
    completion_type: Literal["clarification"]


class ActionLinkedCompletion(_StrictContract):
    completion_type: Literal["action_linked"]
    simulation_step_id: UUID


PlayerInputCompletion = Annotated[
    ThoughtOnlyCompletion | ClarificationCompletion | ActionLinkedCompletion,
    Field(discriminator="completion_type"),
]


class PlayerInputStepTrace(_StrictContract):
    trace_schema_version: Literal[1]
    player_input_id: UUID
    interpretation: PlayerInterpretationResult
    completion: PlayerInputCompletion

    @field_validator("trace_schema_version", mode="before")
    @classmethod
    def trace_schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("trace_schema_version must be an integer literal")
        return value

    @model_validator(mode="after")
    def require_coherent_completion(self) -> Self:
        output = self.interpretation.output
        if isinstance(self.completion, ThoughtOnlyCompletion):
            if (
                output.result_type != "interpreted"
                or output.private_thought is None
                or output.proposal is not None
            ):
                raise ValueError(
                    "thought-only completion requires an interpreted thought without proposal"
                )
        elif isinstance(self.completion, ClarificationCompletion):
            if output.result_type != "clarification":
                raise ValueError(
                    "clarification completion requires clarification output"
                )
        elif output.result_type != "interpreted" or output.proposal is None:
            raise ValueError(
                "action-linked completion requires an interpreted proposal"
            )
        return self
