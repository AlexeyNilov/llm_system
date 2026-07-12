from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from llm_system.game_packages._types import DecisionPolicyType, NonBlankText, RecordId


class _StrictRuleDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ObjectArchetypeDefinition(_StrictRuleDefinition):
    id: RecordId
    name: NonBlankText


class CharacterArchetypeDefinition(_StrictRuleDefinition):
    id: RecordId
    name: NonBlankText


class DecisionPolicyDefinition(_StrictRuleDefinition):
    id: RecordId
    name: NonBlankText
    policy_type: DecisionPolicyType


class RulePackDefinition(_StrictRuleDefinition):
    schema_version: Literal[1]
    object_archetypes: tuple[ObjectArchetypeDefinition, ...]
    character_archetypes: tuple[CharacterArchetypeDefinition, ...]
    decision_policies: tuple[DecisionPolicyDefinition, ...]

    @field_validator("schema_version", mode="before")
    @classmethod
    def schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("schema_version must be an integer literal")
        return value

    @field_validator(
        "object_archetypes", "character_archetypes", "decision_policies", mode="before"
    )
    @classmethod
    def normalize_yaml_catalog_lists_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("rule-pack catalogs must be lists or tuples")
