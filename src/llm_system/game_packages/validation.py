from collections import defaultdict, deque
from collections.abc import Mapping
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ConfigDict

from llm_system.game_packages._types import NonBlankText
from llm_system.game_packages.entities import (
    EntityDefinition,
    LocationPlacementDefinition,
    NpcCharacterDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
    PossessedPlacementDefinition,
)
from llm_system.game_packages.loaded import LoadedRulePackage, LoadedScenarioPackage
from llm_system.game_packages.rules import (
    CharacterArchetypeDefinition,
    DecisionPolicyDefinition,
    ObjectArchetypeDefinition,
    ObjectUseMechanicDefinition,
)
from llm_system.game_packages.scenarios import (
    BooleanWorldFactDefinition,
    ObjectUseBindingDefinition,
)
from llm_system.game_packages.spatial import LocationDefinition


class ValidationIssueCode(StrEnum):
    DUPLICATE_ID = "duplicate-id"
    DEPENDENCY_MISMATCH = "dependency-mismatch"
    UNKNOWN_REFERENCE = "unknown-reference"
    POLICY_TYPE_MISMATCH = "policy-type-mismatch"
    INVALID_SELF_LOOP = "invalid-self-loop"
    UNREACHABLE_LOCATION = "unreachable-location"
    INVALID_PLAYER_COUNT = "invalid-player-count"
    INVALID_POSSESSION_TARGET = "invalid-possession-target"
    OBJECT_ARCHETYPE_MISMATCH = "object-archetype-mismatch"
    AMBIGUOUS_USE_BINDING = "ambiguous-use-binding"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: ValidationIssueCode
    path: NonBlankText
    message: NonBlankText


class GamePackageValidationError(Exception):
    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        if type(issues) is not tuple or not all(
            isinstance(issue, ValidationIssue) for issue in issues
        ):
            raise TypeError("validation issues must be a tuple of ValidationIssue")
        if not issues:
            raise ValueError("validation error requires at least one issue")
        super().__init__("game package validation failed")
        self.issues = issues


