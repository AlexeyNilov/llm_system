from typing import assert_never
from uuid import UUID

from llm_system.simulation.actions import (
    ActorActionOperation,
    HelpActionProposal,
    MoveActionProposal,
    ObserveActionProposal,
    SpeakActionProposal,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.outcomes import Outcome
from llm_system.simulation.resolvers.move import resolve_move
from llm_system.simulation.resolvers.observe import resolve_observe
from llm_system.simulation.resolvers.speak import resolve_speak
from llm_system.simulation.resolvers.wait import resolve_wait


class OperationResolverUnavailableError(RuntimeError):
    operation: ActorActionOperation

    def __init__(self, operation: ActorActionOperation) -> None:
        super().__init__(f"no resolver is available for actor operation: {operation}")
        self.operation = operation


def dispatch_actor_action(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> Outcome:
    proposal = action.submission.proposal
    if isinstance(proposal, MoveActionProposal):
        return resolve_move(action, outcome_id=outcome_id, event_id=event_id)
    if isinstance(proposal, WaitActionProposal):
        return resolve_wait(action, outcome_id=outcome_id, event_id=event_id)
    if isinstance(proposal, ObserveActionProposal):
        return resolve_observe(action, outcome_id=outcome_id, event_id=event_id)
    if isinstance(proposal, SpeakActionProposal):
        return resolve_speak(action, outcome_id=outcome_id, event_id=event_id)
    if isinstance(
        proposal,
        (
            TakeActionProposal,
            UseActionProposal,
            HelpActionProposal,
        ),
    ):
        raise OperationResolverUnavailableError(proposal.operation)
    assert_never(proposal)
