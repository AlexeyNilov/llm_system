from typing import TypedDict, Unpack
from uuid import UUID

import pytest

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    ConnectionDefinition,
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
    ActorMovedEvent,
    AuthorizedActorAction,
    CharacterLocationChanged,
    CharacterState,
    ConnectionState,
    MoveActionProposal,
    PlayerInterpreterActionSource,
    RejectedOutcome,
    SimulationTimeChanged,
    TakeActionProposal,
    ValidatedWorldState,
    WorldState,
    commit_outcome,
    resolve_move,
    validate_world_state,
)

PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


class _WorldOptions(TypedDict, total=False):
    actor_location_id: str
    connection_available: bool
    simulation_time_seconds: int
    traversal_seconds: int


def _world(
    *,
    actor_location_id: str = "start",
    connection_available: bool = True,
    simulation_time_seconds: int = 10,
    traversal_seconds: int = 30,
) -> ValidatedWorldState:
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
                        base_traversal_seconds=traversal_seconds,
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
                )
            ),
        ),
    )
    packages = validate_game_packages(rules, scenario)
    state = WorldState(
        simulation_time_seconds=simulation_time_seconds,
        characters=(
            CharacterState(character_id="marin", location_id=actor_location_id),
        ),
        objects=(),
        connections=(
            ConnectionState(connection_id="path", is_available=connection_available),
        ),
    )
    return validate_world_state(packages, state)


def _authorized_move(
    connection_id: str = "path", **world_options: Unpack[_WorldOptions]
) -> AuthorizedActorAction:
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=MoveActionProposal(operation="move", connection_id=connection_id),
    )
    return AuthorizedActorAction(world=_world(**world_options), submission=submission)


def test_move_returns_exact_success_with_ordered_changes_and_event() -> None:
    action = _authorized_move()

    outcome = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome.status == "succeeded"
    assert outcome.outcome_id == OUTCOME_ID
    assert outcome.proposal_id == PROPOSAL_ID
    assert outcome.reason_code == "move-completed"
    assert outcome.resolved_at_seconds == 40
    assert outcome.state_changes == (
        CharacterLocationChanged(
            change_type="character_location",
            character_id="marin",
            from_location_id="start",
            to_location_id="end",
        ),
        SimulationTimeChanged(
            change_type="simulation_time", from_seconds=10, to_seconds=40
        ),
    )
    assert outcome.events == (
        ActorMovedEvent(
            event_type="actor_moved",
            event_id=EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=40,
            actor_id="marin",
            connection_id="path",
            from_location_id="start",
            to_location_id="end",
        ),
    )


@pytest.mark.parametrize(
    ("connection_id", "world_options", "reason_code"),
    [
        (
            "unknown",
            {"actor_location_id": "end", "connection_available": False},
            "unknown-connection",
        ),
        (
            "path",
            {"actor_location_id": "end", "connection_available": False},
            "actor-not-at-connection-source",
        ),
        ("path", {"connection_available": False}, "connection-unavailable"),
    ],
)
def test_move_rejections_are_effect_free_with_gated_precedence(
    connection_id: str, world_options: _WorldOptions, reason_code: str
) -> None:
    action = _authorized_move(connection_id, **world_options)

    outcome = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome == RejectedOutcome(
        status="rejected",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code=reason_code,
        resolved_at_seconds=10,
    )
    assert set(type(outcome).model_fields) == {
        "status",
        "outcome_id",
        "proposal_id",
        "reason_code",
        "resolved_at_seconds",
    }


def test_move_is_deterministic_for_large_duration_and_does_not_mutate_inputs() -> None:
    duration = 10**100
    action = _authorized_move(simulation_time_seconds=17, traversal_seconds=duration)
    original = action.model_dump(mode="json")

    first = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    second = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert first == second
    assert first.resolved_at_seconds == 17 + duration
    assert action.model_dump(mode="json") == original


def test_non_move_authorized_action_raises_programmer_error() -> None:
    move_action = _authorized_move()
    submission = move_action.submission.model_copy(
        update={"proposal": TakeActionProposal(operation="take", object_id="rope")}
    )
    action = AuthorizedActorAction(world=move_action.world, submission=submission)

    with pytest.raises(TypeError, match=r"\S"):
        resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)


def test_move_requires_both_caller_supplied_identities() -> None:
    action = _authorized_move()

    with pytest.raises(TypeError, match="outcome_id"):
        resolve_move(action, event_id=EVENT_ID)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="event_id"):
        resolve_move(action, outcome_id=OUTCOME_ID)  # type: ignore[call-arg]


def test_successful_move_commits_only_location_and_time() -> None:
    action = _authorized_move()
    outcome = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    result = commit_outcome(action.world, outcome)

    assert result.outcome is outcome
    assert result.world.packages is action.world.packages
    assert result.world.state.characters[0].location_id == "end"
    assert result.world.state.simulation_time_seconds == 40
    assert result.world.state.objects == action.world.state.objects
    assert result.world.state.connections == action.world.state.connections
    assert result.world.state.connections[0] is action.world.state.connections[0]
    assert action.world.state.characters[0].location_id == "start"
    assert action.world.state.simulation_time_seconds == 10


def test_rejected_move_commit_preserves_exact_world() -> None:
    action = _authorized_move("unknown")
    outcome = resolve_move(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    result = commit_outcome(action.world, outcome)

    assert result.outcome is outcome
    assert result.world is action.world
