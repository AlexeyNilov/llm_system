from uuid import UUID

import pytest

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    ConnectionDefinition,
    DecisionPolicyDefinition,
    EntityCollectionDefinition,
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationDefinition,
    NpcCharacterDefinition,
    ObjectArchetypeDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    validate_game_packages,
)
from llm_system.game_packages.entities import (
    DecisionPolicyReference,
    GoalDefinition,
    LocationPlacementDefinition,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionSubmission,
    ActorSpokeEvent,
    AuthorizedActorAction,
    CharacterState,
    ConnectionState,
    ObjectAtLocation,
    ObjectState,
    PlayerInterpreterActionSource,
    RejectedOutcome,
    SpeakActionProposal,
    TakeActionProposal,
    ValidatedWorldState,
    WorldState,
    resolve_speak,
    validate_world_state,
)

PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


def _npc(identifier: str, location_id: str) -> NpcCharacterDefinition:
    return NpcCharacterDefinition(
        entity_type="npc_character",
        id=identifier,
        name=identifier.title(),
        character_archetype_id="person",
        initial_location_id=location_id,
        identity_summary="A person.",
        goals=(GoalDefinition(id="remain", description="Remain present."),),
        decision_policy=DecisionPolicyReference(
            policy_type="rule", policy_id="routine"
        ),
    )


def _world() -> ValidatedWorldState:
    rules = LoadedRulePackage(
        manifest=RulePackageManifest(
            schema_version=1,
            package_id="rules",
            package_version="1.0.0",
            package_type="rule",
            title="Rules",
            entrypoint="content.yaml",
        ),
        definition=RulePackDefinition(
            schema_version=1,
            object_archetypes=(ObjectArchetypeDefinition(id="item", name="Item"),),
            character_archetypes=(
                CharacterArchetypeDefinition(id="person", name="Person"),
            ),
            decision_policies=(
                DecisionPolicyDefinition(
                    id="routine", name="Routine", policy_type="rule"
                ),
            ),
        ),
    )
    scenario = LoadedScenarioPackage(
        manifest=ScenarioPackageManifest(
            schema_version=1,
            package_id="scenario",
            package_version="1.0.0",
            package_type="scenario",
            title="Scenario",
            entrypoint="content.yaml",
            required_rule_pack=RequiredRulePack(
                package_id="rules", package_version="1.0.0"
            ),
        ),
        definition=ScenarioPackDefinition(
            schema_version=1,
            spatial_graph=SpatialGraphDefinition(
                locations=(
                    LocationDefinition(id="room", name="Room"),
                    LocationDefinition(id="remote", name="Remote"),
                ),
                connections=(
                    ConnectionDefinition(
                        id="path",
                        name="Path",
                        source_location_id="room",
                        destination_location_id="remote",
                        base_traversal_seconds=1,
                    ),
                ),
            ),
            entity_collection=EntityCollectionDefinition(
                entities=(
                    PlayerCharacterDefinition(
                        entity_type="player_character",
                        id="marin",
                        name="Marin",
                        character_archetype_id="person",
                        initial_location_id="room",
                    ),
                    _npc("sela", "room"),
                    _npc("remote-person", "remote"),
                    ObjectDefinition(
                        entity_type="object",
                        id="bell",
                        name="Bell",
                        object_archetype_id="item",
                        initial_placement=LocationPlacementDefinition(
                            placement_type="location", location_id="room"
                        ),
                    ),
                )
            ),
        ),
    )
    packages = validate_game_packages(rules, scenario)
    state = WorldState(
        simulation_time_seconds=37,
        characters=(
            CharacterState(character_id="marin", location_id="room"),
            CharacterState(character_id="sela", location_id="room"),
            CharacterState(character_id="remote-person", location_id="remote"),
        ),
        objects=(
            ObjectState(
                object_id="bell",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="room"
                ),
            ),
        ),
        connections=(ConnectionState(connection_id="path", is_available=True),),
    )
    return validate_world_state(packages, state)


def _authorized_speak(
    recipient_id: str, utterance: str = "  Keep the exact words.  "
) -> AuthorizedActorAction:
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=SpeakActionProposal(
            operation="speak", character_id=recipient_id, utterance=utterance
        ),
    )
    return AuthorizedActorAction(world=_world(), submission=submission)


def test_audible_recipient_returns_exact_zero_time_speech_event() -> None:
    action = _authorized_speak("sela")

    outcome = resolve_speak(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome.status == "succeeded"
    assert outcome.outcome_id == OUTCOME_ID
    assert outcome.proposal_id == PROPOSAL_ID
    assert outcome.reason_code == "speech-completed"
    assert outcome.resolved_at_seconds == 37
    assert outcome.state_changes == ()
    assert outcome.events == (
        ActorSpokeEvent(
            event_type="actor_spoke",
            event_id=EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=37,
            speaker_id="marin",
            recipient_id="sela",
            utterance="  Keep the exact words.  ",
        ),
    )


@pytest.mark.parametrize(
    "recipient_id",
    ["unknown", "remote-person", "marin", "bell", "path", "room"],
    ids=["unknown", "remote", "self", "object", "connection", "location"],
)
def test_inaudible_recipients_reject_uniformly_without_event(
    recipient_id: str,
) -> None:
    action = _authorized_speak(recipient_id)

    outcome = resolve_speak(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome == RejectedOutcome(
        status="rejected",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="recipient-not-audible",
        resolved_at_seconds=37,
    )
    assert set(type(outcome).model_fields) == {
        "status",
        "outcome_id",
        "proposal_id",
        "reason_code",
        "resolved_at_seconds",
    }


def test_speak_is_deterministic_and_preserves_authorized_action_and_world() -> None:
    action = _authorized_speak("sela")
    before = action.model_dump(mode="json")
    packages = action.world.packages
    state = action.world.state
    submission = action.submission
    proposal = action.submission.proposal

    first = resolve_speak(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    second = resolve_speak(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert first == second
    assert action.model_dump(mode="json") == before
    assert action.world.packages is packages
    assert action.world.state is state
    assert action.submission is submission
    assert action.submission.proposal is proposal


def test_non_speak_authorized_action_raises_programmer_error() -> None:
    speak_action = _authorized_speak("sela")
    submission = speak_action.submission.model_copy(
        update={"proposal": TakeActionProposal(operation="take", object_id="bell")}
    )
    action = AuthorizedActorAction(world=speak_action.world, submission=submission)

    with pytest.raises(TypeError, match=r"\S"):
        resolve_speak(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
