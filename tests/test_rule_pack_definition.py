from typing import Literal

import pytest
from pydantic import BaseModel, ValidationError

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    DecisionPolicyDefinition,
    ObjectArchetypeDefinition,
    RulePackDefinition,
)


def test_rule_pack_records_preserve_valid_stable_identifiers_and_names() -> None:
    object_archetype = ObjectArchetypeDefinition(
        id="medical-supplies", name="Medical Supplies"
    )
    character_archetype = CharacterArchetypeDefinition(
        id="field-medic", name="Field Medic"
    )

    assert object_archetype.id == "medical-supplies"
    assert character_archetype.name == "Field Medic"


@pytest.mark.parametrize("policy_type", ["rule", "llm", "hybrid"])
def test_policy_definitions_accept_each_supported_policy_type(
    policy_type: Literal["rule", "llm", "hybrid"],
) -> None:
    definition = DecisionPolicyDefinition(
        id="medic-routine", name="Medic Routine", policy_type=policy_type
    )

    assert definition.policy_type == policy_type


def test_rule_pack_preserves_yaml_catalog_order_as_deeply_immutable_tuples() -> None:
    definition = RulePackDefinition.model_validate(
        {
            "schema_version": 1,
            "object_archetypes": [
                {"id": "medical-supplies", "name": "Medical Supplies"},
                {"id": "field-tools", "name": "Field Tools"},
            ],
            "character_archetypes": [{"id": "field-medic", "name": "Field Medic"}],
            "decision_policies": [
                {"id": "medic-routine", "name": "Medic Routine", "policy_type": "rule"}
            ],
        }
    )

    assert [item.id for item in definition.object_archetypes] == [
        "medical-supplies",
        "field-tools",
    ]
    assert isinstance(definition.object_archetypes, tuple)
    with pytest.raises(ValidationError):
        definition.object_archetypes[0].name = "Changed"
    with pytest.raises(ValidationError):
        definition.object_archetypes = ()


def test_rule_pack_allows_all_catalogs_to_be_empty() -> None:
    definition = RulePackDefinition.model_validate(
        {
            "schema_version": 1,
            "object_archetypes": [],
            "character_archetypes": [],
            "decision_policies": [],
        }
    )

    assert definition.object_archetypes == ()
    assert definition.character_archetypes == ()
    assert definition.decision_policies == ()


def test_rule_pack_defers_duplicate_identifier_checks() -> None:
    definition = RulePackDefinition.model_validate(
        {
            "schema_version": 1,
            "object_archetypes": [
                {"id": "duplicate", "name": "First"},
                {"id": "duplicate", "name": "Second"},
            ],
            "character_archetypes": [],
            "decision_policies": [
                {"id": "duplicate", "name": "Duplicate", "policy_type": "llm"}
            ],
        }
    )

    assert len(definition.object_archetypes) == 2
    assert definition.character_archetypes == ()
    assert definition.decision_policies[0].id == "duplicate"


@pytest.mark.parametrize("schema_version", [True, "1", 2, None])
def test_rule_pack_rejects_non_integer_or_unsupported_schema_versions(
    schema_version: object,
) -> None:
    with pytest.raises(ValidationError):
        RulePackDefinition.model_validate(
            {
                "schema_version": schema_version,
                "object_archetypes": [],
                "character_archetypes": [],
                "decision_policies": [],
            }
        )


def test_rule_pack_requires_schema_version() -> None:
    with pytest.raises(ValidationError):
        RulePackDefinition.model_validate(
            {
                "object_archetypes": [],
                "character_archetypes": [],
                "decision_policies": [],
            }
        )


@pytest.mark.parametrize("catalog", ["archetype", {"id": "archetype"}, 1])
def test_rule_pack_rejects_non_list_or_tuple_catalogs(catalog: object) -> None:
    with pytest.raises(ValidationError):
        RulePackDefinition.model_validate(
            {
                "schema_version": 1,
                "object_archetypes": catalog,
                "character_archetypes": [],
                "decision_policies": [],
            }
        )


@pytest.mark.parametrize(
    "model, data",
    [
        (ObjectArchetypeDefinition, {"id": 1, "name": "Medical Supplies"}),
        (ObjectArchetypeDefinition, {"id": "medical-supplies", "name": "   "}),
        (CharacterArchetypeDefinition, {"id": "field-medic", "name": 1}),
        (
            DecisionPolicyDefinition,
            {
                "id": "medic-routine",
                "name": "Medic Routine",
                "policy_type": "scripted",
            },
        ),
    ],
)
def test_rule_pack_records_reject_invalid_values(
    model: type[BaseModel], data: object
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(data)


def test_rule_pack_records_forbid_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        DecisionPolicyDefinition.model_validate(
            {
                "id": "medic-routine",
                "name": "Medic Routine",
                "policy_type": "rule",
                "settings": {},
            }
        )
    with pytest.raises(ValidationError):
        RulePackDefinition.model_validate(
            {
                "schema_version": 1,
                "object_archetypes": [],
                "character_archetypes": [],
                "decision_policies": [],
                "actions": [],
            }
        )