class ValidatedGamePackages(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    rule_package: LoadedRulePackage
    scenario_package: LoadedScenarioPackage


T = TypeVar("T")


def _index_records(
    records: tuple[T, ...], path: str, issues: list[ValidationIssue]
) -> dict[str, tuple[T, ...]]:
    index: dict[str, list[T]] = defaultdict(list)
    for position, record in enumerate(records):
        record_id = getattr(record, "id")
        if record_id in index:
            issues.append(
                _issue(ValidationIssueCode.DUPLICATE_ID, f"{path}[{position}].id")
            )
        index[record_id].append(record)
    return {record_id: tuple(values) for record_id, values in index.items()}


def _issue(code: ValidationIssueCode, path: str) -> ValidationIssue:
    messages = {
        ValidationIssueCode.DUPLICATE_ID: "identifier is duplicated in this namespace",
        ValidationIssueCode.DEPENDENCY_MISMATCH: "required rule package does not match",
        ValidationIssueCode.UNKNOWN_REFERENCE: "reference does not resolve in its namespace",
        ValidationIssueCode.POLICY_TYPE_MISMATCH: "policy type does not match definition",
        ValidationIssueCode.INVALID_SELF_LOOP: "connection must not be a self-loop",
        ValidationIssueCode.UNREACHABLE_LOCATION: "location is not reachable from the player",
        ValidationIssueCode.INVALID_PLAYER_COUNT: "scenario must define exactly one player",
        ValidationIssueCode.INVALID_POSSESSION_TARGET: "possession target must be a character",
        ValidationIssueCode.OBJECT_ARCHETYPE_MISMATCH: (
            "object archetype does not match the mechanic requirement"
        ),
        ValidationIssueCode.AMBIGUOUS_USE_BINDING: (
            "object and target location select more than one use binding"
        ),
    }
    return ValidationIssue(code=code, path=path, message=messages[code])


def _has_unique(index: Mapping[str, tuple[T, ...]], record_id: str) -> bool:
    return len(index.get(record_id, ())) == 1


def _is_missing(index: Mapping[str, tuple[T, ...]], record_id: str) -> bool:
    return record_id not in index


def _dependency_matches(
    rule_package: LoadedRulePackage, scenario_package: LoadedScenarioPackage
) -> bool:
    required = scenario_package.manifest.required_rule_pack
    return (
        required.package_id == rule_package.manifest.package_id
        and required.package_version == rule_package.manifest.package_version
    )


def _validate_connections(
    scenario_package: LoadedScenarioPackage,
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    issues: list[ValidationIssue],
) -> bool:
    connections = scenario_package.definition.spatial_graph.connections
    all_endpoints_resolve = True
    for position, connection in enumerate(connections):
        path = f"scenario.definition.spatial_graph.connections[{position}]"
        if connection.source_location_id == connection.destination_location_id:
            issues.append(
                _issue(
                    ValidationIssueCode.INVALID_SELF_LOOP, f"{path}.source_location_id"
                )
            )
        for field, location_id in (
            ("source_location_id", connection.source_location_id),
            ("destination_location_id", connection.destination_location_id),
        ):
            if _is_missing(locations, location_id):
                all_endpoints_resolve = False
                issues.append(
                    _issue(ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.{field}")
                )
    return all_endpoints_resolve


def _validate_entity_references(
    rule_package: LoadedRulePackage,
    scenario_package: LoadedScenarioPackage,
    dependency_matches: bool,
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    entities: Mapping[str, tuple[EntityDefinition, ...]],
    object_archetypes: Mapping[str, tuple[ObjectArchetypeDefinition, ...]],
    character_archetypes: Mapping[str, tuple[CharacterArchetypeDefinition, ...]],
    policies: Mapping[str, tuple[DecisionPolicyDefinition, ...]],
    issues: list[ValidationIssue],
) -> None:
    for position, entity in enumerate(
        scenario_package.definition.entity_collection.entities
    ):
        path = f"scenario.definition.entity_collection.entities[{position}]"
        if isinstance(entity, ObjectDefinition):
            _validate_object(
                entity,
                path,
                dependency_matches,
                object_archetypes,
                locations,
                entities,
                issues,
            )
        else:
            _validate_character(
                entity,
                path,
                dependency_matches,
                character_archetypes,
                locations,
                policies,
                issues,
            )


def _validate_object(
    entity: ObjectDefinition,
    path: str,
    dependency_matches: bool,
    object_archetypes: Mapping[str, tuple[ObjectArchetypeDefinition, ...]],
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    entities: Mapping[str, tuple[EntityDefinition, ...]],
    issues: list[ValidationIssue],
) -> None:
    if dependency_matches and _is_missing(
        object_archetypes, entity.object_archetype_id
    ):
        issues.append(
            _issue(ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.object_archetype_id")
        )
    placement = entity.initial_placement
    if isinstance(placement, LocationPlacementDefinition) and _is_missing(
        locations, placement.location_id
    ):
        issues.append(
            _issue(
                ValidationIssueCode.UNKNOWN_REFERENCE,
                f"{path}.initial_placement.location_id",
            )
        )
    if isinstance(placement, PossessedPlacementDefinition):
        targets = entities.get(placement.character_id, ())
        if len(targets) == 0:
            issues.append(
                _issue(
                    ValidationIssueCode.UNKNOWN_REFERENCE,
                    f"{path}.initial_placement.character_id",
                )
            )
        elif len(targets) == 1 and not isinstance(
            targets[0], (PlayerCharacterDefinition, NpcCharacterDefinition)
        ):
            issues.append(
                _issue(
                    ValidationIssueCode.INVALID_POSSESSION_TARGET,
                    f"{path}.initial_placement.character_id",
                )
            )


def _validate_character(
    entity: PlayerCharacterDefinition | NpcCharacterDefinition,
    path: str,
    dependency_matches: bool,
    character_archetypes: Mapping[str, tuple[CharacterArchetypeDefinition, ...]],
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    policies: Mapping[str, tuple[DecisionPolicyDefinition, ...]],
    issues: list[ValidationIssue],
) -> None:
    if dependency_matches and _is_missing(
        character_archetypes, entity.character_archetype_id
    ):
        issues.append(
            _issue(
                ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.character_archetype_id"
            )
        )
    if _is_missing(locations, entity.initial_location_id):
        issues.append(
            _issue(ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.initial_location_id")
        )
    if isinstance(entity, NpcCharacterDefinition) and dependency_matches:
        definitions = policies.get(entity.decision_policy.policy_id, ())
        if len(definitions) == 0:
            issues.append(
                _issue(
                    ValidationIssueCode.UNKNOWN_REFERENCE,
                    f"{path}.decision_policy.policy_id",
                )
            )
        elif (
            len(definitions) == 1
            and definitions[0].policy_type != entity.decision_policy.policy_type
        ):
            issues.append(
                _issue(
                    ValidationIssueCode.POLICY_TYPE_MISMATCH,
                    f"{path}.decision_policy.policy_type",
                )
            )


def _validate_reachability(
    scenario_package: LoadedScenarioPackage,
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    connections_unique: bool,
    all_connection_endpoints_resolve: bool,
    players: list[PlayerCharacterDefinition],
    issues: list[ValidationIssue],
) -> None:
    location_records = scenario_package.definition.spatial_graph.locations
    if not (
        len(locations) == len(location_records)
        and connections_unique
        and all_connection_endpoints_resolve
        and len(players) == 1
    ):
        return
    start = players[0].initial_location_id
    if not _has_unique(locations, start):
        return
    edges: dict[str, list[str]] = defaultdict(list)
    for connection in scenario_package.definition.spatial_graph.connections:
        if _has_unique(locations, connection.source_location_id) and _has_unique(
            locations, connection.destination_location_id
        ):
            edges[connection.source_location_id].append(
                connection.destination_location_id
            )
    reachable = {start}
    pending = deque([start])
    while pending:
        for destination in edges[pending.popleft()]:
            if destination not in reachable:
                reachable.add(destination)
                pending.append(destination)
    for position, location in enumerate(location_records):
        if location.id not in reachable:
            issues.append(
                _issue(
                    ValidationIssueCode.UNREACHABLE_LOCATION,
                    f"scenario.definition.spatial_graph.locations[{position}].id",
                )
            )


def _validate_mechanic_references(
    rule_package: LoadedRulePackage,
    object_archetypes: Mapping[str, tuple[ObjectArchetypeDefinition, ...]],
    issues: list[ValidationIssue],
) -> None:
    for position, mechanic in enumerate(rule_package.definition.object_use_mechanics):
        if _is_missing(object_archetypes, mechanic.object_archetype_id):
            issues.append(
                _issue(
                    ValidationIssueCode.UNKNOWN_REFERENCE,
                    f"rule.definition.object_use_mechanics[{position}].object_archetype_id",
                )
            )


def _validate_binding_references(
    binding: ObjectUseBindingDefinition,
    path: str,
    dependency_matches: bool,
    mechanics: Mapping[str, tuple[ObjectUseMechanicDefinition, ...]],
    entities: Mapping[str, tuple[EntityDefinition, ...]],
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    facts: Mapping[str, tuple[BooleanWorldFactDefinition, ...]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if dependency_matches and _is_missing(mechanics, binding.mechanic_id):
        issues.append(
            _issue(ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.mechanic_id")
        )
    object_records = entities.get(binding.object_id, ())
    if not object_records or (
        len(object_records) == 1 and not isinstance(object_records[0], ObjectDefinition)
    ):
        issues.append(
            _issue(ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.object_id")
        )
    checks = (
        ("target_location_id", binding.target_location_id, locations),
        ("fact_id", binding.fact_id, facts),
    )
    for field, identifier, index in checks:
        if _is_missing(index, identifier):
            issues.append(
                _issue(ValidationIssueCode.UNKNOWN_REFERENCE, f"{path}.{field}")
            )
    return issues


def _binding_archetype_issue(
    binding: ObjectUseBindingDefinition,
    path: str,
    mechanics: Mapping[str, tuple[ObjectUseMechanicDefinition, ...]],
    entities: Mapping[str, tuple[EntityDefinition, ...]],
) -> ValidationIssue | None:
    mechanic_records = mechanics.get(binding.mechanic_id, ())
    object_records = entities.get(binding.object_id, ())
    if len(mechanic_records) != 1 or len(object_records) != 1:
        return None
    obj = object_records[0]
    if not isinstance(obj, ObjectDefinition):
        return None
    if obj.object_archetype_id != mechanic_records[0].object_archetype_id:
        return _issue(
            ValidationIssueCode.OBJECT_ARCHETYPE_MISMATCH, f"{path}.object_id"
        )
    return None


def _validate_bindings(
    scenario_package: LoadedScenarioPackage,
    dependency_matches: bool,
    mechanics: Mapping[str, tuple[ObjectUseMechanicDefinition, ...]],
    entities: Mapping[str, tuple[EntityDefinition, ...]],
    locations: Mapping[str, tuple[LocationDefinition, ...]],
    facts: Mapping[str, tuple[BooleanWorldFactDefinition, ...]],
    issues: list[ValidationIssue],
) -> None:
    seen_pairs: set[tuple[str, str]] = set()
    for position, binding in enumerate(scenario_package.definition.object_use_bindings):
        path = f"scenario.definition.object_use_bindings[{position}]"
        issues.extend(
            _validate_binding_references(
                binding, path, dependency_matches, mechanics, entities, locations, facts
            )
        )
        if dependency_matches:
            mismatch = _binding_archetype_issue(binding, path, mechanics, entities)
            if mismatch is not None:
                issues.append(mismatch)
        object_records = entities.get(binding.object_id, ())
        object_resolves = len(object_records) == 1 and isinstance(
            object_records[0], ObjectDefinition
        )
        if not object_resolves or not _has_unique(
            locations, binding.target_location_id
        ):
            continue
        pair = (binding.object_id, binding.target_location_id)
        if pair in seen_pairs:
            issues.append(
                _issue(
                    ValidationIssueCode.AMBIGUOUS_USE_BINDING,
                    f"{path}.target_location_id",
                )
            )
        seen_pairs.add(pair)


def _validate_initial_npc_activities(
    scenario_package: LoadedScenarioPackage,
    entities: Mapping[str, tuple[EntityDefinition, ...]],
    issues: list[ValidationIssue],
) -> None:
    for position, activity in enumerate(
        scenario_package.definition.initial_npc_activities
    ):
        records = entities.get(activity.npc_id, ())
        if len(records) != 1 or not isinstance(records[0], NpcCharacterDefinition):
            issues.append(
                _issue(
                    ValidationIssueCode.UNKNOWN_REFERENCE,
                    f"scenario.definition.initial_npc_activities[{position}].npc_id",
                )
            )


def validate_game_packages(
    rule_package: LoadedRulePackage, scenario_package: LoadedScenarioPackage
) -> ValidatedGamePackages:
    issues: list[ValidationIssue] = []
    dependency_matches = _dependency_matches(rule_package, scenario_package)
    if not dependency_matches:
        issues.append(
            _issue(
                ValidationIssueCode.DEPENDENCY_MISMATCH,
                "scenario.manifest.required_rule_pack",
            )
        )
    definition = rule_package.definition
    object_archetypes = _index_records(
        definition.object_archetypes, "rule.definition.object_archetypes", issues
    )
    character_archetypes = _index_records(
        definition.character_archetypes, "rule.definition.character_archetypes", issues
    )
    policies = _index_records(
        definition.decision_policies, "rule.definition.decision_policies", issues
    )
    mechanics = _index_records(
        definition.object_use_mechanics,
        "rule.definition.object_use_mechanics",
        issues,
    )
    graph = scenario_package.definition.spatial_graph
    locations = _index_records(
        graph.locations, "scenario.definition.spatial_graph.locations", issues
    )
    connections = _index_records(
        graph.connections, "scenario.definition.spatial_graph.connections", issues
    )
    facts = _index_records(
        scenario_package.definition.boolean_world_facts,
        "scenario.definition.boolean_world_facts",
        issues,
    )
    entities = _index_records(
        scenario_package.definition.entity_collection.entities,
        "scenario.definition.entity_collection.entities",
        issues,
    )
    for position, entity in enumerate(
        scenario_package.definition.entity_collection.entities
    ):
        if isinstance(entity, NpcCharacterDefinition):
            _index_records(
                entity.goals,
                f"scenario.definition.entity_collection.entities[{position}].goals",
                issues,
            )
    _index_records(
        scenario_package.definition.object_use_bindings,
        "scenario.definition.object_use_bindings",
        issues,
    )
    players = [
        entity
        for entity in scenario_package.definition.entity_collection.entities
        if isinstance(entity, PlayerCharacterDefinition)
    ]
    if len(players) != 1:
        issues.append(
            _issue(
                ValidationIssueCode.INVALID_PLAYER_COUNT,
                "scenario.definition.entity_collection.entities",
            )
        )
    all_connection_endpoints_resolve = _validate_connections(
        scenario_package, locations, issues
    )
    _validate_entity_references(
        rule_package,
        scenario_package,
        dependency_matches,
        locations,
        entities,
        object_archetypes,
        character_archetypes,
        policies,
        issues,
    )
    _validate_mechanic_references(rule_package, object_archetypes, issues)
    _validate_bindings(
        scenario_package,
        dependency_matches,
        mechanics,
        entities,
        locations,
        facts,
        issues,
    )
    _validate_initial_npc_activities(scenario_package, entities, issues)
    _validate_reachability(
        scenario_package,
        locations,
        len(connections) == len(graph.connections),
        all_connection_endpoints_resolve,
        players,
        issues,
    )
    if issues:
        raise GamePackageValidationError(tuple(issues))
    return ValidatedGamePackages(
        rule_package=rule_package, scenario_package=scenario_package
    )
