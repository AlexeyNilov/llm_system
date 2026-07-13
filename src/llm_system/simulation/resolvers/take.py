from uuid import UUID

from llm_system.simulation.actions import TakeActionProposal
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.changes import ObjectPlacementChanged
from llm_system.simulation.events import ObjectTakenEvent
from llm_system.simulation.outcomes import RejectedOutcome, SucceededOutcome
from llm_system.simulation.state import ObjectAtLocation, ObjectPossessedByCharacter


def _accessible_placement(
    action: AuthorizedActorAction, object_id: str
) -> ObjectAtLocation | None:
    actor_id = action.submission.actor_id
    actor = next(
        item for item in action.world.state.characters if item.character_id == actor_id
    )
    object_state = next(
        (item for item in action.world.state.objects if item.object_id == object_id),
        None,
    )
    if object_state is None or not isinstance(object_state.placement, ObjectAtLocation):
        return None
    if object_state.placement.location_id != actor.location_id:
        return None
    return object_state.placement


def resolve_take(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> RejectedOutcome | SucceededOutcome:
    proposal = action.submission.proposal
    if not isinstance(proposal, TakeActionProposal):
        raise TypeError("resolve_take requires an authorized Take action")

    current_time = action.world.state.simulation_time_seconds
    previous_placement = _accessible_placement(action, proposal.object_id)
    if previous_placement is None:
        return RejectedOutcome(
            status="rejected",
            outcome_id=outcome_id,
            proposal_id=action.submission.proposal_id,
            reason_code="object-not-accessible",
            resolved_at_seconds=current_time,
        )
    possession = ObjectPossessedByCharacter(
        placement_type="possessed_by_character",
        character_id=action.submission.actor_id,
    )
    return SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="object-taken",
        resolved_at_seconds=current_time,
        state_changes=(
            ObjectPlacementChanged(
                change_type="object_placement",
                object_id=proposal.object_id,
                from_placement=previous_placement,
                to_placement=possession,
            ),
        ),
        events=(
            ObjectTakenEvent(
                event_type="object_taken",
                event_id=event_id,
                outcome_id=outcome_id,
                occurred_at_seconds=current_time,
                actor_id=action.submission.actor_id,
                object_id=proposal.object_id,
                previous_placement=previous_placement,
            ),
        ),
    )
