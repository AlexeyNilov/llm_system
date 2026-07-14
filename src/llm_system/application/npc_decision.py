from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm_system.game_packages._types import NonBlankText
from llm_system.game_packages.entities import GoalDefinition
from llm_system.simulation._types import AuthoredId
from llm_system.simulation.actions import (
    ActorActionProposal,
    LocationTarget,
    MoveActionProposal,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)
from llm_system.simulation.perception import (
    ConnectionObserved,
    LocationObserved,
    ObjectObserved,
    PerceptionSnapshot,
)
from llm_system.simulation.state import ObjectAtLocation, ObjectPossessedByCharacter

_CARETAKER_ID = "bridge-caretaker"
_MATERIALS_ID = "reinforcement-materials"
_SPAN_ID = "greybridge-span"
_WAYSTATION_ID = "greybridge-waystation"
_TO_SPAN_CONNECTION_ID = "waystation-to-span"
_TO_WAYSTATION_CONNECTION_ID = "span-to-waystation"


class NpcDecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    decision_context_id: UUID
    npc_id: AuthoredId
    identity_summary: NonBlankText
    goals: tuple[GoalDefinition, ...] = Field(min_length=1)
    current_plan: NonBlankText | None
    perception: PerceptionSnapshot

    @model_validator(mode="after")
    def require_matching_perception_observer(self) -> Self:
        if self.perception.observer_id != self.npc_id:
            raise ValueError("perception observer must match NPC identity")
        return self


def decide_greybridge_caretaker(
    context: NpcDecisionContext,
) -> ActorActionProposal:
    if context.npc_id != _CARETAKER_ID:
        raise ValueError("caretaker policy requires bridge-caretaker")

    location_ids = {
        observation.location_id
        for observation in context.perception.observations
        if isinstance(observation, LocationObserved)
    }
    available_connection_ids = {
        observation.connection_id
        for observation in context.perception.observations
        if isinstance(observation, ConnectionObserved) and observation.is_available
    }
    material_observations = tuple(
        observation
        for observation in context.perception.observations
        if isinstance(observation, ObjectObserved)
        and observation.object_id == _MATERIALS_ID
    )
    possesses_materials = any(
        isinstance(observation.placement, ObjectPossessedByCharacter)
        and observation.placement.character_id == _CARETAKER_ID
        for observation in material_observations
    )

    if possesses_materials and _SPAN_ID in location_ids:
        return UseActionProposal(
            operation="use",
            object_id=_MATERIALS_ID,
            target=LocationTarget(target_type="location", location_id=_SPAN_ID),
        )
    if (
        possesses_materials
        and _WAYSTATION_ID in location_ids
        and _TO_SPAN_CONNECTION_ID in available_connection_ids
    ):
        return MoveActionProposal(
            operation="move", connection_id=_TO_SPAN_CONNECTION_ID
        )
    if any(
        isinstance(observation.placement, ObjectAtLocation)
        and observation.placement.location_id in location_ids
        for observation in material_observations
    ):
        return TakeActionProposal(operation="take", object_id=_MATERIALS_ID)
    if (
        not possesses_materials
        and _SPAN_ID in location_ids
        and _TO_WAYSTATION_CONNECTION_ID in available_connection_ids
    ):
        return MoveActionProposal(
            operation="move", connection_id=_TO_WAYSTATION_CONNECTION_ID
        )
    return WaitActionProposal(operation="wait", duration_seconds=60)
