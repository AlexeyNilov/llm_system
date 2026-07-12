import pytest
from pydantic import ValidationError

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    GamePackageValidationError,
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
    ValidationIssue,
    ValidationIssueCode,
    validate_game_packages,
)
from llm_system.game_packages.models import RequiredRulePack


def _valid_packages() -> tuple[LoadedRulePackage, LoadedScenarioPackage]:
    rule_package = LoadedRulePackage(
        manifest=RulePackageManifest(
            schema_version=1,
            package_id="forest-rules",
            package_version="1.2.3",
            package_type="rule",
            title="Forest Rules",
            entrypoint="content.yaml",
        ),
        definition=RulePackDefinition(
            schema_version=1,
            object_archetypes=(),
            character_archetypes=(
                CharacterArchetypeDefinition(id="scout", name="Scout"),
            ),
            decision_policies=(),
        ),
    )
    scenario_package = LoadedScenarioPackage(
        manifest=ScenarioPackageManifest(
            schema_version=1,
            package_id="lost-woods",
            package_version="2.0.1",
            package_type="scenario",
            title="Lost Woods",
            entrypoint="content.yaml",
            required_rule_pack=RequiredRulePack(
                package_id="forest-rules", package_version="1.2.3"
            ),
        ),
        definition=ScenarioPackDefinition(
            schema_version=1,
            spatial_graph=SpatialGraphDefinition(
                locations=(LocationDefinition(id="clearing", name="Clearing"),),
                connections=(),
            ),
            entity_collection=EntityCollectionDefinition(
                entities=(
                    PlayerCharacterDefinition(
                        entity_type="player_character",
                        id="marin",
                        name="Marin",
                        character_archetype_id="scout",
                        initial_location_id="clearing",
                    ),
                )
            ),
        ),
    )
    return rule_package, scenario_package


def test_validate_game_packages_returns_frozen_pair_preserving_valid_inputs() -> None:
    rule_package, scenario_package = _valid_packages()

    validated_packages = validate_game_packages(rule_package, scenario_package)

    assert validated_packages.rule_package is rule_package
    assert validated_packages.scenario_package is scenario_package
    with pytest.raises(ValidationError):
        validated_packages.rule_package = rule_package


def _packages(
    rule_content: dict[str, object], scenario_content: dict[str, object]
) -> tuple[LoadedRulePackage, LoadedScenarioPackage]:
    rule_package, scenario_package = _valid_packages()
    return (
        rule_package.model_copy(
            update={"definition": RulePackDefinition.model_validate(rule_content)}
        ),
        scenario_package.model_copy(
            update={
                "definition": ScenarioPackDefinition.model_validate(scenario_content)
            }
        ),
    )


def _issues(
    rule_package: LoadedRulePackage, scenario_package: LoadedScenarioPackage
) -> tuple[ValidationIssue, ...]:
    with pytest.raises(GamePackageValidationError) as error:
        validate_game_packages(rule_package, scenario_package)
    return error.value.issues


def _rule_content() -> dict[str, object]:
    return {
        "schema_version": 1,
        "object_archetypes": [{"id": "kit", "name": "Kit"}],
        "character_archetypes": [{"id": "scout", "name": "Scout"}],
        "decision_policies": [
            {"id": "routine", "name": "Routine", "policy_type": "rule"}
        ],
    }


def _scenario_content() -> dict[str, object]:
    return {
        "schema_version": 1,
        "spatial_graph": {
            "locations": [
                {"id": "start", "name": "Start"},
                {"id": "end", "name": "End"},
            ],
            "connections": [
                {
                    "id": "path",
                    "name": "Path",
                    "source_location_id": "start",
                    "destination_location_id": "end",
                    "base_traversal_seconds": 1,
                }
            ],
        },
        "entity_collection": {
            "entities": [
                {
                    "entity_type": "player_character",
                    "id": "marin",
                    "name": "Marin",
                    "character_archetype_id": "scout",
                    "initial_location_id": "start",
                }
            ]
        },
    }


