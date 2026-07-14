from uuid import UUID

from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence.errors import MissingWorldError
from llm_system.persistence.records import (
    NonNegativeRevision,
    PackageReference,
    StoredWorld,
)
from llm_system.persistence.sqlite import SQLiteStore, SQLiteUnitOfWork
from llm_system.simulation._types import _StrictContract
from llm_system.simulation.actions import ActorActionSubmission
from llm_system.simulation.authorization import authorize_actor_action
from llm_system.simulation.commitment import commit_outcome
from llm_system.simulation.dispatch import dispatch_actor_action
from llm_system.simulation.outcomes import RejectedOutcome
from llm_system.simulation.perception_engine import (
    project_current_perception,
    project_self_event_feedback,
)
from llm_system.simulation.traces import CompletedActorActionStepTrace
from llm_system.simulation.validation import validate_world_state


class WorldPackageMismatchError(ValueError):
    pass


class CompletedActorActionStep(_StrictContract):
    world_id: UUID
    resulting_world_revision: NonNegativeRevision
    trace: CompletedActorActionStepTrace


def _require_compatible_packages(
    stored: StoredWorld, packages: ValidatedGamePackages
) -> None:
    expected_rule = PackageReference(
        package_id=packages.rule_package.manifest.package_id,
        package_version=packages.rule_package.manifest.package_version,
    )
    expected_scenario = PackageReference(
        package_id=packages.scenario_package.manifest.package_id,
        package_version=packages.scenario_package.manifest.package_version,
    )
    if (
        stored.rule_package != expected_rule
        or stored.scenario_package != expected_scenario
    ):
        raise WorldPackageMismatchError(
            "supplied packages do not match the stored world's package ownership"
        )


def execute_actor_action_step(
    store: SQLiteStore,
    packages: ValidatedGamePackages,
    submission: ActorActionSubmission,
    *,
    outcome_id: UUID,
    event_id: UUID,
) -> CompletedActorActionStep:
    with store.unit_of_work() as unit:
        completed = execute_actor_action_step_in_unit(
            unit,
            packages,
            submission,
            outcome_id=outcome_id,
            event_id=event_id,
        )
        unit.commit()
        return completed


def execute_actor_action_step_in_unit(
    unit: SQLiteUnitOfWork,
    packages: ValidatedGamePackages,
    submission: ActorActionSubmission,
    *,
    outcome_id: UUID,
    event_id: UUID,
) -> CompletedActorActionStep:
    stored = unit.worlds.get()
    if stored is None:
        raise MissingWorldError("the singleton world does not exist")
    _require_compatible_packages(stored, packages)
    world = validate_world_state(packages, stored.state)
    authorized = authorize_actor_action(world, submission)
    outcome = dispatch_actor_action(
        authorized, outcome_id=outcome_id, event_id=event_id
    )
    committed = commit_outcome(world, outcome)
    current_perception = project_current_perception(
        committed.world, submission.actor_id
    )
    events = () if isinstance(outcome, RejectedOutcome) else outcome.events
    self_event_feedback = project_self_event_feedback(
        committed.world, submission.actor_id, events
    )
    trace = CompletedActorActionStepTrace(
        trace_schema_version=1,
        simulation_step_id=submission.simulation_step_id,
        decision_context_id=submission.decision_context_id,
        submission=submission,
        outcome=outcome,
        current_perception=current_perception,
        self_event_feedback=self_event_feedback,
    )
    replacement = unit.worlds.replace(
        world_id=stored.world_id,
        expected_revision=stored.revision,
        state=committed.world.state,
        scheduled_queue=stored.scheduled_queue,
    )
    unit.events.append(
        world_id=stored.world_id,
        resulting_world_revision=replacement.revision,
        events=events,
    )
    unit.traces.append(
        world_id=stored.world_id,
        resulting_world_revision=replacement.revision,
        trace=trace,
    )
    return CompletedActorActionStep(
        world_id=stored.world_id,
        resulting_world_revision=replacement.revision,
        trace=trace,
    )
