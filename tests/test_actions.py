import json
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    ActorActionProposal,
    ActorActionSource,
    ActorActionSubmission,
    CharacterTarget,
    ConnectionTarget,
    HelpActionProposal,
    LocationTarget,
    MoveActionProposal,
    NpcPolicyActionSource,
    ObjectTarget,
    ObserveActionProposal,
    ObservationTarget,
    PlayerInterpreterActionSource,
    SpeakActionProposal,
    SurroundingsTarget,
    TakeActionProposal,
    UseActionProposal,
    UseTarget,
    WaitActionProposal,
)


def test_actor_action_proposal_discriminates_all_supported_operation_payloads() -> None:
    adapter: TypeAdapter[ActorActionProposal] = TypeAdapter(ActorActionProposal)

    proposals = (
        adapter.validate_python(
            {"operation": "observe", "target": {"target_type": "surroundings"}}
        ),
        adapter.validate_python(
            {"operation": "move", "connection_id": "market-to-dock"}
        ),
        adapter.validate_python(
            {"operation": "speak", "character_id": "sela", "utterance": "Hello."}
        ),
        adapter.validate_python({"operation": "take", "object_id": "medicine-kit"}),
        adapter.validate_python(
            {
                "operation": "use",
                "object_id": "medicine-kit",
                "target": {"target_type": "character", "character_id": "sela"},
            }
        ),
        adapter.validate_python({"operation": "help", "character_id": "sela"}),
        adapter.validate_python({"operation": "wait", "duration_seconds": 30}),
    )

    assert tuple(type(proposal) for proposal in proposals) == (
        ObserveActionProposal,
        MoveActionProposal,
        SpeakActionProposal,
        TakeActionProposal,
        UseActionProposal,
        HelpActionProposal,
        WaitActionProposal,
    )


def test_operation_payloads_accept_only_their_typed_arguments() -> None:
    assert (
        MoveActionProposal(
            operation="move", connection_id="market-to-dock"
        ).connection_id
        == "market-to-dock"
    )
    assert (
        SpeakActionProposal(
            operation="speak", character_id="sela", utterance="Hello."
        ).utterance
        == "Hello."
    )
    assert (
        TakeActionProposal(operation="take", object_id="medicine-kit").object_id
        == "medicine-kit"
    )
    assert (
        HelpActionProposal(operation="help", character_id="sela").character_id == "sela"
    )
    assert (
        WaitActionProposal(operation="wait", duration_seconds=1).duration_seconds == 1
    )

    invalid_payloads = (
        (
            MoveActionProposal,
            {
                "operation": "move",
                "connection_id": "market-to-dock",
                "location_id": "dock",
            },
        ),
        (
            SpeakActionProposal,
            {"operation": "speak", "character_id": "sela", "utterance": "   "},
        ),
        (TakeActionProposal, {"operation": "take", "object_id": "Medicine_Kit"}),
        (
            HelpActionProposal,
            {"operation": "help", "character_id": "sela", "object_id": "medicine-kit"},
        ),
        (WaitActionProposal, {"operation": "wait", "duration_seconds": True}),
        (WaitActionProposal, {"operation": "wait", "duration_seconds": 0}),
    )
    for model, data in invalid_payloads:
        with pytest.raises(ValidationError):
            model.model_validate(data)


def test_target_unions_constrain_reference_namespaces_and_surroundings() -> None:
    observation_adapter: TypeAdapter[ObservationTarget] = TypeAdapter(ObservationTarget)
    use_adapter: TypeAdapter[UseTarget] = TypeAdapter(UseTarget)

    assert isinstance(
        observation_adapter.validate_python({"target_type": "surroundings"}),
        SurroundingsTarget,
    )
    assert isinstance(
        observation_adapter.validate_python(
            {"target_type": "location", "location_id": "market"}
        ),
        LocationTarget,
    )
    assert isinstance(
        observation_adapter.validate_python(
            {"target_type": "connection", "connection_id": "market-to-dock"}
        ),
        ConnectionTarget,
    )
    assert isinstance(
        observation_adapter.validate_python(
            {"target_type": "character", "character_id": "sela"}
        ),
        CharacterTarget,
    )
    assert isinstance(
        observation_adapter.validate_python(
            {"target_type": "object", "object_id": "medicine-kit"}
        ),
        ObjectTarget,
    )
    assert isinstance(
        use_adapter.validate_python(
            {"target_type": "location", "location_id": "market"}
        ),
        LocationTarget,
    )

    for invalid_target in (
        {"target_type": "character", "target_id": "sela"},
        {
            "target_type": "connection",
            "connection_id": "market-to-dock",
            "target_id": "dock",
        },
        {"target_type": "surroundings"},
    ):
        with pytest.raises(ValidationError):
            use_adapter.validate_python(invalid_target)


