import json

from pydantic import BaseModel, ConfigDict

from llm_system.functional_generation import (
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelGateway,
    ModelMessage,
)
from llm_system.narration import (
    NarrationStylePlan,
    NarrationStyleSection,
    NarrationStyleVoice,
    PlayerNarrationContext,
    default_narration_style_plan,
    is_valid_narration_style_plan,
)

_NARRATION_STYLE_SYSTEM_INSTRUCTION = (
    "Select only a fact-neutral narration template family and an order for every "
    "eligible narration section. The supplied context is the only input. Do not "
    "return prose, names, identifiers, claims, actions, or any other values."
)

__all__ = ["NarrationStyleOutput", "NarrationStyleResult", "select_narration_style"]


class NarrationStyleOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    voice: NarrationStyleVoice
    section_order: tuple[NarrationStyleSection, ...]


class NarrationStyleResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    plan: NarrationStylePlan
    generation: FunctionalGenerationResult[NarrationStyleOutput]


def select_narration_style(
    context: PlayerNarrationContext, gateway: FunctionalModelGateway
) -> NarrationStyleResult:
    generation = gateway.generate_functional(
        (
            ModelMessage(role="system", content=_NARRATION_STYLE_SYSTEM_INSTRUCTION),
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
    plan = default_narration_style_plan(context)
    if generation.disposition is FunctionalGenerationDisposition.ACCEPTED:
        output = generation.value
        assert output is not None
        candidate = NarrationStylePlan(
            voice=output.voice, section_order=output.section_order
        )
        if is_valid_narration_style_plan(context, candidate):
            plan = candidate
    return NarrationStyleResult(plan=plan, generation=generation)
