from __future__ import annotations

import json
from typing import cast

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from llm_system.application import (
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    ModelMessage,
    PlayerInterpretationResult,
    PlayerInterpreterOutput,
    interpret_player_input,
)
from llm_system.application.player_interpreter import InterpretedPlayerProposal
from llm_system.simulation import (
    CharacterObserved,
    CharacterTarget,
    ConnectionObserved,
    HelpActionProposal,
    LocationObserved,
    MoveActionProposal,
    ObjectObserved,
    ObjectPossessedByCharacter,
    ObserveActionProposal,
    PerceptionSnapshot,
    SpeakActionProposal,
    SurroundingsTarget,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)

SAFE_CLARIFICATION = (
    "I couldn't interpret that safely. Please clarify your intended thought or action."
)
SYSTEM_INSTRUCTION = (
    "Interpret one non-blank player input using only the supplied current perception. "
    "Extract only explicitly expressed private thought and attempted action. Return at "
    "most one action proposal. Use only IDs present in current perception and only these "
    "schema-supported operations: observe, move, speak, take, use, wait. Represent speech "
    "only through a speak proposal. Request clarification for ambiguity, missing required "
    "arguments, or unsupported mechanics. Do not invent motives, hidden facts, mechanics, "
    "identities, success, outcomes, or narration. Return no trusted metadata."
)


class FakeGateway:
    def __init__(
        self, result: FunctionalGenerationResult[PlayerInterpreterOutput]
    ) -> None:
        self.result = result
        self.calls: list[
            tuple[tuple[ModelMessage, ...], type[PlayerInterpreterOutput]]
        ] = []

    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        self.calls.append(
            (
                messages,
                cast(type[PlayerInterpreterOutput], output_model),
            )
        )
        return cast(FunctionalGenerationResult[ResultT], self.result)


