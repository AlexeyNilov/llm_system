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
    ObjectPlacementDefinition,
    PossessedPlacementDefinition,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionSubmission,
    AuthorizedActorAction,
    CharacterState,
    ConnectionState,
    ObjectAtLocation,
    ObjectPlacementChanged,
    ObjectPossessedByCharacter,
    ObjectState,
    ObjectTakenEvent,
    PlayerInterpreterActionSource,
    RejectedOutcome,
    SpeakActionProposal,
    TakeActionProposal,
    ValidatedWorldState,
    WorldState,
    commit_outcome,
    resolve_take,
    validate_world_state,
)

PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


def _object(identifier: str, placement: str) -> ObjectDefinition:
    initial_placement: ObjectPlacementDefinition
    if placement in {"marin", "sela"}:
        initial_placement = PossessedPlacementDefinition(
            placement_type="possessed", character_id=placement
        )
    else:
        initial_placement = LocationPlacementDefinition(
            placement_type="location", location_id=placement
        )
    return ObjectDefinition(
        entity_type="object",
        id=identifier,
        name=identifier.title(),
        object_archetype_id="item",
        initial_placement=initial_placement,
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
                    NpcCharacterDefinition(
                        entity_type="npc_character",
                        id="sela",
                        name="Sela",
                        character_archetype_id="person",
                        initial_location_id="room",
                        identity_summary="A person.",
                        goals=(GoalDefinition(id="remain", description="Remain."),),
                        decision_policy=DecisionPolicyReference(
                            policy_type="rule", policy_id="routine"
                        ),
                    ),
                    _object("coin", "remote"),
                    _object("remote-object", "room"),
                    _object("self-object", "marin"),
                    _object("other-object", "sela"),
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
        ),
        objects=(
            ObjectState(
                object_id="coin",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="room"
                ),
            ),
            ObjectState(
                object_id="remote-object",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="remote"
                ),
            ),
            ObjectState(
                object_id="self-object",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
            ObjectState(
                object_id="other-object",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="sela"
                ),
            ),
        ),
        connections=(ConnectionState(connection_id="path", is_available=True),),
    )
    return validate_world_state(packages, state)


def _authorized_take(object_id: str) -> AuthorizedActorAction:
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=TakeActionProposal(operation="take", object_id=object_id),
    )
    return AuthorizedActorAction(world=_world(), submission=submission)


def test_accessible_object_returns_exact_zero_time_change_and_event() -> None:
    action = _authorized_take("coin")
    previous_placement = action.world.state.objects[0].placement
    assert isinstance(previous_placement, ObjectAtLocation)

    outcome = resolve_take(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    expected_possession = ObjectPossessedByCharacter(
        placement_type="possessed_by_character", character_id="marin"
    )
    assert outcome.status == "succeeded"
    assert outcome.outcome_id == OUTCOME_ID
    assert outcome.proposal_id == PROPOSAL_ID
    assert outcome.reason_code == "object-taken"
    assert outcome.resolved_at_seconds == 37
    assert outcome.state_changes == (
        ObjectPlacementChanged(
            change_type="object_placement",
            object_id="coin",
            from_placement=previous_placement,
            to_placement=expected_possession,
        ),
    )
    assert outcome.events == (
        ObjectTakenEvent(
            event_type="object_taken",
            event_id=EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=37,
            actor_id="marin",
            object_id="coin",
            previous_placement=previous_placement,
        ),
    )
    assert outcome.state_changes[0].from_placement is previous_placement
    assert outcome.events[0].previous_placement is previous_placement


@pytest.mark.parametrize(
    "object_id",
    [
        "unknown",
        "remote-object",
        "self-object",
        "other-object",
        "marin",
        "room",
        "path",
    ],
    ids=["unknown", "remote", "self", "other", "character", "location", "connection"],
)
def test_inaccessible_objects_reject_uniformly_without_event(object_id: str) -> None:
    outcome = resolve_take(
        _authorized_take(object_id), outcome_id=OUTCOME_ID, event_id=EVENT_ID
    )

    assert outcome == RejectedOutcome(
        status="rejected",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="object-not-accessible",
        resolved_at_seconds=37,
    )
    assert set(type(outcome).model_fields) == {
        "status",
        "outcome_id",
        "proposal_id",
        "reason_code",
        "resolved_at_seconds",
    }


def test_successful_take_commits_possession_without_mutating_input() -> None:
    action = _authorized_take("coin")
    original = action.model_dump(mode="json")
    outcome = resolve_take(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    result = commit_outcome(action.world, outcome)

    assert result.world.state.simulation_time_seconds == 37
    assert result.world.state.objects[0].placement == ObjectPossessedByCharacter(
        placement_type="possessed_by_character", character_id="marin"
    )
    assert action.model_dump(mode="json") == original
    assert action.world.state.objects[0].placement == ObjectAtLocation(
        placement_type="location", location_id="room"
    )


def test_take_is_deterministic_and_preserves_exact_input_objects() -> None:
    action = _authorized_take("coin")
    before = action.model_dump(mode="json")
    world = action.world
    state = world.state
    submission = action.submission
    proposal = submission.proposal
    object_state = state.objects[0]
    placement = object_state.placement

    first = resolve_take(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    second = resolve_take(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert first == second
    assert action.model_dump(mode="json") == before
    assert action.world is world
    assert action.world.state is state
    assert action.submission is submission
    assert action.submission.proposal is proposal
    assert action.world.state.objects[0] is object_state
    assert action.world.state.objects[0].placement is placement


def test_non_take_authorized_action_raises_programmer_error() -> None:
    take_action = _authorized_take("coin")
    submission = take_action.submission.model_copy(
        update={
            "proposal": SpeakActionProposal(
                operation="speak", character_id="sela", utterance="Hello"
            )
        }
    )
    action = AuthorizedActorAction(world=take_action.world, submission=submission)

    with pytest.raises(TypeError, match=r"\S"):
        resolve_take(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