def test_validation_reports_reference_and_policy_issue_codes_at_authored_paths() -> (
    None
):
    rule = _rule_content()
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [{"id": "start", "name": "Start"}],
        "connections": [
            {
                "id": "bad-path",
                "name": "Bad Path",
                "source_location_id": "start",
                "destination_location_id": "missing",
                "base_traversal_seconds": 1,
            }
        ],
    }
    scenario["entity_collection"] = {
        "entities": [
            {
                "entity_type": "object",
                "id": "object",
                "name": "Object",
                "object_archetype_id": "missing",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "missing",
                },
            },
            {
                "entity_type": "npc_character",
                "id": "npc",
                "name": "NPC",
                "character_archetype_id": "missing",
                "initial_location_id": "missing",
                "identity_summary": "A person.",
                "goals": [{"id": "goal", "description": "Act."}],
                "decision_policy": {"policy_type": "llm", "policy_id": "routine"},
            },
        ]
    }

    issues = _issues(*_packages(rule, scenario))

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            ValidationIssueCode.INVALID_PLAYER_COUNT,
            "scenario.definition.entity_collection.entities",
        ),
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.spatial_graph.connections[0].destination_location_id",
        ),
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.entity_collection.entities[0].object_archetype_id",
        ),
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.entity_collection.entities[0].initial_placement.location_id",
        ),
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.entity_collection.entities[1].character_archetype_id",
        ),
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.entity_collection.entities[1].initial_location_id",
        ),
        (
            ValidationIssueCode.POLICY_TYPE_MISMATCH,
            "scenario.definition.entity_collection.entities[1].decision_policy.policy_type",
        ),
    ]


def test_validation_handles_duplicate_namespaces_and_avoids_unknown_reference_cascades() -> (
    None
):
    rule = _rule_content()
    rule["object_archetypes"] = [
        {"id": "kit", "name": "One"},
        {"id": "kit", "name": "Two"},
    ]
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [
            {"id": "start", "name": "Start"},
            {"id": "start", "name": "Again"},
        ],
        "connections": [],
    }
    scenario["entity_collection"] = {
        "entities": [
            {
                "entity_type": "object",
                "id": "object",
                "name": "Object",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "possessed",
                    "character_id": "target",
                },
            },
            {
                "entity_type": "object",
                "id": "target",
                "name": "One",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "start",
                },
            },
            {
                "entity_type": "object",
                "id": "target",
                "name": "Two",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "start",
                },
            },
        ]
    }

    issues = _issues(*_packages(rule, scenario))

    assert [issue.code for issue in issues] == [
        ValidationIssueCode.DUPLICATE_ID,
        ValidationIssueCode.DUPLICATE_ID,
        ValidationIssueCode.DUPLICATE_ID,
        ValidationIssueCode.INVALID_PLAYER_COUNT,
    ]
    assert all(
        issue.path
        != "scenario.definition.entity_collection.entities[0].initial_placement.character_id"
        for issue in issues
    )


def test_validation_distinguishes_missing_and_non_character_possession_targets() -> (
    None
):
    rule = _rule_content()
    scenario = _scenario_content()
    scenario["entity_collection"] = {
        "entities": [
            {
                "entity_type": "player_character",
                "id": "marin",
                "name": "Marin",
                "character_archetype_id": "scout",
                "initial_location_id": "start",
            },
            {
                "entity_type": "object",
                "id": "held",
                "name": "Held",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "possessed",
                    "character_id": "crate",
                },
            },
            {
                "entity_type": "object",
                "id": "crate",
                "name": "Crate",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "start",
                },
            },
        ]
    }

    issues = _issues(*_packages(rule, scenario))

    assert issues[0].code is ValidationIssueCode.INVALID_POSSESSION_TARGET


def test_validation_reports_missing_possession_target_as_unknown_reference() -> None:
    scenario = _scenario_content()
    scenario["entity_collection"] = {
        "entities": [
            {
                "entity_type": "player_character",
                "id": "marin",
                "name": "Marin",
                "character_archetype_id": "scout",
                "initial_location_id": "start",
            },
            {
                "entity_type": "object",
                "id": "held",
                "name": "Held",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "possessed",
                    "character_id": "missing",
                },
            },
        ]
    }

    issues = _issues(*_packages(_rule_content(), scenario))

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.entity_collection.entities[1].initial_placement.character_id",
        )
    ]


