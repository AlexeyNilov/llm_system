from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    ConnectionDefinition,
    DecisionPolicyDefinition,
    EntityCollectionDefinition,
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationDefinition,
    ObjectArchetypeDefinition,
    ObjectDefinition,
    NpcCharacterDefinition,
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    ValidatedGamePackages,
    validate_game_packages,
)
from llm_system.game_packages.entities import (
    DecisionPolicyReference,
    GoalDefinition,
    LocationPlacementDefinition,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorWaitedEvent,
    CanonicalEvent,
    CharacterLocationChanged,
    CharacterState,
    ConnectionAvailabilityChanged,
    ConnectionState,
    FailedOutcome,
    ObjectAtLocation,
    ObjectPlacementChanged,
    ObjectPossessedByCharacter,
    ObjectState,
    OutcomeCommitError,
    OutcomeCommitIssue,
    OutcomeCommitIssueCode,
    OutcomeCommitResult,
    RejectedOutcome,
    SimulationTimeChanged,
    StateChange,
    SucceededOutcome,
    ValidatedWorldState,
    WorldState,
    WorldStateValidationError,
    WorldStateValidationIssue,
    WorldStateValidationIssueCode,
    commit_outcome,
    validate_world_state,
)

OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


def _packages() -> ValidatedGamePackages:
    rule = LoadedRulePackage(
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
            object_archetypes=(ObjectArchetypeDefinition(id="tool", name="Tool"),),
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
                        initial_location_id="start",
                    ),
                    NpcCharacterDefinition(
                        entity_type="npc_character",
                        id="sela",
                        name="Sela",
                        character_archetype_id="person",
                        initial_location_id="end",
                        identity_summary="A guide.",
                        goals=(GoalDefinition(id="guide", description="Guide."),),
                        decision_policy=DecisionPolicyReference(
                            policy_type="rule", policy_id="routine"
                        ),
                    ),
                    ObjectDefinition(
                        entity_type="object",
                        id="rope",
                        name="Rope",
                        object_archetype_id="tool",
                        initial_placement=LocationPlacementDefinition(
                            placement_type="location", location_id="start"
                        ),
                    ),
                )
            ),
        ),
    )
    return validate_game_packages(rule, scenario)


def _world() -> ValidatedWorldState:
    packages = _packages()
    state = WorldState(
        simulation_time_seconds=10,
        characters=(
            CharacterState(character_id="marin", location_id="start"),
            CharacterState(character_id="sela", location_id="end"),
        ),
        objects=(
            ObjectState(
                object_id="rope",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="start"
                ),
            ),
        ),
        connections=(ConnectionState(connection_id="path", is_available=True),),
    )
    return validate_world_state(packages, state)


def _rejected(resolved_at: int = 10) -> RejectedOutcome:
    return RejectedOutcome(
        status="rejected",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="not-allowed",
        resolved_at_seconds=resolved_at,
    )


def _succeeded(
    *changes: StateChange,
    resolved_at: int = 10,
    events: tuple[CanonicalEvent, ...] = (),
) -> SucceededOutcome:
    return SucceededOutcome(
        status="succeeded",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="action-succeeded",
        resolved_at_seconds=resolved_at,
        state_changes=changes,
        events=events,
    )


def test_contracts_are_strict_frozen_and_error_requires_typed_nonempty_tuple() -> None:
    world = _world()
    outcome = _rejected()
    result = OutcomeCommitResult(outcome=outcome, world=world)
    issue = OutcomeCommitIssue(
        code=OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
        path="outcome.state_changes[0].from_seconds",
        message="before value differs",
    )

    assert set(type(result).model_fields) == {"outcome", "world"}
    assert set(type(issue).model_fields) == {"code", "path", "message"}
    assert {code.value for code in OutcomeCommitIssueCode} == {
        "resolution-time-mismatch",
        "unknown-change-target",
        "before-value-mismatch",
        "unknown-after-reference",
    }
    with pytest.raises(ValidationError):
        OutcomeCommitIssue.model_validate(issue.model_dump() | {"extra": "no"})
    with pytest.raises(ValidationError):
        issue.path = "changed"
    with pytest.raises(ValueError):
        OutcomeCommitError(())
    with pytest.raises(TypeError):
        OutcomeCommitError([issue])  # type: ignore[arg-type]
    assert OutcomeCommitError((issue,)).issues == (issue,)


