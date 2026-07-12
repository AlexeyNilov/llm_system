from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from llm_system.game_packages.entities import EntityCollectionDefinition
from llm_system.game_packages.spatial import SpatialGraphDefinition


class ScenarioPackDefinition(BaseModel):
    schema_version: Literal[1]
    spatial_graph: SpatialGraphDefinition
    entity_collection: EntityCollectionDefinition

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("schema_version", mode="before")
    @classmethod
    def schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("schema_version must be an integer literal")
        return value