def test_validation_accepts_one_way_parallel_edges_and_unused_definitions() -> None:
    rule = _rule_content()
    rule["object_archetypes"] = [{"id": "unused", "name": "Unused"}]
    rule["decision_policies"] = [
        {"id": "unused-policy", "name": "Unused", "policy_type": "llm"}
    ]
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [{"id": "start", "name": "Start"}, {"id": "end", "name": "End"}],
        "connections": [
            {
                "id": "first",
                "name": "First",
                "source_location_id": "start",
                "destination_location_id": "end",
                "base_traversal_seconds": 1,
            },
            {
                "id": "second",
                "name": "Second",
                "source_location_id": "start",
                "destination_location_id": "end",
                "base_traversal_seconds": 2,
            },
        ],
    }

    validated = validate_game_packages(*_packages(rule, scenario))

    assert (
        validated.scenario_package.definition.spatial_graph.connections[1].id
        == "second"
    )


def test_validation_reports_self_loop_and_unreachable_locations_in_fixed_order() -> (
    None
):
    rule = _rule_content()
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [
            {"id": "start", "name": "Start"},
            {"id": "isolated", "name": "Isolated"},
        ],
        "connections": [
            {
                "id": "loop",
                "name": "Loop",
                "source_location_id": "start",
                "destination_location_id": "start",
                "base_traversal_seconds": 1,
            },
        ],
    }

    issues = _issues(*_packages(rule, scenario))

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            ValidationIssueCode.INVALID_SELF_LOOP,
            "scenario.definition.spatial_graph.connections[0].source_location_id",
        ),
        (
            ValidationIssueCode.UNREACHABLE_LOCATION,
            "scenario.definition.spatial_graph.locations[1].id",
        ),
    ]


def test_missing_connection_endpoint_suppresses_reachability_cascade() -> None:
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [
            {"id": "start", "name": "Start"},
            {"id": "otherwise-unreachable", "name": "Otherwise Unreachable"},
        ],
        "connections": [
            {
                "id": "broken",
                "name": "Broken",
                "source_location_id": "start",
                "destination_location_id": "missing",
                "base_traversal_seconds": 1,
            }
        ],
    }

    issues = _issues(*_packages(_rule_content(), scenario))

    assert [(issue.code, issue.path) for issue in issues] == [
        (
            ValidationIssueCode.UNKNOWN_REFERENCE,
            "scenario.definition.spatial_graph.connections[0].destination_location_id",
        )
    ]


def test_dependency_mismatch_suppresses_only_scenario_to_rule_checks() -> None:
    rule, scenario = _packages(_rule_content(), _scenario_content())
    scenario = scenario.model_copy(
        update={
            "manifest": scenario.manifest.model_copy(
                update={
                    "required_rule_pack": RequiredRulePack(
                        package_id="other", package_version="1.0.0"
                    )
                }
            )
        }
    )
    invalid_scenario = scenario.definition.model_copy(
        update={
            "entity_collection": EntityCollectionDefinition.model_validate(
                {
                    "entities": [
                        {
                            "entity_type": "player_character",
                            "id": "marin",
                            "name": "Marin",
                            "character_archetype_id": "missing",
                            "initial_location_id": "missing",
                        }
                    ]
                }
            )
        }
    )
    scenario = scenario.model_copy(update={"definition": invalid_scenario})

    issues = _issues(rule, scenario)

    assert [issue.code for issue in issues] == [
        ValidationIssueCode.DEPENDENCY_MISMATCH,
        ValidationIssueCode.UNKNOWN_REFERENCE,
    ]


def test_validation_issues_are_frozen_and_tuple_backed() -> None:
    rule, scenario = _packages(_rule_content(), _scenario_content())
    scenario = scenario.model_copy(
        update={
            "definition": ScenarioPackDefinition.model_validate(
                {**_scenario_content(), "entity_collection": {"entities": []}}
            )
        }
    )

    issues = _issues(rule, scenario)

    assert isinstance(issues, tuple)
    assert issues[0].message.strip()
    with pytest.raises(ValidationError):
        issues[0].path = "changed"


