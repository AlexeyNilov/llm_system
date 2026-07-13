from uuid import UUID

from llm_system.game_packages.spatial import ConnectionDefinition
from llm_system.simulation.actions import MoveActionProposal
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.changes import (
    CharacterLocationChanged,
    SimulationTimeChanged,
)
from llm_system.simulation.events import ActorMovedEvent
from llm_system.simulation.outcomes import RejectedOutcome, SucceededOutcome


def _reject(
    action: AuthorizedActorAction, outcome_id: UUID, reason_code: str
) -> RejectedOutcome:
    return RejectedOutcome(
        status="rejected",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code=reason_code,
        resolved_at_seconds=action.world.state.simulation_time_seconds,
    )


def _succeed(
    action: AuthorizedActorAction,
    connection: ConnectionDefinition,
    outcome_id: UUID,
    event_id: UUID,
) -> SucceededOutcome:
    actor_id = action.submission.actor_id
    current_time = action.world.state.simulation_time_seconds
    completion_time = current_time + connection.base_traversal_seconds
    source_id = connection.source_location_id
    destination_id = connection.destination_location_id
    return SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="move-completed",
        resolved_at_seconds=completion_time,
        state_changes=(
            CharacterLocationChanged(
                change_type="character_location",
                character_id=actor_id,
                from_location_id=source_id,
                to_location_id=destination_id,
            ),
            SimulationTimeChanged(
                change_type="simulation_time",
                from_seconds=current_time,
                to_seconds=completion_time,
            ),
        ),
        events=(
            ActorMovedEvent(
                event_type="actor_moved",
                event_id=event_id,
                outcome_id=outcome_id,
                occurred_at_seconds=completion_time,
                actor_id=actor_id,
                connection_id=connection.id,
                from_location_id=source_id,
                to_location_id=destination_id,
            ),
        ),
    )


def resolve_move(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> RejectedOutcome | SucceededOutcome:
    proposal = action.submission.proposal
    if not isinstance(proposal, MoveActionProposal):
        raise TypeError("resolve_move requires an authorized Move action")

    definitions = action.world.packages.scenario_package.definition
    connection = next(
        (
            item
            for item in definitions.spatial_graph.connections
            if item.id == proposal.connection_id
        ),
        None,
    )
    if connection is None:
        return _reject(action, outcome_id, "unknown-connection")
    actor = next(
        item
        for item in action.world.state.characters
        if item.character_id == action.submission.actor_id
    )
    if actor.location_id != connection.source_location_id:
        return _reject(action, outcome_id, "actor-not-at-connection-source")
    runtime_connection = next(
        item
        for item in action.world.state.connections
        if item.connection_id == connection.id
    )
    if not runtime_connection.is_available:
        return _reject(action, outcome_id, "connection-unavailable")
    return _succeed(action, connection, outcome_id, event_id)
