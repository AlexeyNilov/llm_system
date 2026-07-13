from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from llm_system.game_packages._types import NonBlankText, RecordId
from llm_system.game_packages.entities import EntityCollectionDefinition
from llm_system.game_packages.spatial import SpatialGraphDefinition


class _StrictScenarioDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class BooleanWorldFactDefinition(_StrictScenarioDefinition):
    id: RecordId
    name: NonBlankText
    initial_value: bool


class ObjectUseBindingDefinition(_StrictScenarioDefinition):
    id: RecordId
    mechanic_id: RecordId
    object_id: RecordId
    target_location_id: RecordId
    fact_id: RecordId
    fact_value: bool


class ScenarioPackDefinition(BaseModel):
    schema_version: Literal[1]
    spatial_graph: SpatialGraphDefinition
    entity_collection: EntityCollectionDefinition
    boolean_world_facts: tuple[BooleanWorldFactDefinition, ...] = ()
    object_use_bindings: tuple[ObjectUseBindingDefinition, ...] = ()

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("schema_version", mode="before")
    @classmethod
    def schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("schema_version must be an integer literal")
        return value

    @field_validator("boolean_world_facts", "object_use_bindings", mode="before")
    @classmethod
    def normalize_yaml_catalog_lists_to_tuples(cls, value: object) -> object:
        if type(value) is list:
            return tuple(value)
        if type(value) is tuple:
            return value
        raise ValueError("scenario-pack catalogs must be lists or tuples")
