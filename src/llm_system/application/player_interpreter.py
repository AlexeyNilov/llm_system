import json
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from llm_system.application.model_gateway import (
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelGateway,
    ModelMessage,
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

_SYSTEM_INSTRUCTION = (
    "Interpret one non-blank player input using only the supplied current perception. "
    "Extract only explicitly expressed private thought and attempted action. Return at "
    "most one action proposal. Use only IDs present in current perception and only these "
    "schema-supported operations: observe, move, speak, take, use, wait. Represent speech "
    "only through a speak proposal. Request clarification for ambiguity, missing required "
    "arguments, or unsupported mechanics. Do not invent motives, hidden facts, mechanics, "
    "identities, success, outcomes, or narration. Return no trusted metadata."
)
_SAFE_CLARIFICATION_TEXT = (
    "I couldn't interpret that safely. Please clarify your intended thought or action."
)
_NON_BLANK_TEXT_ADAPTER = TypeAdapter(NonBlankText)


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

        if self.generation.value is not None or self.output != _fallback_output():
            raise ValueError(
                "failed generation requires no value and the fixed fallback output"
            )
        return self


def interpret_player_input(
    gateway: FunctionalModelGateway,
    *,
    player_text: str,
    perception: PerceptionSnapshot,
) -> PlayerInterpretationResult:
    validated_player_text = _NON_BLANK_TEXT_ADAPTER.validate_python(
        player_text, strict=True
    )
    context = json.dumps(
        {
            "player_input": validated_player_text,
            "current_perception": perception.model_dump(mode="json"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    messages = (
        ModelMessage(role="system", content=_SYSTEM_INSTRUCTION),
        ModelMessage(role="user", content=context),
    )
    generation = gateway.generate_functional(messages, PlayerInterpreterOutput)
    output = (
        generation.value
        if generation.disposition is FunctionalGenerationDisposition.ACCEPTED
        else _fallback_output()
    )
    assert output is not None
    return PlayerInterpretationResult(
        player_text=validated_player_text,
        perception=perception,
        output=output,
        generation=generation,
    )


def _fallback_output() -> PlayerInterpreterOutput:
    return PlayerInterpreterOutput(
        result_type="clarification",
        private_thought=None,
        proposal=None,
        clarification=_SAFE_CLARIFICATION_TEXT,
    )