def test_interpreter_routes_only_exact_deterministic_messages_and_output_model() -> (
    None
):
    perception = _perception()
    output = _interpreted(private_thought="I should stay alert.")
    gateway = FakeGateway(_accepted(output))

    result = interpret_player_input(
        gateway, player_text="  I should stay alert.  ", perception=perception
    )

    expected_context = json.dumps(
        {
            "player_input": "  I should stay alert.  ",
            "current_perception": perception.model_dump(mode="json"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    assert gateway.calls == [
        (
            (
                ModelMessage(role="system", content=SYSTEM_INSTRUCTION),
                ModelMessage(role="user", content=expected_context),
            ),
            PlayerInterpreterOutput,
        )
    ]
    assert result.player_text == "  I should stay alert.  "
    assert result.perception is perception
    assert result.output is output
    assert result.generation is gateway.result


@pytest.mark.parametrize(
    "proposal",
    [
        ObserveActionProposal(
            operation="observe",
            target=SurroundingsTarget(target_type="surroundings"),
        ),
        MoveActionProposal(operation="move", connection_id="road-to-bridge"),
        SpeakActionProposal(
            operation="speak", character_id="sela", utterance="Stay back."
        ),
        TakeActionProposal(operation="take", object_id="medicine-kit"),
        UseActionProposal(
            operation="use",
            object_id="medicine-kit",
            target=CharacterTarget(target_type="character", character_id="sela"),
        ),
        WaitActionProposal(operation="wait", duration_seconds=30),
    ],
)
def test_interpreter_preserves_each_supported_proposal_exactly(
    proposal: InterpretedPlayerProposal,
) -> None:
    output = _interpreted(proposal=proposal)
    gateway = FakeGateway(_accepted(output))

    result = interpret_player_input(
        gateway, player_text="Do that.", perception=_perception()
    )

    assert result.output is output
    assert result.output.proposal is proposal
    assert result.generation is gateway.result


def test_interpreter_preserves_thought_plus_one_proposal() -> None:
    proposal = SpeakActionProposal(
        operation="speak", character_id="sela", utterance="We should leave."
    )
    output = _interpreted(private_thought="This place is unsafe.", proposal=proposal)

    result = interpret_player_input(
        FakeGateway(_accepted(output)),
        player_text='I think this is unsafe. I tell Sela, "We should leave."',
        perception=_perception(),
    )

    assert result.output == output


def test_interpreter_preserves_an_accepted_model_clarification() -> None:
    output = PlayerInterpreterOutput(
        result_type="clarification",
        private_thought=None,
        proposal=None,
        clarification="Which route do you mean?",
    )

    result = interpret_player_input(
        FakeGateway(_accepted(output)),
        player_text="Go that way.",
        perception=_perception(),
    )

    assert result.output is output
    assert result.output.clarification == "Which route do you mean?"


@pytest.mark.parametrize(
    "failure_kind",
    [
        FunctionalModelFailureKind.TRANSPORT_UNAVAILABLE,
        FunctionalModelFailureKind.SERVICE_ERROR,
        FunctionalModelFailureKind.MALFORMED_RESPONSE,
    ],
)
def test_any_failed_generation_maps_to_the_fixed_safe_clarification(
    failure_kind: FunctionalModelFailureKind,
) -> None:
    generation = FunctionalGenerationResult[PlayerInterpreterOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(failure_kind=failure_kind),
    )

    result = interpret_player_input(
        FakeGateway(generation),
        player_text="Try something.",
        perception=_perception(),
    )

    assert result.output == PlayerInterpreterOutput(
        result_type="clarification",
        private_thought=None,
        proposal=None,
        clarification=SAFE_CLARIFICATION,
    )
    assert result.generation is generation
    assert result.output.clarification is not None
    assert failure_kind.value not in result.output.clarification


def test_failed_repair_generation_also_maps_to_the_fixed_safe_clarification() -> None:
    invalid_attempt = FunctionalGenerationAttempt(
        content='{"result_type":"interpreted"}',
        finish_reason="stop",
        failure_kind=FunctionalModelFailureKind.INVALID_OUTPUT,
        validation_errors=("private_thought: Field required",),
    )
    generation = FunctionalGenerationResult[PlayerInterpreterOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=invalid_attempt,
        repair_attempt=invalid_attempt,
    )

    result = interpret_player_input(
        FakeGateway(generation),
        player_text="Try something.",
        perception=_perception(),
    )

    assert result.output.clarification == SAFE_CLARIFICATION
    assert result.generation is generation


@pytest.mark.parametrize(
    "payload",
    [
        {
            "result_type": "interpreted",
            "private_thought": None,
            "proposal": None,
            "clarification": None,
        },
        {
            "result_type": "interpreted",
            "private_thought": "Think.",
            "proposal": None,
            "clarification": "Also clarify.",
        },
        {
            "result_type": "clarification",
            "private_thought": "Think.",
            "proposal": None,
            "clarification": "Clarify.",
        },
        {
            "result_type": "clarification",
            "private_thought": None,
            "proposal": None,
            "clarification": None,
        },
        {
            "result_type": "interpreted",
            "private_thought": "   ",
            "proposal": None,
            "clarification": None,
        },
        {
            "result_type": "interpreted",
            "private_thought": "Think.",
            "proposal": None,
        },
        {
            "result_type": "interpreted",
            "private_thought": "Think.",
            "proposal": None,
            "clarification": None,
            "extra": "forbidden",
        },
        {
            "result_type": "interpreted",
            "private_thought": 7,
            "proposal": None,
            "clarification": None,
        },
        {
            "result_type": "interpreted",
            "private_thought": None,
            "proposal": {"operation": "help", "character_id": "sela"},
            "clarification": None,
        },
    ],
)
def test_output_contract_rejects_incoherence_missing_extra_coercion_and_help(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        PlayerInterpreterOutput.model_validate(payload)


def test_all_output_fields_are_required_even_when_nullable() -> None:
    valid: dict[str, object] = {
        "result_type": "interpreted",
        "private_thought": "Think.",
        "proposal": None,
        "clarification": None,
    }

    for missing_field in valid:
        incomplete = {
            key: value for key, value in valid.items() if key != missing_field
        }
        with pytest.raises(ValidationError):
            PlayerInterpreterOutput.model_validate(incomplete)


def test_output_schema_is_closed_immutable_and_discriminates_supported_proposals() -> (
    None
):
    output = _interpreted(private_thought="Keep watch.")
    proposal_schema = TypeAdapter(InterpretedPlayerProposal).json_schema()

    assert proposal_schema["discriminator"]["propertyName"] == "operation"
    assert "help" not in json.dumps(proposal_schema)
    with pytest.raises(ValidationError):
        output.private_thought = "Changed."

    with pytest.raises(ValidationError):
        TypeAdapter(InterpretedPlayerProposal).validate_python(
            HelpActionProposal(operation="help", character_id="sela")
        )


def test_result_contract_enforces_generation_and_final_output_coherence() -> None:
    perception = _perception()
    model_output = _interpreted(private_thought="Model thought.")
    other_output = _interpreted(private_thought="Different thought.")
    accepted = _accepted(model_output)
    failed = FunctionalGenerationResult[PlayerInterpreterOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(
            failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
        ),
    )

    with pytest.raises(ValidationError, match="accepted"):
        PlayerInterpretationResult(
            player_text="Think.",
            perception=perception,
            output=other_output,
            generation=accepted,
        )
    with pytest.raises(ValidationError, match="fallback"):
        PlayerInterpretationResult(
            player_text="Think.",
            perception=perception,
            output=other_output,
            generation=failed,
        )
    for invalid in (
        {
            "player_text": "Think.",
            "perception": perception,
            "output": model_output,
            "generation": accepted,
            "extra": True,
        },
        {
            "player_text": 3,
            "perception": perception,
            "output": model_output,
            "generation": accepted,
        },
    ):
        with pytest.raises(ValidationError):
            PlayerInterpretationResult.model_validate(invalid)


@pytest.mark.parametrize("player_text", ["", " ", "\n\t"])
def test_blank_player_input_fails_before_gateway_invocation(player_text: str) -> None:
    gateway = FakeGateway(_accepted(_interpreted(private_thought="Unused.")))

    with pytest.raises(ValueError, match="blank"):
        interpret_player_input(
            gateway, player_text=player_text, perception=_perception()
        )

    assert gateway.calls == []


def test_equal_calls_are_repeatable_and_do_not_mutate_or_replace_inputs() -> None:
    perception = _perception()
    original_dump = perception.model_dump(mode="json")
    output = _interpreted(
        proposal=WaitActionProposal(operation="wait", duration_seconds=5)
    )
    gateway = FakeGateway(_accepted(output))

    first = interpret_player_input(
        gateway, player_text="Wait five seconds.", perception=perception
    )
    second = interpret_player_input(
        gateway, player_text="Wait five seconds.", perception=perception
    )

    assert first == second
    assert gateway.calls[0] == gateway.calls[1]
    assert first.perception is perception
    assert second.perception is perception
    assert perception.model_dump(mode="json") == original_dump


def _interpreted(
    *,
    private_thought: str | None = None,
    proposal: InterpretedPlayerProposal | None = None,
) -> PlayerInterpreterOutput:
    return PlayerInterpreterOutput(
        result_type="interpreted",
        private_thought=private_thought,
        proposal=proposal,
        clarification=None,
    )


def _accepted(
    output: PlayerInterpreterOutput,
) -> FunctionalGenerationResult[PlayerInterpreterOutput]:
    return FunctionalGenerationResult[PlayerInterpreterOutput](
        disposition=FunctionalGenerationDisposition.ACCEPTED,
        value=output,
        initial_attempt=FunctionalGenerationAttempt(
            content=json.dumps(output.model_dump(mode="json")), finish_reason="stop"
        ),
    )


def _perception() -> PerceptionSnapshot:
    return PerceptionSnapshot(
        observer_id="marin",
        perceived_at_seconds=30,
        observations=(
            LocationObserved(
                observation_type="location",
                source_type="current_state",
                observer_id="marin",
                observed_at_seconds=30,
                location_id="bridge",
            ),
            CharacterObserved(
                observation_type="character",
                source_type="current_state",
                observer_id="marin",
                observed_at_seconds=30,
                character_id="sela",
            ),
            ConnectionObserved(
                observation_type="connection",
                source_type="current_state",
                observer_id="marin",
                observed_at_seconds=30,
                connection_id="road-to-bridge",
                is_available=True,
            ),
            ObjectObserved(
                observation_type="object",
                source_type="current_state",
                observer_id="marin",
                observed_at_seconds=30,
                object_id="medicine-kit",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
        ),
    )
