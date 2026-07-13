from uuid import UUID

from llm_system.simulation.actions import WaitActionProposal
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.changes import SimulationTimeChanged
from llm_system.simulation.events import ActorWaitedEvent
from llm_system.simulation.outcomes import SucceededOutcome


def resolve_wait(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> SucceededOutcome:
    proposal = action.submission.proposal
    if not isinstance(proposal, WaitActionProposal):
        raise TypeError("resolve_wait requires an authorized Wait action")

    current_time = action.world.state.simulation_time_seconds
    completion_time = current_time + proposal.duration_seconds
    return SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="wait-completed",
        resolved_at_seconds=completion_time,
        state_changes=(
            SimulationTimeChanged(
                change_type="simulation_time",
                from_seconds=current_time,
                to_seconds=completion_time,
            ),
        ),
        events=(
            ActorWaitedEvent(
                event_type="actor_waited",
                event_id=event_id,
                outcome_id=outcome_id,
                occurred_at_seconds=completion_time,
                actor_id=action.submission.actor_id,
                duration_seconds=proposal.duration_seconds,
            ),
        ),
    )
