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
)
from llm_system.game_packages.entities import NpcCharacterDefinition
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence.errors import MissingWorldError
from llm_system.persistence.sqlite import SQLiteStore
from llm_system.simulation._types import _StrictContract
from llm_system.simulation.actions import ActorActionSubmission, NpcPolicyActionSource
from llm_system.simulation.perception_engine import project_current_perception
from llm_system.simulation.validation import validate_world_state


_CARETAKER_ID = "bridge-caretaker"
_CARETAKER_POLICY_ID = "caretaker-rule-policy"


class UnsupportedNpcTurnError(ValueError):
    pass


class CompletedNpcTurnResult(_StrictContract):
    result_type: Literal["completed"]
    completed_action: CompletedActorActionStep


class StaleNpcTurnResult(_StrictContract):
    result_type: Literal["stale"]


NpcTurnResult: TypeAlias = CompletedNpcTurnResult | StaleNpcTurnResult


def coordinate_caretaker_turn(
    store: SQLiteStore,
    packages: ValidatedGamePackages,
    *,
    npc_id: str,
    policy_id: str,
    identity_factory: Callable[[], UUID],
) -> NpcTurnResult:
    """Run one pure caretaker decision, then durably resolve it if still current."""
    with store.unit_of_work() as unit:
        stored = unit.worlds.get()
        if stored is None:
            raise MissingWorldError("the singleton world does not exist")
        _require_compatible_packages(stored, packages)
        world = validate_world_state(packages, stored.state)
        npc = _require_caretaker(packages, npc_id, policy_id)
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

    proposal = decide_greybridge_caretaker(context)

    with store.unit_of_work() as unit:
        current = unit.worlds.get()
        if (
            current is None
            or current.world_id != observed_world_id
            or current.revision != observed_revision
        ):
            return StaleNpcTurnResult(result_type="stale")

        submission = ActorActionSubmission(
            proposal_id=identity_factory(),
            simulation_step_id=identity_factory(),
            decision_context_id=context.decision_context_id,
            source=NpcPolicyActionSource(
                source_type="npc_policy", npc_id=npc.id, policy_id=policy_id
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
        )
        unit.commit()
        return CompletedNpcTurnResult(
            result_type="completed", completed_action=completed
        )


def _require_caretaker(
    packages: ValidatedGamePackages, npc_id: str, policy_id: str
) -> NpcCharacterDefinition:
    if npc_id != _CARETAKER_ID or policy_id != _CARETAKER_POLICY_ID:
        raise UnsupportedNpcTurnError("only the caretaker rule policy is supported")
    for entity in packages.scenario_package.definition.entity_collection.entities:
        if entity.id == npc_id:
            if (
                isinstance(entity, NpcCharacterDefinition)
                and entity.decision_policy.policy_id == policy_id
                and entity.decision_policy.policy_type == "rule"
            ):
                return entity
            break
    raise UnsupportedNpcTurnError("requested caretaker does not match authored policy")
