from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class ObjectUseMechanicDefinition(_StrictRuleDefinition):
    id: RecordId
    name: NonBlankText
    object_archetype_id: RecordId
    target_type: Literal["location"]
    duration_seconds: Annotated[int, Field(gt=0)]
    effect_type: Literal["set_boolean_world_fact"]


class RulePackDefinition(_StrictRuleDefinition):
    schema_version: Literal[1]
    object_archetypes: tuple[ObjectArchetypeDefinition, ...]
    character_archetypes: tuple[CharacterArchetypeDefinition, ...]
    decision_policies: tuple[DecisionPolicyDefinition, ...]
    object_use_mechanics: tuple[ObjectUseMechanicDefinition, ...] = ()

    @field_validator("schema_version", mode="before")
    @classmethod
    def schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("schema_version must be an integer literal")
        return value

    @field_validator(
        "object_archetypes",
        "character_archetypes",
        "decision_policies",
        "object_use_mechanics",
        mode="before",
    )
    @classmethod
    def normalize_yaml_catalog_lists_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("rule-pack catalogs must be lists or tuples")
