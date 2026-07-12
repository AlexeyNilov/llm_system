from pathlib import Path

from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationPlacementDefinition,
    NpcCharacterDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
    PossessedPlacementDefinition,
    ValidatedGamePackages,
    load_game_package,
    validate_game_packages,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_RULE_PACKAGE_DIRECTORY = (
    _REPOSITORY_ROOT / "game_packages" / "rules" / "greybridge-rules" / "0.1.0"
)
_SCENARIO_PACKAGE_DIRECTORY = (
    _REPOSITORY_ROOT / "game_packages" / "scenarios" / "storm-at-greybridge" / "0.1.0"
)


def test_greybridge_packages_load_and_validate_real_authored_content() -> None:
    rule_package = load_game_package(_RULE_PACKAGE_DIRECTORY)
    scenario_package = load_game_package(_SCENARIO_PACKAGE_DIRECTORY)

    assert isinstance(rule_package, LoadedRulePackage)
    assert isinstance(scenario_package, LoadedScenarioPackage)
    assert isinstance(
        validate_game_packages(rule_package, scenario_package), ValidatedGamePackages
    )

    assert rule_package.manifest.package_id == "greybridge-rules"
    assert rule_package.manifest.package_version == "0.1.0"
    assert rule_package.manifest.entrypoint == "rules.yaml"
    assert [
        archetype.id for archetype in rule_package.definition.object_archetypes
    ] == ["medicine", "reinforcement-materials"]
    assert [
        archetype.id for archetype in rule_package.definition.character_archetypes
    ] == ["traveler", "courier", "caretaker"]
    assert [
        (policy.id, policy.policy_type)
        for policy in rule_package.definition.decision_policies
    ] == [
        ("courier-llm-policy", "llm"),
        ("caretaker-rule-policy", "rule"),
    ]

    assert scenario_package.manifest.package_id == "storm-at-greybridge"
    assert scenario_package.manifest.package_version == "0.1.0"
    assert scenario_package.manifest.entrypoint == "scenario.yaml"
    assert scenario_package.manifest.required_rule_pack.package_id == "greybridge-rules"
    assert scenario_package.manifest.required_rule_pack.package_version == "0.1.0"
    spatial_graph = scenario_package.definition.spatial_graph
    assert [location.id for location in spatial_graph.locations] == [
        "greybridge-waystation",
        "greybridge-span",
        "far-bank",
    ]
    assert [
        (
            connection.id,
            connection.source_location_id,
            connection.destination_location_id,
            connection.base_traversal_seconds,
        )
        for connection in spatial_graph.connections
    ] == [
        ("waystation-to-span", "greybridge-waystation", "greybridge-span", 60),
        ("span-to-waystation", "greybridge-span", "greybridge-waystation", 60),
        ("span-to-far-bank", "greybridge-span", "far-bank", 120),
        ("far-bank-to-span", "far-bank", "greybridge-span", 120),
    ]

    entities = scenario_package.definition.entity_collection.entities
    assert [entity.id for entity in entities] == [
        "player",
        "injured-courier",
        "bridge-caretaker",
        "medicine",
        "reinforcement-materials",
    ]
    player, courier, caretaker, medicine, materials = entities
    assert isinstance(player, PlayerCharacterDefinition)
    assert player.name == "Traveler"
    assert player.character_archetype_id == "traveler"
    assert player.initial_location_id == "greybridge-waystation"
    assert isinstance(courier, NpcCharacterDefinition)
    assert courier.character_archetype_id == "courier"
    assert courier.initial_location_id == "greybridge-waystation"
    assert courier.decision_policy.policy_id == "courier-llm-policy"
    assert courier.decision_policy.policy_type == "llm"
    assert [goal.id for goal in courier.goals] == ["deliver-medicine", "protect-injury"]
    assert courier.identity_summary
    assert courier.initial_plan
    assert isinstance(caretaker, NpcCharacterDefinition)
    assert caretaker.character_archetype_id == "caretaker"
    assert caretaker.initial_location_id == "greybridge-span"
    assert caretaker.decision_policy.policy_id == "caretaker-rule-policy"
    assert caretaker.decision_policy.policy_type == "rule"
    assert [goal.id for goal in caretaker.goals] == [
        "protect-people",
        "preserve-bridge",
        "protect-supplies",
        "reach-safety",
    ]
    assert caretaker.identity_summary
    assert caretaker.initial_plan
    assert isinstance(medicine, ObjectDefinition)
    assert medicine.object_archetype_id == "medicine"
    assert isinstance(medicine.initial_placement, PossessedPlacementDefinition)
    assert medicine.initial_placement.character_id == "injured-courier"
    assert isinstance(materials, ObjectDefinition)
    assert materials.object_archetype_id == "reinforcement-materials"
    assert isinstance(materials.initial_placement, LocationPlacementDefinition)
    assert materials.initial_placement.location_id == "greybridge-waystation"
