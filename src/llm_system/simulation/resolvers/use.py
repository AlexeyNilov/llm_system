from uuid import UUID

from llm_system.game_packages.rules import ObjectUseMechanicDefinition
from llm_system.game_packages.scenarios import ObjectUseBindingDefinition
from llm_system.simulation.actions import LocationTarget, UseActionProposal
from llm_system.simulation.authorization import AuthorizedActorAction
from llm_system.simulation.changes import (
    BooleanWorldFactChanged,
    SimulationTimeChanged,
)
from llm_system.simulation.events import ObjectUsedEvent
from llm_system.simulation.outcomes import RejectedOutcome, SucceededOutcome
from llm_system.simulation.state import (
    BooleanWorldFactState,
    ObjectPossessedByCharacter,
)

ApplicableUse = tuple[
    ObjectUseBindingDefinition,
    ObjectUseMechanicDefinition,
    BooleanWorldFactState,
]


def _binding(
    action: AuthorizedActorAction, proposal: UseActionProposal
) -> ObjectUseBindingDefinition | None:
    if not isinstance(proposal.target, LocationTarget):
        return None
    bindings = action.world.packages.scenario_package.definition.object_use_bindings
    return next(
        (
            item
            for item in bindings
            if item.object_id == proposal.object_id
            and item.target_location_id == proposal.target.location_id
        ),
        None,
    )


def _applicable_use(
    action: AuthorizedActorAction, proposal: UseActionProposal
) -> ApplicableUse | None:
    binding = _binding(action, proposal)
    if binding is None:
        return None
    actor_id = action.submission.actor_id
    actor = next(
        item for item in action.world.state.characters if item.character_id == actor_id
    )
    object_state = next(
        item
        for item in action.world.state.objects
        if item.object_id == proposal.object_id
    )
    placement = object_state.placement
    if actor.location_id != binding.target_location_id or not (
        isinstance(placement, ObjectPossessedByCharacter)
        and placement.character_id == actor_id
    ):
        return None
    fact = next(
        item
        for item in action.world.state.boolean_world_facts
        if item.fact_id == binding.fact_id
    )
    if fact.value == binding.fact_value:
        return None
    mechanics = action.world.packages.rule_package.definition.object_use_mechanics
    mechanic = next(item for item in mechanics if item.id == binding.mechanic_id)
    return binding, mechanic, fact


def _rejected(action: AuthorizedActorAction, outcome_id: UUID) -> RejectedOutcome:
    return RejectedOutcome(
        status="rejected",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="use-not-applicable",
        resolved_at_seconds=action.world.state.simulation_time_seconds,
    )


def resolve_use(
    action: AuthorizedActorAction, *, outcome_id: UUID, event_id: UUID
) -> RejectedOutcome | SucceededOutcome:
    proposal = action.submission.proposal
    if not isinstance(proposal, UseActionProposal):
        raise TypeError("resolve_use requires an authorized Use action")
    applicable = _applicable_use(action, proposal)
    if applicable is None:
        return _rejected(action, outcome_id)
    binding, mechanic, fact = applicable
    current_time = action.world.state.simulation_time_seconds
    completion_time = current_time + mechanic.duration_seconds
    return SucceededOutcome(
        status="succeeded",
        outcome_id=outcome_id,
        proposal_id=action.submission.proposal_id,
        reason_code="object-used",
        resolved_at_seconds=completion_time,
        state_changes=(
            BooleanWorldFactChanged(
                change_type="boolean_world_fact",
                fact_id=binding.fact_id,
                from_value=fact.value,
                to_value=binding.fact_value,
            ),
            SimulationTimeChanged(
                change_type="simulation_time",
                from_seconds=current_time,
                to_seconds=completion_time,
            ),
        ),
        events=(
            ObjectUsedEvent(
                event_type="object_used",
                event_id=event_id,
                outcome_id=outcome_id,
                occurred_at_seconds=completion_time,
                actor_id=action.submission.actor_id,
                object_id=proposal.object_id,
                target=proposal.target,
            ),
        ),
    )
