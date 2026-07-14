import json
from typing import cast

from pydantic import BaseModel

from llm_system.application import (
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    ModelMessage,
    NarrationStyleOutput,
    select_narration_style,
)
from llm_system.narration import (
    NarrationStylePlan,
    NarrationStyleSection,
    NarrationStyleVoice,
    PlayerNarrationContext,
)


SYSTEM_INSTRUCTION = (
    "Select only a fact-neutral narration template family and an order for every "
    "eligible narration section. The supplied context is the only input. Do not "
    "return prose, names, identifiers, claims, actions, or any other values."
)


class FakeGateway:
    def __init__(
        self, result: FunctionalGenerationResult[NarrationStyleOutput]
    ) -> None:
        self.result = result
        self.calls: list[
            tuple[tuple[ModelMessage, ...], type[NarrationStyleOutput]]
        ] = []

    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        self.calls.append((messages, cast(type[NarrationStyleOutput], output_model)))
        return cast(FunctionalGenerationResult[ResultT], self.result)


def test_style_selection_sends_only_canonical_narration_context() -> None:
    context = _context()
    output = NarrationStyleOutput(
        voice=NarrationStyleVoice.OBSERVATIONAL,
        section_order=(
            NarrationStyleSection.CONNECTIONS,
            NarrationStyleSection.LOCATION,
            NarrationStyleSection.CHARACTERS,
            NarrationStyleSection.OBJECTS,
        ),
    )
    gateway = FakeGateway(_accepted(output))

    result = select_narration_style(context, gateway)

    assert gateway.calls == [
        (
            (
                ModelMessage(role="system", content=SYSTEM_INSTRUCTION),
                ModelMessage(
                    role="user",
                    content=json.dumps(
                        context.model_dump(mode="json"),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            ),
            NarrationStyleOutput,
        )
    ]
    assert result.plan == NarrationStylePlan(
        voice=NarrationStyleVoice.OBSERVATIONAL,
        section_order=output.section_order,
    )


def test_invalid_or_failed_style_selection_uses_direct_default() -> None:
    context = _context()
    invalid = NarrationStyleOutput(
        voice=NarrationStyleVoice.OBSERVATIONAL,
        section_order=(
            NarrationStyleSection.LOCATION,
            NarrationStyleSection.CHARACTERS,
            NarrationStyleSection.CHARACTERS,
            NarrationStyleSection.CONNECTIONS,
        ),
    )
    failed = FunctionalGenerationResult[NarrationStyleOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(
            failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
        ),
    )

    invalid_result = select_narration_style(context, FakeGateway(_accepted(invalid)))
    failed_result = select_narration_style(context, FakeGateway(failed))

    expected = NarrationStylePlan(
        voice=NarrationStyleVoice.DIRECT,
        section_order=(
            NarrationStyleSection.LOCATION,
            NarrationStyleSection.CHARACTERS,
            NarrationStyleSection.OBJECTS,
            NarrationStyleSection.CONNECTIONS,
        ),
    )
    assert invalid_result.plan == expected
    assert failed_result.plan == expected


def _context() -> PlayerNarrationContext:
    return PlayerNarrationContext(
        current_location_name="Greybridge Waystation",
        co_located_character_names=("Injured Courier",),
        visible_object_names=("Medicine",),
        outgoing_connections=(),
    )


def _accepted(
    output: NarrationStyleOutput,
) -> FunctionalGenerationResult[NarrationStyleOutput]:
    return FunctionalGenerationResult[NarrationStyleOutput](
        disposition=FunctionalGenerationDisposition.ACCEPTED,
        value=output,
        initial_attempt=FunctionalGenerationAttempt(
            content=json.dumps(output.model_dump(mode="json")), finish_reason="stop"
        ),
    )