def test_proposals_are_immutable_strict_and_contain_no_trusted_metadata() -> None:
    proposal = ObserveActionProposal(
        operation="observe", target=SurroundingsTarget(target_type="surroundings")
    )

    with pytest.raises(ValidationError):
        proposal.target = LocationTarget(target_type="location", location_id="market")
    with pytest.raises(ValidationError):
        ObserveActionProposal.model_validate(
            {
                "operation": "observe",
                "target": {"target_type": "surroundings"},
                "proposal_id": "e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07",
            }
        )
    with pytest.raises(ValidationError):
        ObserveActionProposal.model_validate(
            {
                "operation": "observe",
                "target": {"target_type": "surroundings"},
                "actor_id": "marin",
                "intent": "look around",
                "reasoning": "I need information",
            }
        )

    assert proposal.model_dump(mode="json") == {
        "operation": "observe",
        "target": {"target_type": "surroundings"},
    }
    assert (
        TypeAdapter(ActorActionProposal).json_schema()["discriminator"]["propertyName"]
        == "operation"
    )


def test_submission_requires_injected_uuid_metadata_and_typed_source() -> None:
    proposal_id = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")
    step_id = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
    context_id = UUID("864c0a47-0f9b-4866-a178-3380a4a5543d")
    source = PlayerInterpreterActionSource(
        source_type="player_interpreter", interpreter_id="local-parser"
    )
    submission = ActorActionSubmission(
        proposal_id=proposal_id,
        simulation_step_id=step_id,
        decision_context_id=context_id,
        source=source,
        actor_id="marin",
        proposal=WaitActionProposal(operation="wait", duration_seconds=30),
    )

    assert submission.proposal_id == proposal_id
    assert submission.simulation_step_id == step_id
    assert submission.decision_context_id == context_id
    assert submission.model_dump(mode="json")["proposal_id"] == str(proposal_id)
    assert (
        ActorActionSubmission.model_validate_json(
            json.dumps(submission.model_dump(mode="json"))
        )
        == submission
    )
    with pytest.raises(ValidationError):
        submission.actor_id = "sela"
    with pytest.raises(ValidationError):
        ActorActionSubmission.model_validate(
            {
                "proposal_id": str(proposal_id),
                "simulation_step_id": str(step_id),
                "decision_context_id": str(context_id),
                "source": {
                    "source_type": "player_interpreter",
                    "interpreter_id": "local-parser",
                },
                "actor_id": "marin",
                "proposal": {"operation": "wait", "duration_seconds": 30},
            }
        )


def test_actor_action_source_discriminates_required_provenance_without_authorization() -> (
    None
):
    adapter: TypeAdapter[ActorActionSource] = TypeAdapter(ActorActionSource)

    player = adapter.validate_python(
        {"source_type": "player_interpreter", "interpreter_id": "local-parser"}
    )
    npc = adapter.validate_python(
        {"source_type": "npc_policy", "npc_id": "sela", "policy_id": "medic-routine"}
    )

    assert isinstance(player, PlayerInterpreterActionSource)
    assert isinstance(npc, NpcPolicyActionSource)
    for invalid_source in (
        {"source_type": "player_interpreter", "interpreter_id": "   "},
        {
            "source_type": "player_interpreter",
            "interpreter_id": "local-parser",
            "npc_id": "sela",
        },
        {"source_type": "npc_policy", "npc_id": "Sela", "policy_id": "medic-routine"},
        {
            "source_type": "npc_policy",
            "npc_id": "sela",
            "policy_id": "medic-routine",
            "interpreter_id": "local-parser",
        },
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid_source)

    submission = ActorActionSubmission(
        proposal_id=UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07"),
        simulation_step_id=UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d"),
        decision_context_id=UUID("864c0a47-0f9b-4866-a178-3380a4a5543d"),
        source=npc,
        actor_id="another-character",
        proposal=WaitActionProposal(operation="wait", duration_seconds=30),
    )

    assert submission.actor_id == "another-character"
