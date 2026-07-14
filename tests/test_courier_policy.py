from __future__ import annotations

import json
from typing import cast
from uuid import UUID

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from llm_system.application import (
    CourierPolicyOutput,
    CourierPolicyResult,
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    ModelMessage,
    NpcDecisionContext,
    decide_injured_courier,
)
from llm_system.application.npc_decision import CourierProposal
from llm_system.game_packages.entities import GoalDefinition
from llm_system.simulation import (
    CharacterObserved,
    CharacterTarget,
    ConnectionObserved,
    HelpActionProposal,
    LocationObserved,
    MoveActionProposal,
    ObserveActionProposal,
    PerceptionSnapshot,
    SpeakActionProposal,
    SurroundingsTarget,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)

SYSTEM_INSTRUCTION = (
    "Choose exactly one action proposal for the injured courier using only the "
    "supplied identity, goals, current plan, and current perception. Use only "
    "these schema-supported operations: observe, move, speak, take, use, wait. "
    "Do not invent hidden facts, memories, prior conversation, trusted metadata, "
    "outcomes, or narration. Return no prose."
)


class FakeGateway:
    def __init__(self, result: FunctionalGenerationResult[CourierPolicyOutput]) -> None:
        self.result = result
        self.calls: list[
            tuple[tuple[ModelMessage, ...], type[CourierPolicyOutput]]
        ] = []

    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        self.calls.append((messages, cast(type[CourierPolicyOutput], output_model)))
        return cast(FunctionalGenerationResult[ResultT], self.result)


def test_courier_routes_only_deterministic_bounded_context_and_output_model() -> None:
    context = _context()
    output = CourierPolicyOutput(
        proposal=MoveActionProposal(operation="move", connection_id="road-to-clinic")
    )
    gateway = FakeGateway(_accepted(output))

    result = decide_injured_courier(context, gateway)

    expected_context = json.dumps(
        {
            "current_perception": context.perception.model_dump(mode="json"),
            "current_plan": context.current_plan,
            "goals": [goal.model_dump(mode="json") for goal in context.goals],
            "identity_summary": context.identity_summary,
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
            CourierPolicyOutput,
        )
    ]
    assert result == CourierPolicyResult(
        proposal=output.proposal, generation=gateway.result
    )
    assert result.proposal is output.proposal
    assert result.generation is gateway.result


@pytest.mark.parametrize(
    "proposal",
    [
        ObserveActionProposal(
            operation="observe", target=SurroundingsTarget(target_type="surroundings")
        ),
        MoveActionProposal(operation="move", connection_id="road-to-clinic"),
        SpeakActionProposal(
            operation="speak", character_id="marin", utterance="Please help me."
        ),
        TakeActionProposal(operation="take", object_id="medicine-kit"),
        UseActionProposal(
            operation="use",
            object_id="medicine-kit",
            target=CharacterTarget(target_type="character", character_id="marin"),
        ),
        WaitActionProposal(operation="wait", duration_seconds=12),
    ],
)
def test_courier_preserves_each_accepted_supported_proposal_with_evidence(
    proposal: CourierProposal,
) -> None:
    output = CourierPolicyOutput(proposal=proposal)
    gateway = FakeGateway(_accepted(output))

    result = decide_injured_courier(_context(), gateway)

    assert result.proposal is proposal
    assert result.generation is gateway.result


def test_failed_generation_maps_to_fixed_wait_without_provider_detail() -> None:
    generation = FunctionalGenerationResult[CourierPolicyOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(
            failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
        ),
    )

    result = decide_injured_courier(_context(), FakeGateway(generation))

    assert result.proposal == WaitActionProposal(operation="wait", duration_seconds=60)
    assert result.generation is generation
    assert (
        generation.initial_attempt.failure_kind
        is FunctionalModelFailureKind.SERVICE_ERROR
    )


