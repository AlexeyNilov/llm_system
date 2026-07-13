from uuid import UUID

from llm_system.simulation.actions import (
    CharacterTarget,
    ConnectionTarget,
    LocationTarget,
    ObjectTarget,
    ObservationTarget,
    ObserveActionProposal,
    SurroundingsTarget,
)
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.events import ActorObservedEvent
from llm_system.simulation.outcomes import RejectedOutcome, SucceededOutcome
from llm_system.simulation.perception import (
    CharacterObserved,
    ConnectionObserved,
    LocationObserved,
    ObjectObserved,
    Observation,
)
from llm_system.simulation.perception_engine import project_current_perception


def _matches_target(observation: Observation, target: ObservationTarget) -> bool:
    if isinstance(target, LocationTarget):
        return isinstance(observation, LocationObserved) and (
            observation.location_id == target.location_id
        )
    if isinstance(target, ConnectionTarget):
        return isinstance(observation, ConnectionObserved) and (
            observation.connection_id == target.connection_id
        )
    if isinstance(target, CharacterTarget):
        return isinstance(observation, CharacterObserved) and (
            observation.character_id == target.character_id
        )
    return (
        isinstance(target, ObjectTarget)
        and isinstance(observation, ObjectObserved)
        and (observation.object_id == target.object_id)
    )


def _target_is_perceptible(
    action: AuthorizedActorAction, target: ObservationTarget
) -> bool:
    snapshot = project_current_perception(action.world, action.submission.actor_id)
    if isinstance(target, SurroundingsTarget):
        return True
    return any(
        _matches_target(observation, target) for observation in snapshot.observations
    )


def resolve_observe(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> RejectedOutcome | SucceededOutcome:
    proposal = action.submission.proposal
    if not isinstance(proposal, ObserveActionProposal):
        raise TypeError("resolve_observe requires an authorized Observe action")

    current_time = action.world.state.simulation_time_seconds
    if not _target_is_perceptible(action, proposal.target):
        return RejectedOutcome(
            status="rejected",
            outcome_id=outcome_id,
            proposal_id=action.submission.proposal_id,
            reason_code="target-not-perceptible",
            resolved_at_seconds=current_time,
        )
    return SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="observation-completed",
        resolved_at_seconds=current_time,
        state_changes=(),
        events=(
            ActorObservedEvent(
                event_type="actor_observed",
                event_id=event_id,
                outcome_id=outcome_id,
                occurred_at_seconds=current_time,
                actor_id=action.submission.actor_id,
                target=proposal.target,
            ),
        ),
    )
