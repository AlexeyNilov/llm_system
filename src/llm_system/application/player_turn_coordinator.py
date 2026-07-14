from collections.abc import Callable
from typing import Literal, TypeAlias
from uuid import UUID

from llm_system.application.actor_action_step import (
    CompletedActorActionStep,
    _require_compatible_packages,
    execute_actor_action_step_in_unit,
)
from llm_system.application.player_interpreter import interpret_player_input
from llm_system.functional_generation import FunctionalModelGateway
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence.errors import MissingWorldError
from llm_system.persistence.sqlite import SQLiteStore, SQLiteUnitOfWork
from llm_system.player_interpretation import PlayerInterpretationResult
from llm_system.player_input_traces import (
    ActionLinkedCompletion,
    ClarificationCompletion,
    PlayerInputStepTrace,
    ThoughtOnlyCompletion,
)
from llm_system.simulation._types import _StrictContract
from llm_system.simulation.actions import (
    ActorActionSubmission,
    PlayerInterpreterActionSource,
)
from llm_system.simulation.perception_engine import project_current_perception
from llm_system.simulation.validation import validate_world_state


class ThoughtOnlyPlayerTurnResult(_StrictContract):
    result_type: Literal["thought_only"]
    private_thought: str


class ClarificationPlayerTurnResult(_StrictContract):
    result_type: Literal["clarification"]
    clarification: str


class ActionCompletedPlayerTurnResult(_StrictContract):
    result_type: Literal["action_completed"]
    completed_action: CompletedActorActionStep
    private_thought: str | None


class StalePlayerTurnResult(_StrictContract):
    result_type: Literal["stale"]


PlayerTurnResult: TypeAlias = (
    ThoughtOnlyPlayerTurnResult
    | ClarificationPlayerTurnResult
    | ActionCompletedPlayerTurnResult
    | StalePlayerTurnResult
)


def coordinate_player_turn(
    store: SQLiteStore,
    packages: ValidatedGamePackages,
    gateway: FunctionalModelGateway,
    *,
    player_text: str,
    player_id: str,
    identity_factory: Callable[[], UUID],
) -> PlayerTurnResult:
    with store.unit_of_work() as unit:
        stored = unit.worlds.get()
        if stored is None:
            raise MissingWorldError("the singleton world does not exist")
        _require_compatible_packages(stored, packages)
        world = validate_world_state(packages, stored.state)
        perception = project_current_perception(world, player_id)
        observed_world_id = stored.world_id
        observed_revision = stored.revision

    interpretation = interpret_player_input(
        gateway, player_text=player_text, perception=perception
    )

    with store.unit_of_work() as unit:
        current = unit.worlds.get()
        if (
            current is None
            or current.world_id != observed_world_id
            or current.revision != observed_revision
        ):
            return StalePlayerTurnResult(result_type="stale")

        output = interpretation.output
        player_input_id = identity_factory()
        if output.result_type == "clarification":
            assert output.clarification is not None
            _append_no_action_trace(
                unit,
                world_id=observed_world_id,
                revision=observed_revision,
                player_input_id=player_input_id,
                interpretation=interpretation,
                completion=ClarificationCompletion(completion_type="clarification"),
            )
            unit.commit()
            return ClarificationPlayerTurnResult(
                result_type="clarification", clarification=output.clarification
            )

        if output.proposal is None:
            assert output.private_thought is not None
            _append_no_action_trace(
                unit,
                world_id=observed_world_id,
                revision=observed_revision,
                player_input_id=player_input_id,
                interpretation=interpretation,
                completion=ThoughtOnlyCompletion(completion_type="thought_only"),
            )
            unit.commit()
            return ThoughtOnlyPlayerTurnResult(
                result_type="thought_only", private_thought=output.private_thought
            )

        proposal_id = identity_factory()
        simulation_step_id = identity_factory()
        decision_context_id = identity_factory()
        outcome_id = identity_factory()
        event_id = identity_factory()
        submission = ActorActionSubmission(
            proposal_id=proposal_id,
            simulation_step_id=simulation_step_id,
            decision_context_id=decision_context_id,
            source=PlayerInterpreterActionSource(
                source_type="player_interpreter", interpreter_id="freeform-player-turn"
            ),
            actor_id=player_id,
            proposal=output.proposal,
        )
        completed = execute_actor_action_step_in_unit(
            unit, packages, submission, outcome_id=outcome_id, event_id=event_id
        )
        unit.player_input_traces.append(
            world_id=observed_world_id,
            observed_world_revision=observed_revision,
            resulting_world_revision=completed.resulting_world_revision,
            trace=PlayerInputStepTrace(
                trace_schema_version=1,
                player_input_id=player_input_id,
                interpretation=interpretation,
                completion=ActionLinkedCompletion(
                    completion_type="action_linked",
                    simulation_step_id=simulation_step_id,
                ),
            ),
        )
        unit.commit()
        return ActionCompletedPlayerTurnResult(
            result_type="action_completed",
            completed_action=completed,
            private_thought=output.private_thought,
        )


def _append_no_action_trace(
    unit: SQLiteUnitOfWork,
    *,
    world_id: UUID,
    revision: int,
    player_input_id: UUID,
    interpretation: PlayerInterpretationResult,
    completion: ThoughtOnlyCompletion | ClarificationCompletion,
) -> None:
    unit.player_input_traces.append(
        world_id=world_id,
        observed_world_revision=revision,
        resulting_world_revision=revision,
        trace=PlayerInputStepTrace(
            trace_schema_version=1,
            player_input_id=player_input_id,
            interpretation=interpretation,
            completion=completion,
        ),
    )
