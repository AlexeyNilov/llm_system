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
    PossessedPlacementDefinition,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionSubmission,
    ActorObservedEvent,
    AuthorizedActorAction,
    CharacterState,
    CharacterTarget,
    ConnectionState,
    ConnectionTarget,
    LocationTarget,
    ObjectAtLocation,
    ObjectPossessedByCharacter,
    ObjectState,
    ObjectTarget,
    ObservationTarget,
    ObserveActionProposal,
    PlayerInterpreterActionSource,
    RejectedOutcome,
    SurroundingsTarget,
    TakeActionProposal,
    ValidatedWorldState,
    WorldState,
    resolve_observe,
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


def _object(
    identifier: str,
    placement: LocationPlacementDefinition | PossessedPlacementDefinition,
) -> ObjectDefinition:
    return ObjectDefinition(
        entity_type="object",
        id=identifier,
        name=identifier.title(),
        object_archetype_id="item",
        initial_placement=placement,
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
                        id="open-exit",
                        name="Open exit",
                        source_location_id="room",
                        destination_location_id="remote",
                        base_traversal_seconds=1,
                    ),
                    ConnectionDefinition(
                        id="blocked-exit",
                        name="Blocked exit",
                        source_location_id="room",
                        destination_location_id="remote",
                        base_traversal_seconds=1,
                    ),
                    ConnectionDefinition(
                        id="incoming-only",
                        name="Incoming only",
                        source_location_id="remote",
                        destination_location_id="room",
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
                    _object(
                        "room-object",
                        LocationPlacementDefinition(
                            placement_type="location", location_id="room"
                        ),
                    ),
                    _object(
                        "own-object",
                        PossessedPlacementDefinition(
                            placement_type="possessed", character_id="marin"
                        ),
                    ),
                    _object(
                        "other-held",
                        PossessedPlacementDefinition(
                            placement_type="possessed", character_id="sela"
                        ),
                    ),
                    _object(
                        "remote-object",
                        LocationPlacementDefinition(
                            placement_type="location", location_id="remote"
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
                object_id="room-object",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="room"
                ),
            ),
            ObjectState(
                object_id="own-object",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
            ObjectState(
                object_id="other-held",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="sela"
                ),
            ),
            ObjectState(
                object_id="remote-object",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="remote"
                ),
            ),
        ),
        connections=(
            ConnectionState(connection_id="open-exit", is_available=True),
            ConnectionState(connection_id="blocked-exit", is_available=False),
            ConnectionState(connection_id="incoming-only", is_available=True),
        ),
    )
    return validate_world_state(packages, state)


def _authorized_observe(target: ObservationTarget) -> AuthorizedActorAction:
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=ObserveActionProposal(operation="observe", target=target),
    )
    return AuthorizedActorAction(world=_world(), submission=submission)


@pytest.mark.parametrize(
    "target",
    [
        SurroundingsTarget(target_type="surroundings"),
        LocationTarget(target_type="location", location_id="room"),
        ConnectionTarget(target_type="connection", connection_id="blocked-exit"),
        CharacterTarget(target_type="character", character_id="sela"),
        ObjectTarget(target_type="object", object_id="room-object"),
        ObjectTarget(target_type="object", object_id="own-object"),
    ],
    ids=[
        "surroundings",
        "current-location",
        "unavailable-outgoing-connection",
        "co-located-character",
        "co-located-object",
        "possessed-object",
    ],
)
def test_perceptible_target_returns_exact_zero_time_success_event(
    target: ObservationTarget,
) -> None:
    action = _authorized_observe(target)

    outcome = resolve_observe(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome.status == "succeeded"
    assert outcome.outcome_id == OUTCOME_ID
    assert outcome.proposal_id == PROPOSAL_ID
    assert outcome.reason_code == "observation-completed"
    assert outcome.resolved_at_seconds == 37
    assert outcome.state_changes == ()
    assert outcome.events == (
        ActorObservedEvent(
            event_type="actor_observed",
            event_id=EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=37,
            actor_id="marin",
            target=target,
        ),
    )


@pytest.mark.parametrize(
    "target",
    [
        LocationTarget(target_type="location", location_id="unknown"),
        LocationTarget(target_type="location", location_id="remote"),
        ConnectionTarget(target_type="connection", connection_id="incoming-only"),
        CharacterTarget(target_type="character", character_id="marin"),
        CharacterTarget(target_type="character", character_id="remote-person"),
        ObjectTarget(target_type="object", object_id="other-held"),
        ObjectTarget(target_type="object", object_id="remote-object"),
        ObjectTarget(target_type="object", object_id="room"),
    ],
    ids=[
        "unknown",
        "remote-location",
        "incoming-only-connection",
        "self-character",
        "remote-character",
        "other-possessed-object",
        "remote-object",
        "wrong-namespace",
    ],
)
def test_non_perceptible_targets_reject_uniformly_without_event(
    target: ObservationTarget,
) -> None:
    action = _authorized_observe(target)

    outcome = resolve_observe(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome == RejectedOutcome(
        status="rejected",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="target-not-perceptible",
        resolved_at_seconds=37,
    )
    assert set(type(outcome).model_fields) == {
        "status",
        "outcome_id",
        "proposal_id",
        "reason_code",
        "resolved_at_seconds",
    }


def test_observe_is_deterministic_and_preserves_authorized_action_and_world() -> None:
    action = _authorized_observe(
        CharacterTarget(target_type="character", character_id="sela")
    )
    before = action.model_dump(mode="json")
    packages = action.world.packages
    state = action.world.state

    first = resolve_observe(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    second = resolve_observe(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert first == second
    assert action.model_dump(mode="json") == before
    assert action.world.packages is packages
    assert action.world.state is state


def test_non_observe_authorized_action_raises_programmer_error() -> None:
    observe_action = _authorized_observe(SurroundingsTarget(target_type="surroundings"))
    submission = observe_action.submission.model_copy(
        update={"proposal": TakeActionProposal(operation="take", object_id="rope")}
    )
    action = AuthorizedActorAction(world=observe_action.world, submission=submission)

    with pytest.raises(TypeError, match=r"\S"):
        resolve_observe(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
