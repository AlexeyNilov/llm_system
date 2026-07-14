from collections.abc import Callable
from typing import Literal, TypeAlias
from uuid import UUID

from llm_system.application.actor_action_step import (
    CompletedActorActionStep,
    _require_compatible_packages,
    execute_actor_action_step_in_unit,
)
from llm_system.application.npc_decision import (
    NpcDecisionContext,
    decide_greybridge_caretaker,
    decide_injured_courier,
)
from llm_system.application.npc_turn_coordinator import _require_caretaker
from llm_system.courier_decision import CourierPolicyResult
from llm_system.functional_generation import FunctionalModelGateway
from llm_system.game_packages.entities import NpcCharacterDefinition
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence.errors import MissingWorldError
from llm_system.persistence.sqlite import SQLiteStore
from llm_system.simulation._types import _StrictContract
from llm_system.simulation.actions import (
    ActorActionProposal,
    ActorActionSubmission,
    NpcPolicyActionSource,
)
from llm_system.simulation.perception_engine import project_current_perception
from llm_system.simulation.scheduling import (
    NpcScheduledActivity,
    ScheduledActivity,
    ScheduledActivityQueue,
    select_eligible_activities,
)
from llm_system.simulation.traces import (
    CourierScheduledActivityExecutionTrace,
    ScheduledActivityExecutionTrace,
)
from llm_system.simulation.validation import validate_world_state


_CARETAKER_POLICY_ID = "caretaker-rule-policy"
_COURIER_ID = "injured-courier"
_COURIER_POLICY_ID = "courier-llm-policy"


class UnsupportedScheduledActivityError(ValueError):
    pass


class NoDueScheduledActivityResult(_StrictContract):
    result_type: Literal["no_activity"]


class CompletedScheduledActivityResult(_StrictContract):
    result_type: Literal["completed"]
    completed_action: CompletedActorActionStep


class StaleScheduledActivityResult(_StrictContract):
    result_type: Literal["stale"]


class OperationalScheduledActivityResult(_StrictContract):
    result_type: Literal["operational_failure"]


ScheduledActivityExecutionResult: TypeAlias = (
    NoDueScheduledActivityResult
    | CompletedScheduledActivityResult
    | StaleScheduledActivityResult
    | OperationalScheduledActivityResult
)


def coordinate_due_npc_activity(
    store: SQLiteStore,
    packages: ValidatedGamePackages,
    gateway: FunctionalModelGateway,
    *,
    identity_factory: Callable[[], UUID],
) -> ScheduledActivityExecutionResult:
    """Prepare one due NPC policy decision, then consume it if still current."""
    with store.unit_of_work() as unit:
        stored = unit.worlds.get()
        if stored is None:
            raise MissingWorldError("the singleton world does not exist")
        _require_compatible_packages(stored, packages)
        world = validate_world_state(packages, stored.state)
        selection = select_eligible_activities(world, stored.scheduled_queue)
        if not selection.eligible_activities:
            return NoDueScheduledActivityResult(result_type="no_activity")
        activity = selection.eligible_activities[0]
        if not isinstance(activity, NpcScheduledActivity):
            raise UnsupportedScheduledActivityError(
                "only due caretaker NPC activity is supported"
            )
        npc = _require_supported_npc(packages, activity)
        context = NpcDecisionContext(
            decision_context_id=identity_factory(),
            npc_id=npc.id,
            identity_summary=npc.identity_summary,
            goals=npc.goals,
            current_plan=npc.initial_plan,
            perception=project_current_perception(world, npc.id),
        )
        observed_world_id = stored.world_id
        observed_revision = stored.revision
        selected_at_seconds = selection.selected_at_seconds

    try:
        courier_result: CourierPolicyResult | None = None
        proposal: ActorActionProposal
        if npc.id == _COURIER_ID:
            courier_result = decide_injured_courier(context, gateway)
            proposal = courier_result.proposal
        else:
            proposal = decide_greybridge_caretaker(context)

        with store.unit_of_work() as unit:
            current = unit.worlds.get()
            if (
                current is None
                or current.world_id != observed_world_id
                or current.revision != observed_revision
            ):
                return StaleScheduledActivityResult(result_type="stale")
            current_world = validate_world_state(packages, current.state)
            current_selection = select_eligible_activities(
                current_world, current.scheduled_queue
            )
            if (
                not current_selection.eligible_activities
                or current_selection.eligible_activities[0] != activity
            ):
                return StaleScheduledActivityResult(result_type="stale")

            submission = ActorActionSubmission(
                proposal_id=identity_factory(),
                simulation_step_id=identity_factory(),
                decision_context_id=context.decision_context_id,
                source=NpcPolicyActionSource(
                    source_type="npc_policy",
                    npc_id=npc.id,
                    policy_id=npc.decision_policy.policy_id,
                ),
                actor_id=npc.id,
                proposal=proposal,
            )
            completed = execute_actor_action_step_in_unit(
                unit,
                packages,
                submission,
                outcome_id=identity_factory(),
                event_id=identity_factory(),
                scheduled_queue=_queue_without(current.scheduled_queue, activity),
            )
            trace = (
                CourierScheduledActivityExecutionTrace(
                    trace_schema_version=2,
                    activity=activity,
                    selected_at_seconds=selected_at_seconds,
                    decision_context_id=context.decision_context_id,
                    simulation_step_id=submission.simulation_step_id,
                    result=courier_result,
                )
                if courier_result is not None
                else ScheduledActivityExecutionTrace(
                    trace_schema_version=1,
                    activity=activity,
                    selected_at_seconds=selected_at_seconds,
                    simulation_step_id=submission.simulation_step_id,
                )
            )
            unit.scheduled_activity_traces.append(
                world_id=completed.world_id,
                resulting_world_revision=completed.resulting_world_revision,
                trace=trace,
            )
            unit.commit()
            return CompletedScheduledActivityResult(
                result_type="completed", completed_action=completed
            )
    except Exception:
        return OperationalScheduledActivityResult(result_type="operational_failure")


def _require_supported_npc(
    packages: ValidatedGamePackages, activity: NpcScheduledActivity
) -> NpcCharacterDefinition:
    if activity.npc_id == "bridge-caretaker":
        return _require_caretaker(packages, activity.npc_id, _CARETAKER_POLICY_ID)
    if activity.npc_id != _COURIER_ID:
        raise UnsupportedScheduledActivityError(
            "only authored caretaker or courier activity is supported"
        )
    for entity in packages.scenario_package.definition.entity_collection.entities:
        if (
            entity.id == _COURIER_ID
            and isinstance(entity, NpcCharacterDefinition)
            and entity.decision_policy.policy_id == _COURIER_POLICY_ID
            and entity.decision_policy.policy_type == "llm"
        ):
            return entity
    raise UnsupportedScheduledActivityError(
        "requested courier does not match authored policy"
    )


def _queue_without(
    queue: ScheduledActivityQueue, selected: ScheduledActivity
) -> ScheduledActivityQueue:
    return ScheduledActivityQueue(
        activities=tuple(
            activity
            for activity in queue.activities
            if activity.activity_id != selected.activity_id
        )
    )
