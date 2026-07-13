import pytest
from pydantic import ValidationError

from llm_system.game_packages import (
    BooleanWorldFactDefinition,
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
    BooleanWorldFactState,
    CharacterState,
    ConnectionState,
    ObjectAtLocation,
    ObjectPossessedByCharacter,
    ObjectState,
    WorldState,
    WorldStateValidationError,
    WorldStateValidationIssue,
    WorldStateValidationIssueCode,
    validate_world_state,
)


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
            boolean_world_facts=(
                BooleanWorldFactDefinition(
                    id="bridge-safe", name="Bridge Safe", initial_value=False
                ),
            ),
        ),
    )
    return validate_game_packages(rule, scenario)


def _state(
    characters: tuple[CharacterState, ...] | None = None,
    objects: tuple[ObjectState, ...] | None = None,
    connections: tuple[ConnectionState, ...] | None = None,
    boolean_world_facts: tuple[BooleanWorldFactState, ...] | None = None,
) -> WorldState:
    return WorldState(
        simulation_time_seconds=0,
        characters=characters
        if characters is not None
        else (
            CharacterState(character_id="marin", location_id="start"),
            CharacterState(character_id="sela", location_id="end"),
        ),
        objects=objects
        if objects is not None
        else (
            ObjectState(
                object_id="rope",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="start"
                ),
            ),
        ),
        connections=connections
        if connections is not None
        else (ConnectionState(connection_id="path", is_available=True),),
        boolean_world_facts=boolean_world_facts
        if boolean_world_facts is not None
        else (BooleanWorldFactState(fact_id="bridge-safe", value=False),),
    )


def _issues(state: WorldState) -> tuple[WorldStateValidationIssue, ...]:
    with pytest.raises(WorldStateValidationError) as error:
        validate_world_state(_packages(), state)
    return error.value.issues


def test_validate_world_state_returns_frozen_identity_preserving_wrapper() -> None:
    packages = _packages()
    state = _state()

    result = validate_world_state(packages, state)

    assert result.packages is packages
    assert result.state is state
    with pytest.raises(ValidationError):
        result.state = state


def test_validation_preserves_invalid_inputs_without_repairing_them() -> None:
    packages = _packages()
    state = _state(
        characters=(CharacterState(character_id="marin", location_id="missing"),)
    )
    original_packages = packages.model_dump(mode="json")
    original_state = state.model_dump(mode="json")

    _issues(state)

    assert packages.model_dump(mode="json") == original_packages
    assert state.model_dump(mode="json") == original_state


def test_validation_orders_overlay_issues_by_namespace_and_runtime_authorship_order() -> (
    None
):
    issues = _issues(
        _state(
            characters=(
                CharacterState(character_id="marin", location_id="start"),
                CharacterState(character_id="marin", location_id="end"),
                CharacterState(character_id="extra", location_id="start"),
            ),
            objects=(
                ObjectState(
                    object_id="rope",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="start"
                    ),
                ),
                ObjectState(
                    object_id="rope",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="end"
                    ),
                ),
                ObjectState(
                    object_id="extra",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="start"
                    ),
                ),
            ),
            connections=(
                ConnectionState(connection_id="path", is_available=True),
                ConnectionState(connection_id="path", is_available=False),
                ConnectionState(connection_id="extra", is_available=True),
            ),
        )
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
            "characters[1].character_id",
        ),
        (WorldStateValidationIssueCode.MISSING_STATE, "characters"),
        (WorldStateValidationIssueCode.UNEXPECTED_STATE, "characters[2].character_id"),
        (WorldStateValidationIssueCode.DUPLICATE_STATE_ID, "objects[1].object_id"),
        (WorldStateValidationIssueCode.UNEXPECTED_STATE, "objects[2].object_id"),
        (
            WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
            "connections[1].connection_id",
        ),
        (
            WorldStateValidationIssueCode.UNEXPECTED_STATE,
            "connections[2].connection_id",
        ),
    ]
    assert "sela" in issues[1].message