def test_rejection_and_no_change_attempt_preserve_exact_inputs_and_events() -> None:
    world = _world()
    rejected = _rejected()
    event = ActorWaitedEvent(
        event_type="actor_waited",
        event_id=EVENT_ID,
        outcome_id=OUTCOME_ID,
        occurred_at_seconds=10,
        actor_id="marin",
        duration_seconds=1,
    )
    succeeded = _succeeded(events=(event,))
    failed = FailedOutcome(
        status="failed",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="action-failed",
        resolved_at_seconds=10,
        state_changes=(),
        events=(),
    )

    rejected_result = commit_outcome(world, rejected)
    succeeded_result = commit_outcome(world, succeeded)
    failed_result = commit_outcome(world, failed)

    assert rejected_result.outcome is rejected
    assert rejected_result.world is world
    assert succeeded_result.outcome is succeeded
    assert succeeded_result.world is world
    assert succeeded_result.outcome.events[0] is event
    assert failed_result.outcome is failed
    assert failed_result.world is world


def test_all_change_types_apply_atomically_preserving_order_and_unaffected_identity() -> (
    None
):
    world = _world()
    outcome = _succeeded(
        CharacterLocationChanged(
            change_type="character_location",
            character_id="marin",
            from_location_id="start",
            to_location_id="end",
        ),
        ObjectPlacementChanged(
            change_type="object_placement",
            object_id="rope",
            from_placement=ObjectAtLocation(
                placement_type="location", location_id="start"
            ),
            to_placement=ObjectPossessedByCharacter(
                placement_type="possessed_by_character", character_id="marin"
            ),
        ),
        ConnectionAvailabilityChanged(
            change_type="connection_availability",
            connection_id="path",
            from_available=True,
            to_available=False,
        ),
        SimulationTimeChanged(
            change_type="simulation_time", from_seconds=10, to_seconds=20
        ),
        resolved_at=20,
    )

    result = commit_outcome(world, outcome)

    assert result.outcome is outcome
    assert result.world is not world
    assert result.world.packages is world.packages
    assert result.world.state.simulation_time_seconds == 20
    assert [item.character_id for item in result.world.state.characters] == [
        "marin",
        "sela",
    ]
    assert result.world.state.characters[0].location_id == "end"
    assert result.world.state.characters[1] is world.state.characters[1]
    object_change = outcome.state_changes[1]
    assert isinstance(object_change, ObjectPlacementChanged)
    assert result.world.state.objects[0].placement == object_change.to_placement
    assert result.world.state.connections[0].is_available is False
    assert world.state.simulation_time_seconds == 10
    assert world.state.characters[0].location_id == "start"


