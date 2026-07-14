from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm_system.functional_generation import (
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
)
from llm_system.simulation.actions import (
    MoveActionProposal,
    NonBlankText,
    ObserveActionProposal,
    SpeakActionProposal,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)
from llm_system.simulation.perception import PerceptionSnapshot

InterpretedPlayerProposal = Annotated[
    ObserveActionProposal
    | MoveActionProposal
    | SpeakActionProposal
    | TakeActionProposal
    | UseActionProposal
    | WaitActionProposal,
    Field(discriminator="operation"),
]


class PlayerInterpreterOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    result_type: Literal["interpreted", "clarification"]
    private_thought: NonBlankText | None
    proposal: InterpretedPlayerProposal | None
    clarification: NonBlankText | None

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        if self.result_type == "interpreted":
            if self.private_thought is None and self.proposal is None:
                raise ValueError(
                    "interpreted output requires a private thought or proposal"
                )
            if self.clarification is not None:
                raise ValueError("interpreted output forbids clarification")
            return self
        if self.private_thought is not None or self.proposal is not None:
            raise ValueError("clarification output forbids thought and proposal")
        if self.clarification is None:
            raise ValueError("clarification output requires clarification")
        return self


class PlayerInterpretationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    player_text: NonBlankText
    perception: PerceptionSnapshot
    output: PlayerInterpreterOutput
    generation: FunctionalGenerationResult[PlayerInterpreterOutput]

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        if self.generation.disposition is FunctionalGenerationDisposition.ACCEPTED:
            if self.generation.value != self.output:
                raise ValueError(
                    "accepted generation value must equal the final output"
                )
            return self
        fallback = PlayerInterpreterOutput(
            result_type="clarification",
            private_thought=None,
            proposal=None,
            clarification="I couldn't interpret that safely. Please clarify your intended thought or action.",
        )
        if self.generation.value is not None or self.output != fallback:
            raise ValueError(
                "failed generation requires no value and a fixed fallback output"
            )
        return self