def test_duplicate_issues_follow_first_duplicate_encounter_order() -> None:
    issues = _issues(
        _state(
            characters=(
                CharacterState(character_id="marin", location_id="start"),
                CharacterState(character_id="sela", location_id="end"),
                CharacterState(character_id="sela", location_id="end"),
                CharacterState(character_id="marin", location_id="start"),
            )
        )
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
            "characters[2].character_id",
        ),
        (
            WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
            "characters[3].character_id",
        ),
    ]


def test_boolean_fact_overlay_is_complete_and_ordered_after_connections() -> None:
    issues = _issues(
        _state(
            connections=(
                ConnectionState(connection_id="path", is_available=True),
                ConnectionState(connection_id="path", is_available=False),
            ),
            boolean_world_facts=(
                BooleanWorldFactState(fact_id="bridge-safe", value=False),
                BooleanWorldFactState(fact_id="bridge-safe", value=True),
                BooleanWorldFactState(fact_id="extra", value=False),
            ),
        )
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
            "connections[1].connection_id",
        ),
        (
            WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
            "boolean_world_facts[1].fact_id",
        ),
        (
            WorldStateValidationIssueCode.UNEXPECTED_STATE,
            "boolean_world_facts[2].fact_id",
        ),
    ]

    missing = _issues(_state(boolean_world_facts=()))
    assert [(issue.code, issue.path) for issue in missing] == [
        (WorldStateValidationIssueCode.MISSING_STATE, "boolean_world_facts")
    ]


def test_validation_reports_valid_owner_runtime_references_after_overlay_issues() -> (
    None
):
    issues = _issues(
        _state(
            characters=(
                CharacterState(character_id="marin", location_id="missing"),
                CharacterState(character_id="sela", location_id="end"),
            ),
            objects=(
                ObjectState(
                    object_id="rope",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="missing"
                    ),
                ),
            ),
        )
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
            "characters[0].location_id",
        ),
        (
            WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
            "objects[0].placement.location_id",
        ),
    ]


def test_validation_suppresses_references_for_ambiguous_or_unexpected_owners_and_missing_possessor_state() -> (
    None
):
    issues = _issues(
        _state(
            characters=(CharacterState(character_id="marin", location_id="start"),),
            objects=(
                ObjectState(
                    object_id="rope",
                    placement=ObjectPossessedByCharacter(
                        placement_type="possessed_by_character", character_id="sela"
                    ),
                ),
                ObjectState(
                    object_id="rope",
                    placement=ObjectAtLocation(
                        placement_type="location", location_id="missing"
                    ),
                ),
                ObjectState(
                    object_id="extra",
                    placement=ObjectPossessedByCharacter(
                        placement_type="possessed_by_character", character_id="missing"
                    ),
                ),
            ),
        )
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        (WorldStateValidationIssueCode.MISSING_STATE, "characters"),
        (WorldStateValidationIssueCode.DUPLICATE_STATE_ID, "objects[1].object_id"),
        (WorldStateValidationIssueCode.UNEXPECTED_STATE, "objects[2].object_id"),
    ]


def test_validation_reports_unknown_object_possessor_at_its_runtime_path() -> None:
    issues = _issues(
        _state(
            objects=(
                ObjectState(
                    object_id="rope",
                    placement=ObjectPossessedByCharacter(
                        placement_type="possessed_by_character", character_id="missing"
                    ),
                ),
            )
        )
    )

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
            "objects[0].placement.character_id",
        ),
    ]


def test_world_state_validation_issue_and_error_enforce_strict_immutable_evidence() -> (
    None
):
    issue = WorldStateValidationIssue(
        code=WorldStateValidationIssueCode.MISSING_STATE,
        path="characters",
        message="missing runtime state for authored identifier 'marin'",
    )

    with pytest.raises(ValidationError):
        issue.path = "objects"
    with pytest.raises(ValidationError):
        WorldStateValidationIssue.model_validate(
            {
                "code": "missing-state",
                "path": "",
                "message": "missing",
                "extra": "forbidden",
            }
        )
    for invalid_issues in ((), [issue], ("not-an-issue",)):
        with pytest.raises((TypeError, ValueError)):
            WorldStateValidationError(invalid_issues)  # type: ignore[arg-type]