def test_validation_issue_and_error_reject_blank_or_empty_diagnostics() -> None:
    with pytest.raises(ValidationError):
        ValidationIssue(
            code=ValidationIssueCode.DUPLICATE_ID,
            path="   ",
            message="Useful message",
        )
    with pytest.raises(ValidationError):
        ValidationIssue(
            code=ValidationIssueCode.DUPLICATE_ID,
            path="rule.definition.object_archetypes[1].id",
            message="   ",
        )
    with pytest.raises(ValueError):
        GamePackageValidationError(())


def test_validation_reports_all_duplicate_namespaces_in_fixed_order() -> None:
    rule = _rule_content()
    rule["object_archetypes"] = [
        {"id": "kit", "name": "First"},
        {"id": "kit", "name": "Second"},
    ]
    rule["character_archetypes"] = [
        {"id": "scout", "name": "First"},
        {"id": "scout", "name": "Second"},
    ]
    rule["decision_policies"] = [
        {"id": "routine", "name": "First", "policy_type": "rule"},
        {"id": "routine", "name": "Second", "policy_type": "rule"},
    ]
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [
            {"id": "start", "name": "First"},
            {"id": "start", "name": "Second"},
            {"id": "end", "name": "End"},
        ],
        "connections": [
            {
                "id": "path",
                "name": "First",
                "source_location_id": "start",
                "destination_location_id": "end",
                "base_traversal_seconds": 1,
            },
            {
                "id": "path",
                "name": "Second",
                "source_location_id": "start",
                "destination_location_id": "end",
                "base_traversal_seconds": 1,
            },
        ],
    }
    scenario["entity_collection"] = {
        "entities": [
            {
                "entity_type": "player_character",
                "id": "player",
                "name": "Player",
                "character_archetype_id": "scout",
                "initial_location_id": "start",
            },
            {
                "entity_type": "npc_character",
                "id": "npc",
                "name": "NPC",
                "character_archetype_id": "scout",
                "initial_location_id": "start",
                "identity_summary": "A person.",
                "goals": [
                    {"id": "act", "description": "First."},
                    {"id": "act", "description": "Second."},
                ],
                "decision_policy": {"policy_type": "rule", "policy_id": "routine"},
            },
            {
                "entity_type": "object",
                "id": "object",
                "name": "First",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "start",
                },
            },
            {
                "entity_type": "object",
                "id": "object",
                "name": "Second",
                "object_archetype_id": "kit",
                "initial_placement": {
                    "placement_type": "location",
                    "location_id": "start",
                },
            },
        ]
    }

    issues = _issues(*_packages(rule, scenario))

    assert [issue.path for issue in issues] == [
        "rule.definition.object_archetypes[1].id",
        "rule.definition.character_archetypes[1].id",
        "rule.definition.decision_policies[1].id",
        "scenario.definition.spatial_graph.locations[1].id",
        "scenario.definition.spatial_graph.connections[1].id",
        "scenario.definition.entity_collection.entities[3].id",
        "scenario.definition.entity_collection.entities[1].goals[1].id",
    ]


def test_identifier_text_may_be_reused_across_typed_namespaces() -> None:
    rule = _rule_content()
    rule["object_archetypes"] = [{"id": "shared", "name": "Object"}]
    rule["character_archetypes"] = [{"id": "shared", "name": "Character"}]
    rule["decision_policies"] = [
        {"id": "shared", "name": "Policy", "policy_type": "rule"}
    ]
    scenario = _scenario_content()
    scenario["spatial_graph"] = {
        "locations": [{"id": "shared", "name": "Location"}],
        "connections": [],
    }
    scenario["entity_collection"] = {
        "entities": [
            {
                "entity_type": "player_character",
                "id": "shared",
                "name": "Player",
                "character_archetype_id": "shared",
                "initial_location_id": "shared",
            }
        ]
    }

    validated = validate_game_packages(*_packages(rule, scenario))

    assert (
        validated.scenario_package.definition.entity_collection.entities[0].id
        == "shared"
    )
