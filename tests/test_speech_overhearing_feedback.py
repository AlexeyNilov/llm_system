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
    ActorSpokeEvent,
    ActorWaitedEvent,
    CharacterState,
    ConnectionState,
    EventObserved,
    ObjectAtLocation,
    ObjectState,
    PerceptionObserverNotFoundError,
    SpeechSpeakerNotFoundError,
    ValidatedWorldState,
    WitnessEventTimeMismatchError,
    WorldState,
    project_speech_overhearing_feedback,
    validate_world_state,
)
from llm_system.simulation.events import CanonicalEvent

OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")


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
                    _npc("orin", "room"),
                    _npc("tovan", "remote"),
                    ObjectDefinition(
                        entity_type="object",
                        id="token",
                        name="Token",
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
    return validate_world_state(
        packages,
        WorldState(
            simulation_time_seconds=30,
            characters=(
                CharacterState(character_id="marin", location_id="room"),
                CharacterState(character_id="sela", location_id="room"),
                CharacterState(character_id="orin", location_id="room"),
                CharacterState(character_id="tovan", location_id="remote"),
            ),
            objects=(
                ObjectState(
                    object_id="token",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="room"
                    ),
                ),
            ),
            connections=(ConnectionState(connection_id="path", is_available=True),),
        ),
    )


def _speech(
    event_number: int,
    *,
    speaker_id: str = "marin",
    recipient_id: str = "sela",
    occurred_at_seconds: int = 30,
) -> ActorSpokeEvent:
    return ActorSpokeEvent(
        event_type="actor_spoke",
        event_id=UUID(f"00000000-0000-0000-0000-{event_number:012d}"),
        outcome_id=OUTCOME_ID,
        occurred_at_seconds=occurred_at_seconds,
        speaker_id=speaker_id,
        recipient_id=recipient_id,
        utterance=f"Message {event_number}.",
    )


def _waited(occurred_at_seconds: int = 30) -> ActorWaitedEvent:
    return ActorWaitedEvent(
        event_type="actor_waited",
        event_id=UUID("00000000-0000-0000-0000-000000000099"),
        outcome_id=OUTCOME_ID,
        occurred_at_seconds=occurred_at_seconds,
        actor_id="marin",
        duration_seconds=1,
    )


def test_colocated_third_party_observes_exact_current_speech_event() -> None:
    event = _speech(1)

    feedback = project_speech_overhearing_feedback(_world(), "orin", (event,))

    assert feedback == (
        EventObserved(
            observation_type="event",
            source_type="canonical_event",
            observer_id="orin",
            observed_at_seconds=30,
            event=event,
        ),
    )
    assert feedback[0].event is event


def test_speaker_recipient_remote_observer_and_non_speech_are_excluded() -> None:
    event = _speech(1)

    assert project_speech_overhearing_feedback(_world(), "marin", (event,)) == ()
    assert project_speech_overhearing_feedback(_world(), "sela", (event,)) == ()
    assert project_speech_overhearing_feedback(_world(), "tovan", (event,)) == ()
    assert project_speech_overhearing_feedback(_world(), "orin", (_waited(),)) == ()


def test_observer_validation_precedes_time_and_speaker_validation() -> None:
    invalid = _speech(1, speaker_id="missing", occurred_at_seconds=29)

    for observer_id in ("unknown", "token"):
        with pytest.raises(PerceptionObserverNotFoundError) as error:
            project_speech_overhearing_feedback(_world(), observer_id, (invalid,))
        assert error.value.observer_id == observer_id


@pytest.mark.parametrize("mismatch_time", [29, 31], ids=["past", "future"])
def test_first_whole_batch_time_mismatch_precedes_speaker_and_filtering(
    mismatch_time: int,
) -> None:
    mismatch = _waited(mismatch_time)
    missing_speaker = _speech(2, speaker_id="missing")

    with pytest.raises(WitnessEventTimeMismatchError) as error:
        project_speech_overhearing_feedback(
            _world(), "orin", (_speech(1), mismatch, missing_speaker)
        )

    assert error.value.event_id == mismatch.event_id
    assert error.value.occurred_at_seconds == mismatch_time
    assert error.value.perceived_at_seconds == 30


def test_first_missing_speaker_is_validated_before_observer_filtering() -> None:
    first = _speech(1, speaker_id="missing", recipient_id="orin")
    second = _speech(2, speaker_id="also-missing")

    with pytest.raises(SpeechSpeakerNotFoundError) as error:
        project_speech_overhearing_feedback(_world(), "orin", (first, second))

    assert error.value.event_id == first.event_id
    assert error.value.speaker_id == "missing"
    assert str(error.value) == (
        f"actor-spoke event {first.event_id} references missing speaker: missing"
    )


def test_missing_remote_speaker_is_rejected_but_non_speech_needs_no_speaker() -> None:
    missing = _speech(1, speaker_id="missing", recipient_id="sela")

    with pytest.raises(SpeechSpeakerNotFoundError):
        project_speech_overhearing_feedback(_world(), "tovan", (missing,))
    assert project_speech_overhearing_feedback(_world(), "orin", (_waited(),)) == ()


def test_recipient_is_not_revalidated_for_third_party_colocation() -> None:
    event = _speech(1, recipient_id="missing")

    feedback = project_speech_overhearing_feedback(_world(), "orin", (event,))

    assert tuple(item.event for item in feedback) == (event,)


def test_projection_preserves_order_duplicates_empty_results_and_inputs() -> None:
    world = _world()
    first = _speech(1)
    second = _speech(2)
    events: tuple[CanonicalEvent, ...] = (second, first, second)
    before_world = world.model_dump()
    packages = world.packages
    state = world.state

    projected = project_speech_overhearing_feedback(world, "orin", events)

    assert tuple(item.event for item in projected) == events
    assert all(
        item.event is event for item, event in zip(projected, events, strict=True)
    )
    assert projected == project_speech_overhearing_feedback(world, "orin", events)
    assert project_speech_overhearing_feedback(world, "orin", ()) == ()
    assert project_speech_overhearing_feedback(world, "tovan", events) == ()
    assert world.model_dump() == before_world
    assert world.packages is packages
    assert world.state is state
    assert events == (second, first, second)