def test_output_and_result_contracts_reject_help_malformed_extra_and_incoherent_values() -> (
    None
):
    with pytest.raises(ValidationError):
        CourierPolicyOutput.model_validate(
            {"proposal": {"operation": "help", "character_id": "marin"}}
        )
    with pytest.raises(ValidationError):
        CourierPolicyOutput.model_validate(
            {
                "proposal": {"operation": "wait", "duration_seconds": 3},
                "extra": "forbidden",
            }
        )
    with pytest.raises(ValidationError):
        CourierPolicyOutput.model_validate(
            {"proposal": {"operation": "wait", "duration_seconds": "3"}}
        )

    output = CourierPolicyOutput(
        proposal=WaitActionProposal(operation="wait", duration_seconds=3)
    )
    accepted = _accepted(output)
    failed = FunctionalGenerationResult[CourierPolicyOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(
            failure_kind=FunctionalModelFailureKind.MALFORMED_RESPONSE
        ),
    )
    with pytest.raises(ValidationError, match="accepted"):
        CourierPolicyResult(
            proposal=WaitActionProposal(operation="wait", duration_seconds=4),
            generation=accepted,
        )
    with pytest.raises(ValidationError, match="fallback"):
        CourierPolicyResult(proposal=output.proposal, generation=failed)

    schema = TypeAdapter(CourierProposal).json_schema()
    assert schema["discriminator"]["propertyName"] == "operation"
    assert "help" not in json.dumps(schema)
    with pytest.raises(ValidationError):
        TypeAdapter(CourierProposal).validate_python(
            HelpActionProposal(operation="help", character_id="marin")
        )


def test_courier_rejects_wrong_identity_and_context_rejects_other_actor_perception() -> (
    None
):
    wrong_courier = _context(npc_id="bridge-caretaker")
    gateway = FakeGateway(_accepted(_wait_output()))

    with pytest.raises(ValueError, match="injured-courier"):
        decide_injured_courier(wrong_courier, gateway)
    assert gateway.calls == []

    with pytest.raises(ValidationError, match="perception observer"):
        _context(perception=_perception(observer_id="marin"))


def test_equal_calls_do_not_mutate_or_replace_context() -> None:
    context = _context()
    original_dump = context.model_dump(mode="json")
    gateway = FakeGateway(_accepted(_wait_output()))

    first = decide_injured_courier(context, gateway)
    second = decide_injured_courier(context, gateway)

    assert first == second
    assert gateway.calls[0] == gateway.calls[1]
    assert context.model_dump(mode="json") == original_dump


def _accepted(
    output: CourierPolicyOutput,
) -> FunctionalGenerationResult[CourierPolicyOutput]:
    return FunctionalGenerationResult[CourierPolicyOutput](
        disposition=FunctionalGenerationDisposition.ACCEPTED,
        value=output,
        initial_attempt=FunctionalGenerationAttempt(
            content=json.dumps(output.model_dump(mode="json")), finish_reason="stop"
        ),
    )


def _wait_output() -> CourierPolicyOutput:
    return CourierPolicyOutput(
        proposal=WaitActionProposal(operation="wait", duration_seconds=5)
    )


def _context(
    *,
    npc_id: str = "injured-courier",
    perception: PerceptionSnapshot | None = None,
) -> NpcDecisionContext:
    return NpcDecisionContext(
        decision_context_id=UUID("864c0a47-0f9b-4866-a178-3380a4a5543d"),
        npc_id=npc_id,
        identity_summary="An injured courier carrying an urgent message.",
        goals=(
            GoalDefinition(
                id="deliver-message",
                description="Deliver the urgent message to the clinic.",
            ),
        ),
        current_plan="Reach the clinic by the road.",
        perception=perception or _perception(observer_id=npc_id),
    )


def _perception(*, observer_id: str) -> PerceptionSnapshot:
    return PerceptionSnapshot(
        observer_id=observer_id,
        perceived_at_seconds=30,
        observations=(
            LocationObserved(
                observation_type="location",
                source_type="current_state",
                observer_id=observer_id,
                observed_at_seconds=30,
                location_id="greybridge-waystation",
            ),
            CharacterObserved(
                observation_type="character",
                source_type="current_state",
                observer_id=observer_id,
                observed_at_seconds=30,
                character_id="marin",
            ),
            ConnectionObserved(
                observation_type="connection",
                source_type="current_state",
                observer_id=observer_id,
                observed_at_seconds=30,
                connection_id="road-to-clinic",
                is_available=True,
            ),
        ),
    )
