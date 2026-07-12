from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from llm_system.game_packages._types import NonBlankText
from llm_system.game_packages.entities import (
    NpcCharacterDefinition,
    PlayerCharacterDefinition,
)
from llm_system.simulation.changes import (
    CharacterLocationChanged,
    ConnectionAvailabilityChanged,
    ObjectPlacementChanged,
    SimulationTimeChanged,
    StateChange,
)
from llm_system.simulation.outcomes import Outcome, RejectedOutcome
from llm_system.simulation.state import (
    CharacterState,
    ConnectionState,
    ObjectAtLocation,
    ObjectState,
    WorldState,
)
from llm_system.simulation.validation import (
    ValidatedWorldState,
    WorldStateValidationError,
    validate_world_state,
)


class OutcomeCommitIssueCode(StrEnum):
    RESOLUTION_TIME_MISMATCH = "resolution-time-mismatch"
    UNKNOWN_CHANGE_TARGET = "unknown-change-target"
    BEFORE_VALUE_MISMATCH = "before-value-mismatch"
    UNKNOWN_AFTER_REFERENCE = "unknown-after-reference"


class OutcomeCommitIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: OutcomeCommitIssueCode
    path: NonBlankText
    message: NonBlankText


class OutcomeCommitError(Exception):
    def __init__(self, issues: tuple[OutcomeCommitIssue, ...]) -> None:
        if type(issues) is not tuple or not all(
            isinstance(issue, OutcomeCommitIssue) for issue in issues
        ):
            raise TypeError("commit issues must be a tuple of OutcomeCommitIssue")
        if not issues:
            raise ValueError("commit error requires at least one issue")
        super().__init__("outcome commitment failed")
        self.issues = issues


class OutcomeCommitResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    outcome: Outcome
    world: ValidatedWorldState


def _issue(code: OutcomeCommitIssueCode, path: str, message: str) -> OutcomeCommitIssue:
    return OutcomeCommitIssue(code=code, path=path, message=message)


def _authored_ids(world: ValidatedWorldState) -> tuple[set[str], set[str]]:
    scenario = world.packages.scenario_package.definition
    location_ids = {location.id for location in scenario.spatial_graph.locations}
    character_ids = {
        entity.id
        for entity in scenario.entity_collection.entities
        if isinstance(entity, (PlayerCharacterDefinition, NpcCharacterDefinition))
    }
    return location_ids, character_ids


def _find_character(
    world: ValidatedWorldState, identifier: str
) -> CharacterState | None:
    return next(
        (item for item in world.state.characters if item.character_id == identifier),
        None,
    )


def _find_object(world: ValidatedWorldState, identifier: str) -> ObjectState | None:
    return next(
        (item for item in world.state.objects if item.object_id == identifier), None
    )


def _find_connection(
    world: ValidatedWorldState, identifier: str
) -> ConnectionState | None:
    return next(
        (item for item in world.state.connections if item.connection_id == identifier),
        None,
    )


def _unknown_target(path: str) -> OutcomeCommitIssue:
    return _issue(
        OutcomeCommitIssueCode.UNKNOWN_CHANGE_TARGET,
        path,
        "state-change target does not exist in runtime state",
    )


def _before_mismatch(path: str) -> OutcomeCommitIssue:
    return _issue(
        OutcomeCommitIssueCode.BEFORE_VALUE_MISMATCH,
        path,
        "state-change before value does not match current world state",
    )


def _unknown_reference(path: str) -> OutcomeCommitIssue:
    return _issue(
        OutcomeCommitIssueCode.UNKNOWN_AFTER_REFERENCE,
        path,
        "state-change after reference does not exist in authored definitions",
    )


def _resolution_mismatch(path: str) -> OutcomeCommitIssue:
    return _issue(
        OutcomeCommitIssueCode.RESOLUTION_TIME_MISMATCH,
        path,
        "outcome completion time is inconsistent with world state change",
    )


def _character_issues(
    world: ValidatedWorldState,
    change: CharacterLocationChanged,
    path: str,
    location_ids: set[str],
) -> list[OutcomeCommitIssue]:
    target = _find_character(world, change.character_id)
    if target is None:
        return [_unknown_target(f"{path}.character_id")]
    issues = []
    if target.location_id != change.from_location_id:
        issues.append(_before_mismatch(f"{path}.from_location_id"))
    if change.to_location_id not in location_ids:
        issues.append(_unknown_reference(f"{path}.to_location_id"))
    return issues


def _object_after_path(change: ObjectPlacementChanged, path: str) -> str:
    if isinstance(change.to_placement, ObjectAtLocation):
        return f"{path}.to_placement.location_id"
    return f"{path}.to_placement.character_id"


def _object_after_exists(
    change: ObjectPlacementChanged,
    location_ids: set[str],
    character_ids: set[str],
) -> bool:
    placement = change.to_placement
    if isinstance(placement, ObjectAtLocation):
        return placement.location_id in location_ids
    return placement.character_id in character_ids


