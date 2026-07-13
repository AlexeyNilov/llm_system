from uuid import UUID

import pytest

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
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
    ActorActionFailedEvent,
    ActorHelpedEvent,
    ActorMovedEvent,
    ActorObservedEvent,
    ActorSpokeEvent,
    ActorWaitedEvent,
    CanonicalEvent,
    CharacterState,
    CharacterTarget,
    EventObserved,
    FutureEventFeedbackError,
    ObjectAtLocation,
    ObjectState,
    ObjectTakenEvent,
    ObjectUsedEvent,
    PerceptionObserverNotFoundError,
    ValidatedWorldState,
    WorldState,
    project_self_event_feedback,
    validate_world_state,
)

OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")


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
                locations=(LocationDefinition(id="room", name="Room"),),
                connections=(),
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
                    NpcCharacterDefinition(
                        entity_type="npc_character",
                        id="sela",
                        name="Sela",
                        character_archetype_id="person",
                        initial_location_id="room",
                        identity_summary="A person.",
                        goals=(
                            GoalDefinition(id="remain", description="Remain present."),
                        ),
                        decision_policy=DecisionPolicyReference(
                            policy_type="rule", policy_id="routine"
                        ),
                    ),
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
            ),
            objects=(
                ObjectState(
                    object_id="token",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="room"
                    ),
                ),
            ),
            connections=(),
        ),
    )


def _event_id(event_number: int) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{event_number:012d}")


def _owned_events(
    actor_id: str = "marin", occurred_at_seconds: int = 30
) -> tuple[CanonicalEvent, ...]:
    return (
        ActorObservedEvent(
            event_type="actor_observed",
            event_id=_event_id(1),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            target=CharacterTarget(target_type="character", character_id="sela"),
        ),
        ActorMovedEvent(
            event_type="actor_moved",
            event_id=_event_id(2),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            connection_id="room-to-hall",
            from_location_id="room",
            to_location_id="hall",
        ),
        ActorSpokeEvent(
            event_type="actor_spoke",
            event_id=_event_id(3),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            speaker_id=actor_id,
            recipient_id="sela",
            utterance="Hello.",
        ),
        ObjectTakenEvent(
            event_type="object_taken",
            event_id=_event_id(4),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            object_id="token",
            previous_placement=ObjectAtLocation(
                placement_type="location", location_id="room"
            ),
        ),
        ObjectUsedEvent(
            event_type="object_used",
            event_id=_event_id(5),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            object_id="token",
            target=CharacterTarget(target_type="character", character_id="sela"),
        ),
        ActorHelpedEvent(
            event_type="actor_helped",
            event_id=_event_id(6),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            assisted_character_id="sela",
        ),
        ActorWaitedEvent(
            event_type="actor_waited",
            event_id=_event_id(7),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            duration_seconds=5,
        ),
        ActorActionFailedEvent(
            event_type="actor_action_failed",
            event_id=_event_id(8),
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=occurred_at_seconds,
            actor_id=actor_id,
            attempted_operation="move",
        ),
    )


def test_all_initial_event_variants_produce_exact_self_feedback() -> None:
    world = _world()
    events = _owned_events()

    feedback = project_self_event_feedback(world, "marin", events)

    assert feedback == tuple(
        EventObserved(
            observation_type="event",
            source_type="canonical_event",
            observer_id="marin",
            observed_at_seconds=30,
            event=event,
        )
        for event in events
    )
    assert all(
        item.event is event for item, event in zip(feedback, events, strict=True)
    )


def test_filtering_preserves_owned_order_duplicates_and_excludes_participant_roles() -> (
    None
):
    owned_past = _owned_events(occurred_at_seconds=12)[0]
    owned_current = _owned_events()[6]
    other_events = _owned_events("sela")
    participant_events: tuple[CanonicalEvent, ...] = (
        other_events[0].model_copy(
            update={
                "target": CharacterTarget(target_type="character", character_id="marin")
            }
        ),
        other_events[2].model_copy(update={"recipient_id": "marin"}),
        other_events[4].model_copy(
            update={
                "target": CharacterTarget(target_type="character", character_id="marin")
            }
        ),
        other_events[5].model_copy(update={"assisted_character_id": "marin"}),
    )
    events = (
        participant_events[0],
        owned_current,
        participant_events[1],
        owned_past,
        participant_events[2],
        owned_current,
        participant_events[3],
    )

    feedback = project_self_event_feedback(_world(), "marin", events)

    assert tuple(item.event for item in feedback) == (
        owned_current,
        owned_past,
        owned_current,
    )
    assert project_self_event_feedback(_world(), "marin", ()) == ()
    assert project_self_event_feedback(_world(), "marin", other_events) == ()


def test_observer_validation_precedes_whole_batch_future_event_validation() -> None:
    future_other = _owned_events("sela", occurred_at_seconds=31)[0]

    for observer_id in ("unknown", "token"):
        with pytest.raises(PerceptionObserverNotFoundError) as observer_error:
            project_self_event_feedback(_world(), observer_id, (future_other,))
        assert observer_error.value.observer_id == observer_id

    with pytest.raises(FutureEventFeedbackError) as future_error:
        project_self_event_feedback(
            _world(), "marin", (_owned_events()[0], future_other, _owned_events()[1])
        )
    assert future_error.value.event_id == future_other.event_id
    assert future_error.value.occurred_at_seconds == 31
    assert future_error.value.perceived_at_seconds == 30
    assert str(future_error.value).strip()
    assert "later" in str(future_error.value)


def test_projection_is_deterministic_and_preserves_immutable_inputs() -> None:
    world = _world()
    events = (_owned_events()[0], _owned_events()[6])
    before_world = world.model_dump()
    packages = world.packages
    state = world.state

    first = project_self_event_feedback(world, "marin", events)
    second = project_self_event_feedback(world, "marin", events)

    assert first == second
    assert world.model_dump() == before_world
    assert world.packages is packages
    assert world.state is state
    assert events[0] is first[0].event
    assert events[1] is first[1].event