def test_time_mismatch_is_first_and_change_issues_aggregate_with_target_gating() -> (
    None
):
    world = _world()
    outcome = _succeeded(
        CharacterLocationChanged(
            change_type="character_location",
            character_id="missing",
            from_location_id="wrong",
            to_location_id="unknown",
        ),
        ObjectPlacementChanged(
            change_type="object_placement",
            object_id="rope",
            from_placement=ObjectAtLocation(
                placement_type="location", location_id="end"
            ),
            to_placement=ObjectAtLocation(
                placement_type="location", location_id="unknown"
            ),
        ),
        ConnectionAvailabilityChanged(
            change_type="connection_availability",
            connection_id="missing",
            from_available=False,
            to_available=True,
        ),
        resolved_at=11,
    )

    with pytest.raises(OutcomeCommitError) as error:
        commit_outcome(world, outcome)

    assert [(issue.code, issue.path) for issue in error.value.issues] == [
        (
            OutcomeCommitIssueCode.RESOLUTION_TIME_MISMATCH,
            "outcome.resolved_at_seconds",
        ),
        (
            OutcomeCommitIssueCode.UNKNOWN_CHANGE_TARGET,
            "outcome.state_changes[0].character_id",
        ),
        (
            OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
            "outcome.state_changes[1].from_placement",
        ),
        (
            OutcomeCommitIssueCode.UNKNOWN_AFTER_REFERENCE,
            "outcome.state_changes[1].to_placement.location_id",
        ),
        (
            OutcomeCommitIssueCode.UNKNOWN_CHANGE_TARGET,
            "outcome.state_changes[2].connection_id",
        ),
    ]
    placement = world.state.objects[0].placement
    assert isinstance(placement, ObjectAtLocation)
    assert placement.location_id == "start"


def test_character_possessor_connection_and_time_checks_use_exact_paths() -> None:
    world = _world()
    outcome = _succeeded(
        CharacterLocationChanged(
            change_type="character_location",
            character_id="marin",
            from_location_id="end",
            to_location_id="unknown",
        ),
        ObjectPlacementChanged(
            change_type="object_placement",
            object_id="rope",
            from_placement=ObjectAtLocation(
                placement_type="location", location_id="end"
            ),
            to_placement=ObjectPossessedByCharacter(
                placement_type="possessed_by_character", character_id="unknown"
            ),
        ),
        ConnectionAvailabilityChanged(
            change_type="connection_availability",
            connection_id="path",
            from_available=False,
            to_available=True,
        ),
        SimulationTimeChanged(
            change_type="simulation_time", from_seconds=9, to_seconds=19
        ),
        resolved_at=20,
    )

    with pytest.raises(OutcomeCommitError) as error:
        commit_outcome(world, outcome)

    assert [(issue.code, issue.path) for issue in error.value.issues] == [
        (
            OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
            "outcome.state_changes[0].from_location_id",
        ),
        (
            OutcomeCommitIssueCode.UNKNOWN_AFTER_REFERENCE,
            "outcome.state_changes[0].to_location_id",
        ),
        (
            OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
            "outcome.state_changes[1].from_placement",
        ),
        (
            OutcomeCommitIssueCode.UNKNOWN_AFTER_REFERENCE,
            "outcome.state_changes[1].to_placement.character_id",
        ),
        (
            OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
            "outcome.state_changes[2].from_available",
        ),
        (
            OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
            "outcome.state_changes[3].from_seconds",
        ),
        (
            OutcomeCommitIssueCode.RESOLUTION_TIME_MISMATCH,
            "outcome.state_changes[3].to_seconds",
        ),
    ]


def test_outcome_level_time_mismatch_applies_to_rejection() -> None:
    with pytest.raises(OutcomeCommitError) as error:
        commit_outcome(_world(), _rejected(resolved_at=11))

    assert [(issue.code, issue.path) for issue in error.value.issues] == [
        (
            OutcomeCommitIssueCode.RESOLUTION_TIME_MISMATCH,
            "outcome.resolved_at_seconds",
        )
    ]


def test_unexpected_final_world_validation_failure_is_chained_as_invariant_defect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import llm_system.simulation.commitment as commitment

    world = _world()
    issue = WorldStateValidationIssue(
        code=WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
        path="characters[0].location_id",
        message="unexpected failure",
    )

    def fail_validation(*_args: object) -> None:
        raise WorldStateValidationError((issue,))

    monkeypatch.setattr(commitment, "validate_world_state", fail_validation)
    outcome = _succeeded(
        CharacterLocationChanged(
            change_type="character_location",
            character_id="marin",
            from_location_id="start",
            to_location_id="end",
        )
    )

    with pytest.raises(AssertionError, match="kernel invariant") as error:
        commit_outcome(world, outcome)

    assert isinstance(error.value.__cause__, WorldStateValidationError)