def _object_issues(
    world: ValidatedWorldState,
    change: ObjectPlacementChanged,
    path: str,
    location_ids: set[str],
    character_ids: set[str],
) -> list[OutcomeCommitIssue]:
    target = _find_object(world, change.object_id)
    if target is None:
        return [_unknown_target(f"{path}.object_id")]
    issues = []
    if target.placement != change.from_placement:
        issues.append(_before_mismatch(f"{path}.from_placement"))
    if not _object_after_exists(change, location_ids, character_ids):
        issues.append(_unknown_reference(_object_after_path(change, path)))
    return issues


def _connection_issues(
    world: ValidatedWorldState,
    change: ConnectionAvailabilityChanged,
    path: str,
) -> list[OutcomeCommitIssue]:
    target = _find_connection(world, change.connection_id)
    if target is None:
        return [_unknown_target(f"{path}.connection_id")]
    if target.is_available != change.from_available:
        return [_before_mismatch(f"{path}.from_available")]
    return []


def _time_issues(
    world: ValidatedWorldState,
    outcome: Outcome,
    change: SimulationTimeChanged,
    path: str,
) -> list[OutcomeCommitIssue]:
    issues = []
    if change.from_seconds != world.state.simulation_time_seconds:
        issues.append(_before_mismatch(f"{path}.from_seconds"))
    if change.to_seconds != outcome.resolved_at_seconds:
        issues.append(_resolution_mismatch(f"{path}.to_seconds"))
    return issues


def _change_issues(
    world: ValidatedWorldState,
    outcome: Outcome,
    change: StateChange,
    path: str,
    location_ids: set[str],
    character_ids: set[str],
) -> list[OutcomeCommitIssue]:
    if isinstance(change, CharacterLocationChanged):
        return _character_issues(world, change, path, location_ids)
    if isinstance(change, ObjectPlacementChanged):
        return _object_issues(world, change, path, location_ids, character_ids)
    if isinstance(change, ConnectionAvailabilityChanged):
        return _connection_issues(world, change, path)
    if isinstance(change, SimulationTimeChanged):
        return _time_issues(world, outcome, change, path)
    raise AssertionError("unreachable closed state-change variant")


def _validate_commitment(
    world: ValidatedWorldState, outcome: Outcome
) -> tuple[OutcomeCommitIssue, ...]:
    changes = () if isinstance(outcome, RejectedOutcome) else outcome.state_changes
    issues = []
    has_time_change = any(isinstance(item, SimulationTimeChanged) for item in changes)
    if (
        not has_time_change
        and outcome.resolved_at_seconds != world.state.simulation_time_seconds
    ):
        issues.append(_resolution_mismatch("outcome.resolved_at_seconds"))
    location_ids, character_ids = _authored_ids(world)
    for index, change in enumerate(changes):
        issues.extend(
            _change_issues(
                world,
                outcome,
                change,
                f"outcome.state_changes[{index}]",
                location_ids,
                character_ids,
            )
        )
    return tuple(issues)


def _replace_character(
    records: tuple[CharacterState, ...], change: CharacterLocationChanged
) -> tuple[CharacterState, ...]:
    return tuple(
        item.model_copy(update={"location_id": change.to_location_id})
        if item.character_id == change.character_id
        else item
        for item in records
    )


def _replace_object(
    records: tuple[ObjectState, ...], change: ObjectPlacementChanged
) -> tuple[ObjectState, ...]:
    return tuple(
        item.model_copy(update={"placement": change.to_placement})
        if item.object_id == change.object_id
        else item
        for item in records
    )


def _replace_connection(
    records: tuple[ConnectionState, ...], change: ConnectionAvailabilityChanged
) -> tuple[ConnectionState, ...]:
    return tuple(
        item.model_copy(update={"is_available": change.to_available})
        if item.connection_id == change.connection_id
        else item
        for item in records
    )


def _apply_changes(state: WorldState, changes: tuple[StateChange, ...]) -> WorldState:
    characters = state.characters
    objects = state.objects
    connections = state.connections
    time = state.simulation_time_seconds
    for change in changes:
        if isinstance(change, CharacterLocationChanged):
            characters = _replace_character(characters, change)
        elif isinstance(change, ObjectPlacementChanged):
            objects = _replace_object(objects, change)
        elif isinstance(change, ConnectionAvailabilityChanged):
            connections = _replace_connection(connections, change)
        elif isinstance(change, SimulationTimeChanged):
            time = change.to_seconds
        else:
            raise AssertionError("unreachable closed state-change variant")
    return WorldState(
        simulation_time_seconds=time,
        characters=characters,
        objects=objects,
        connections=connections,
    )


def commit_outcome(world: ValidatedWorldState, outcome: Outcome) -> OutcomeCommitResult:
    issues = _validate_commitment(world, outcome)
    if issues:
        raise OutcomeCommitError(issues)
    changes = () if isinstance(outcome, RejectedOutcome) else outcome.state_changes
    if not changes:
        return OutcomeCommitResult(outcome=outcome, world=world)
    state = _apply_changes(world.state, changes)
    try:
        replacement = validate_world_state(world.packages, state)
    except WorldStateValidationError as error:
        raise AssertionError(
            "kernel invariant defect: committed state failed world validation"
        ) from error
    return OutcomeCommitResult(outcome=outcome, world=replacement)
