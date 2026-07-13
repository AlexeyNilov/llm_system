from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator

from llm_system.game_packages.models import PackageId, PackageVersion
from llm_system.simulation._types import _StrictContract
from llm_system.simulation.events import CanonicalEvent
from llm_system.simulation.scheduling import ScheduledActivityQueue
from llm_system.simulation.state import WorldState

NonNegativeRevision = Annotated[int, Field(ge=0)]
PositiveInsertionSequence = Annotated[int, Field(gt=0)]


class PackageReference(_StrictContract):
    package_id: PackageId
    package_version: PackageVersion


class StoredWorld(_StrictContract):
    payload_schema_version: Literal[1]
    world_id: UUID
    revision: NonNegativeRevision
    rule_package: PackageReference
    scenario_package: PackageReference
    state: WorldState
    scheduled_queue: ScheduledActivityQueue

    @field_validator("payload_schema_version", mode="before")
    @classmethod
    def payload_schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("payload_schema_version must be an integer literal")
        return value


class StoredCanonicalEvent(_StrictContract):
    insertion_sequence: PositiveInsertionSequence
    world_id: UUID
    resulting_world_revision: NonNegativeRevision
    event: CanonicalEvent
