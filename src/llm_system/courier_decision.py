from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm_system.functional_generation import (
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
)
from llm_system.simulation.actions import (
    MoveActionProposal,
    ObserveActionProposal,
    SpeakActionProposal,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)

CourierProposal = Annotated[
    ObserveActionProposal
    | MoveActionProposal
    | SpeakActionProposal
    | TakeActionProposal
    | UseActionProposal
    | WaitActionProposal,
    Field(discriminator="operation"),
]


class CourierPolicyOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    proposal: CourierProposal


class CourierPolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    proposal: CourierProposal
    generation: FunctionalGenerationResult[CourierPolicyOutput]

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        if self.generation.disposition is FunctionalGenerationDisposition.ACCEPTED:
            if (
                self.generation.value is None
                or self.generation.value.proposal != self.proposal
            ):
                raise ValueError(
                    "accepted generation value must equal the final proposal"
                )
            return self
        fallback = WaitActionProposal(operation="wait", duration_seconds=60)
        if self.generation.value is not None or self.proposal != fallback:
            raise ValueError(
                "failed generation requires no value and a fixed fallback proposal"
            )
        return self
