import json

from pydantic import TypeAdapter

from llm_system.functional_generation import (
    FunctionalGenerationDisposition,
    FunctionalModelGateway,
    ModelMessage,
)
from llm_system.player_interpretation import (
    InterpretedPlayerProposal,
    PlayerInterpretationResult,
    PlayerInterpreterOutput,
)
from llm_system.simulation.actions import NonBlankText
from llm_system.simulation.perception import PerceptionSnapshot

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

__all__ = [
    "InterpretedPlayerProposal",
    "PlayerInterpretationResult",
    "PlayerInterpreterOutput",
    "interpret_player_input",
]


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
