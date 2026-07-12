from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from llm_system.game_packages._types import DecisionPolicyType, NonBlankText, RecordId


class _StrictDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class LocationPlacementDefinition(_StrictDefinition):
    placement_type: Literal["location"]
    location_id: RecordId


class PossessedPlacementDefinition(_StrictDefinition):
    placement_type: Literal["possessed"]
    character_id: RecordId


ObjectPlacementDefinition = Annotated[
    LocationPlacementDefinition | PossessedPlacementDefinition,
    Field(discriminator="placement_type"),
]


class GoalDefinition(_StrictDefinition):
    id: RecordId
    description: NonBlankText


class DecisionPolicyReference(_StrictDefinition):
    policy_type: DecisionPolicyType
    policy_id: RecordId


class ObjectDefinition(_StrictDefinition):
    entity_type: Literal["object"]
    id: RecordId
    name: NonBlankText
    object_archetype_id: RecordId
    initial_placement: ObjectPlacementDefinition


class PlayerCharacterDefinition(_StrictDefinition):
    entity_type: Literal["player_character"]
    id: RecordId
    name: NonBlankText
    character_archetype_id: RecordId
    initial_location_id: RecordId


class NpcCharacterDefinition(_StrictDefinition):
    entity_type: Literal["npc_character"]
    id: RecordId
    name: NonBlankText
    character_archetype_id: RecordId
    initial_location_id: RecordId
    identity_summary: NonBlankText
    goals: tuple[GoalDefinition, ...] = Field(min_length=1)
    initial_plan: NonBlankText | None = None
    decision_policy: DecisionPolicyReference

    @field_validator("goals", mode="before")
    @classmethod
    def normalize_yaml_goal_lists_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("NPC goals must be a list or tuple")


CharacterDefinition = Annotated[
    PlayerCharacterDefinition | NpcCharacterDefinition,
    Field(discriminator="entity_type"),
]
EntityDefinition = Annotated[
    ObjectDefinition | PlayerCharacterDefinition | NpcCharacterDefinition,
    Field(discriminator="entity_type"),
]


class EntityCollectionDefinition(_StrictDefinition):
    entities: tuple[EntityDefinition, ...]

    @field_validator("entities", mode="before")
    @classmethod
    def normalize_yaml_entity_lists_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("entity collections must be lists or tuples")
