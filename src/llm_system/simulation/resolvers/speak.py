from uuid import UUID

from llm_system.simulation.actions import SpeakActionProposal
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.events import ActorSpokeEvent
from llm_system.simulation.outcomes import RejectedOutcome, SucceededOutcome


def _recipient_is_audible(action: AuthorizedActorAction, recipient_id: str) -> bool:
    speaker_id = action.submission.actor_id
    speaker = next(
        character
        for character in action.world.state.characters
        if character.character_id == speaker_id
    )
    return any(
        character.character_id == recipient_id
        and character.character_id != speaker_id
        and character.location_id == speaker.location_id
        for character in action.world.state.characters
    )


def resolve_speak(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> RejectedOutcome | SucceededOutcome:
    proposal = action.submission.proposal
    if not isinstance(proposal, SpeakActionProposal):
        raise TypeError("resolve_speak requires an authorized Speak action")

    current_time = action.world.state.simulation_time_seconds
    if not _recipient_is_audible(action, proposal.character_id):
        return RejectedOutcome(
            status="rejected",
            outcome_id=outcome_id,
            proposal_id=action.submission.proposal_id,
            reason_code="recipient-not-audible",
            resolved_at_seconds=current_time,
        )
    return SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="speech-completed",
        resolved_at_seconds=current_time,
        state_changes=(),
        events=(
            ActorSpokeEvent(
                event_type="actor_spoke",
                event_id=event_id,
                outcome_id=outcome_id,
                occurred_at_seconds=current_time,
                speaker_id=action.submission.actor_id,
                recipient_id=proposal.character_id,
                utterance=proposal.utterance,
            ),
        ),
    )
