from uuid import UUID

import pytest

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    EntityCollectionDefinition,
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationDefinition,
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    validate_game_packages,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionSubmission,
    ActorWaitedEvent,
    AuthorizedActorAction,
    CharacterState,
    PlayerInterpreterActionSource,
    SimulationTimeChanged,
    TakeActionProposal,
    ValidatedWorldState,
    WaitActionProposal,
    WorldState,
    commit_outcome,
    resolve_wait,
    validate_world_state,
)

PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


def _world(simulation_time_seconds: int = 10) -> ValidatedWorldState:
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
            decision_policies=(),
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
                locations=(LocationDefinition(id="square", name="Square"),),
                connections=(),
            ),
            entity_collection=EntityCollectionDefinition(
                entities=(
                    PlayerCharacterDefinition(
                        entity_type="player_character",
                        id="marin",
                        name="Marin",
                        character_archetype_id="person",
                        initial_location_id="square",
                    ),
                )
            ),
        ),
    )
    packages = validate_game_packages(rules, scenario)
    state = WorldState(
        simulation_time_seconds=simulation_time_seconds,
        characters=(CharacterState(character_id="marin", location_id="square"),),
        objects=(),
        connections=(),
    )
    return validate_world_state(packages, state)


def _authorized_wait(
    duration_seconds: int, *, simulation_time_seconds: int = 10
) -> AuthorizedActorAction:
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=WaitActionProposal(
            operation="wait", duration_seconds=duration_seconds
        ),
    )
    return AuthorizedActorAction(
        world=_world(simulation_time_seconds), submission=submission
    )


def test_wait_returns_exact_successful_outcome_with_time_delta_and_event() -> None:
    action = _authorized_wait(30)

    outcome = resolve_wait(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome.status == "succeeded"
    assert outcome.outcome_id == OUTCOME_ID
    assert outcome.proposal_id == PROPOSAL_ID
    assert outcome.reason_code == "wait-completed"
    assert outcome.resolved_at_seconds == 40
    assert outcome.state_changes == (
        SimulationTimeChanged(
            change_type="simulation_time", from_seconds=10, to_seconds=40
        ),
    )
    assert outcome.events == (
        ActorWaitedEvent(
            event_type="actor_waited",
            event_id=EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=40,
            actor_id="marin",
            duration_seconds=30,
        ),
    )


def test_wait_is_deterministic_for_large_duration_and_does_not_mutate_inputs() -> None:
    duration = 10**100
    action = _authorized_wait(duration, simulation_time_seconds=17)
    original = action.model_dump(mode="json")

    first = resolve_wait(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    second = resolve_wait(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert first == second
    assert first.resolved_at_seconds == 17 + duration
    assert action.model_dump(mode="json") == original


def test_non_wait_authorized_action_raises_programmer_error() -> None:
    wait_action = _authorized_wait(30)
    submission = wait_action.submission.model_copy(
        update={"proposal": TakeActionProposal(operation="take", object_id="unknown")}
    )
    action = AuthorizedActorAction(world=wait_action.world, submission=submission)

    with pytest.raises(TypeError, match=r"\S"):
        resolve_wait(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)


def test_wait_outcome_commits_only_time_and_preserves_event_evidence() -> None:
    action = _authorized_wait(30)
    outcome = resolve_wait(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    result = commit_outcome(action.world, outcome)

    assert result.outcome is outcome
    assert result.outcome.events == outcome.events
    assert result.world.packages is action.world.packages
    assert result.world.state.simulation_time_seconds == 40
    assert result.world.state.characters == action.world.state.characters
    assert result.world.state.objects == action.world.state.objects
    assert result.world.state.connections == action.world.state.connections
