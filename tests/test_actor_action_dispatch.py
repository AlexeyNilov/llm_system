from collections.abc import Callable
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
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    validate_game_packages,
)
from llm_system.game_packages.entities import DecisionPolicyReference, GoalDefinition
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionOperation,
    ActorActionProposal,
    ActorActionSubmission,
    AuthorizedActorAction,
    CharacterState,
    ConnectionState,
    HelpActionProposal,
    LocationTarget,
    MoveActionProposal,
    ObserveActionProposal,
    OperationResolverUnavailableError,
    PlayerInterpreterActionSource,
    SpeakActionProposal,
    SurroundingsTarget,
    TakeActionProposal,
    UseActionProposal,
    ValidatedWorldState,
    WaitActionProposal,
    WorldState,
    dispatch_actor_action,
    resolve_move,
    resolve_observe,
    resolve_speak,
    resolve_take,
    resolve_wait,
    validate_world_state,
)

PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


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
            object_archetypes=(),
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
                    LocationDefinition(id="start", name="Start"),
                    LocationDefinition(id="end", name="End"),
                ),
                connections=(
                    ConnectionDefinition(
                        id="path",
                        name="Path",
                        source_location_id="start",
                        destination_location_id="end",
                        base_traversal_seconds=30,
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
                        initial_location_id="start",
                    ),
                    NpcCharacterDefinition(
                        entity_type="npc_character",
                        id="sela",
                        name="Sela",
                        character_archetype_id="person",
                        initial_location_id="start",
                        identity_summary="A person.",
                        goals=(
                            GoalDefinition(id="remain", description="Remain present."),
                        ),
                        decision_policy=DecisionPolicyReference(
                            policy_type="rule", policy_id="routine"
                        ),
                    ),
                )
            ),
        ),
    )
    packages = validate_game_packages(rules, scenario)
    state = WorldState(
        simulation_time_seconds=10,
        characters=(
            CharacterState(character_id="marin", location_id="start"),
            CharacterState(character_id="sela", location_id="start"),
        ),
        objects=(),
        connections=(ConnectionState(connection_id="path", is_available=True),),
    )
    return validate_world_state(packages, state)


def _authorized(proposal: ActorActionProposal) -> AuthorizedActorAction:
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=proposal,
    )
    return AuthorizedActorAction(world=_world(), submission=submission)


def test_wait_dispatch_matches_direct_resolution_and_preserves_inputs() -> None:
    action = _authorized(WaitActionProposal(operation="wait", duration_seconds=30))
    original = action.model_dump(mode="json")

    dispatched = dispatch_actor_action(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    direct = resolve_wait(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert dispatched == direct
    assert dispatched.outcome_id == OUTCOME_ID
    assert dispatched.events[0].event_id == EVENT_ID
    assert action.model_dump(mode="json") == original


@pytest.mark.parametrize(
    "proposal",
    [
        MoveActionProposal(operation="move", connection_id="path"),
        MoveActionProposal(operation="move", connection_id="unknown"),
    ],
    ids=["succeeded", "rejected"],
)
def test_move_dispatch_matches_direct_resolution_and_preserves_inputs(
    proposal: MoveActionProposal,
) -> None:
    action = _authorized(proposal)
    original = action.model_dump(mode="json")

    dispatched = dispatch_actor_action(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    direct = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert dispatched == direct
    assert dispatched.outcome_id == OUTCOME_ID
    if dispatched.status == "succeeded":
        assert dispatched.events[0].event_id == EVENT_ID
    else:
        assert dispatched.status == "rejected"
    assert action.model_dump(mode="json") == original


def test_observe_dispatch_matches_direct_resolution_and_preserves_inputs() -> None:
    action = _authorized(
        ObserveActionProposal(
            operation="observe",
            target=SurroundingsTarget(target_type="surroundings"),
        )
    )
    original = action.model_dump(mode="json")

    dispatched = dispatch_actor_action(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    direct = resolve_observe(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert dispatched == direct
    assert dispatched.outcome_id == OUTCOME_ID
    assert dispatched.status == "succeeded"
    assert dispatched.events[0].event_id == EVENT_ID
    assert action.model_dump(mode="json") == original


def test_speak_dispatch_matches_direct_resolution_and_preserves_inputs() -> None:
    action = _authorized(
        SpeakActionProposal(
            operation="speak", character_id="sela", utterance="Exact words"
        )
    )
    original = action.model_dump(mode="json")

    dispatched = dispatch_actor_action(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    direct = resolve_speak(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert dispatched == direct
    assert dispatched.outcome_id == OUTCOME_ID
    assert dispatched.status == "succeeded"
    assert dispatched.events[0].event_id == EVENT_ID
    assert action.model_dump(mode="json") == original


def test_take_dispatch_matches_direct_resolution_and_preserves_inputs() -> None:
    action = _authorized(TakeActionProposal(operation="take", object_id="rope"))
    original = action.model_dump(mode="json")

    dispatched = dispatch_actor_action(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    direct = resolve_take(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert dispatched == direct
    assert dispatched.outcome_id == OUTCOME_ID
    assert dispatched.status == "rejected"
    assert action.model_dump(mode="json") == original


UnavailableProposalFactory = Callable[[], ActorActionProposal]


@pytest.mark.parametrize(
    ("proposal_factory", "operation"),
    [
        (
            lambda: UseActionProposal(
                operation="use",
                object_id="rope",
                target=LocationTarget(target_type="location", location_id="end"),
            ),
            "use",
        ),
        (lambda: HelpActionProposal(operation="help", character_id="marin"), "help"),
    ],
)
def test_unimplemented_operation_reports_typed_unavailable_capability(
    proposal_factory: UnavailableProposalFactory, operation: ActorActionOperation
) -> None:
    action = _authorized(proposal_factory())
    original = action.model_dump(mode="json")

    with pytest.raises(OperationResolverUnavailableError) as caught:
        dispatch_actor_action(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert isinstance(caught.value, RuntimeError)
    assert caught.value.operation == operation
    assert str(caught.value) == (
        f"no resolver is available for actor operation: {operation}"
    )
    assert action.model_dump(mode="json") == original
