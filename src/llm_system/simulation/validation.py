from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ConfigDict

from llm_system.game_packages._types import NonBlankText
from llm_system.game_packages.entities import (
    NpcCharacterDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.simulation.state import (
    CharacterState,
    ObjectAtLocation,
    ObjectPossessedByCharacter,
    ObjectState,
    WorldState,
)


class WorldStateValidationIssueCode(StrEnum):
    DUPLICATE_STATE_ID = "duplicate-state-id"
    MISSING_STATE = "missing-state"
    UNEXPECTED_STATE = "unexpected-state"
    UNKNOWN_RUNTIME_REFERENCE = "unknown-runtime-reference"


class WorldStateValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: WorldStateValidationIssueCode
    path: NonBlankText
    message: NonBlankText


class WorldStateValidationError(Exception):
    def __init__(self, issues: tuple[WorldStateValidationIssue, ...]) -> None:
        if type(issues) is not tuple or not all(
            isinstance(issue, WorldStateValidationIssue) for issue in issues
        ):
            raise TypeError(
                "validation issues must be a tuple of WorldStateValidationIssue"
            )
        if not issues:
            raise ValueError("validation error requires at least one issue")
        super().__init__("world state validation failed")
        self.issues = issues


class ValidatedWorldState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    packages: ValidatedGamePackages
    state: WorldState


T = TypeVar("T")


def _issue(
    code: WorldStateValidationIssueCode, path: str, message: str
) -> WorldStateValidationIssue:
    return WorldStateValidationIssue(code=code, path=path, message=message)


def _validate_overlay(
    records: tuple[T, ...],
    expected_ids: tuple[str, ...],
    collection: str,
    id_field: str,
    record_id: Callable[[T], str],
    issues: list[WorldStateValidationIssue],
) -> set[str]:
    positions: dict[str, list[int]] = {}
    for position, record in enumerate(records):
        identifier = record_id(record)
        if identifier in positions:
            issues.append(
                _issue(
                    WorldStateValidationIssueCode.DUPLICATE_STATE_ID,
                    f"{collection}[{position}].{id_field}",
                    "runtime state identifier is duplicated",
                )
            )
        positions.setdefault(identifier, []).append(position)
    for identifier in expected_ids:
        if identifier not in positions:
            issues.append(
                _issue(
                    WorldStateValidationIssueCode.MISSING_STATE,
                    collection,
                    f"missing runtime state for authored identifier '{identifier}'",
                )
            )
    expected = set(expected_ids)
    for position, record in enumerate(records):
        if record_id(record) not in expected:
            issues.append(
                _issue(
                    WorldStateValidationIssueCode.UNEXPECTED_STATE,
                    f"{collection}[{position}].{id_field}",
                    "runtime state identifier has no matching authored definition",
                )
            )
    return {
        identifier
        for identifier, record_positions in positions.items()
        if identifier in expected and len(record_positions) == 1
    }


def _validate_character_references(
    characters: tuple[CharacterState, ...],
    valid_character_ids: set[str],
    location_ids: set[str],
    issues: list[WorldStateValidationIssue],
) -> None:
    for position, character in enumerate(characters):
        if (
            character.character_id in valid_character_ids
            and character.location_id not in location_ids
        ):
            issues.append(
                _issue(
                    WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
                    f"characters[{position}].location_id",
                    "runtime reference does not resolve in authored definitions",
                )
            )


def _validate_object_references(
    objects: tuple[ObjectState, ...],
    valid_object_ids: set[str],
    location_ids: set[str],
    character_ids: set[str],
    issues: list[WorldStateValidationIssue],
) -> None:
    for position, obj in enumerate(objects):
        if obj.object_id not in valid_object_ids:
            continue
        placement = obj.placement
        if (
            isinstance(placement, ObjectAtLocation)
            and placement.location_id not in location_ids
        ):
            issues.append(
                _issue(
                    WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
                    f"objects[{position}].placement.location_id",
                    "runtime reference does not resolve in authored definitions",
                )
            )
        if (
            isinstance(placement, ObjectPossessedByCharacter)
            and placement.character_id not in character_ids
        ):
            issues.append(
                _issue(
                    WorldStateValidationIssueCode.UNKNOWN_RUNTIME_REFERENCE,
                    f"objects[{position}].placement.character_id",
                    "runtime reference does not resolve in authored definitions",
                )
            )


def validate_world_state(
    packages: ValidatedGamePackages, state: WorldState
) -> ValidatedWorldState:
    scenario = packages.scenario_package.definition
    entities = scenario.entity_collection.entities
    character_ids = tuple(
        entity.id
        for entity in entities
        if isinstance(entity, (PlayerCharacterDefinition, NpcCharacterDefinition))
    )
    object_ids = tuple(
        entity.id for entity in entities if isinstance(entity, ObjectDefinition)
    )
    connection_ids = tuple(
        connection.id for connection in scenario.spatial_graph.connections
    )
    location_ids = {location.id for location in scenario.spatial_graph.locations}
    issues: list[WorldStateValidationIssue] = []
    valid_character_ids = _validate_overlay(
        state.characters,
        character_ids,
        "characters",
        "character_id",
        lambda item: item.character_id,
        issues,
    )
    valid_object_ids = _validate_overlay(
        state.objects,
        object_ids,
        "objects",
        "object_id",
        lambda item: item.object_id,
        issues,
    )
    _validate_overlay(
        state.connections,
        connection_ids,
        "connections",
        "connection_id",
        lambda item: item.connection_id,
        issues,
    )
    _validate_character_references(
        state.characters, valid_character_ids, location_ids, issues
    )
    _validate_object_references(
        state.objects, valid_object_ids, location_ids, set(character_ids), issues
    )
    if issues:
        raise WorldStateValidationError(tuple(issues))
    return ValidatedWorldState(packages=packages, state=state)
