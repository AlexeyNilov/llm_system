from pathlib import Path
from typing import Self
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, model_validator

from llm_system.application.actor_action_step import WorldPackageMismatchError
from llm_system.game_packages.entities import (
    LocationPlacementDefinition,
    NpcCharacterDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
    PossessedPlacementDefinition,
)
from llm_system.game_packages.loaded import LoadedRulePackage, LoadedScenarioPackage
from llm_system.game_packages.loader import load_game_package
from llm_system.game_packages.validation import (
    ValidatedGamePackages,
    validate_game_packages,
)
from llm_system.persistence.errors import MissingWorldError
from llm_system.persistence.records import PackageReference, StoredWorld
from llm_system.persistence.sqlite import SQLiteStore
from llm_system.simulation.scheduling import (
    NpcScheduledActivity,
    ScheduledActivityQueue,
)
from llm_system.simulation.state import (
    BooleanWorldFactState,
    CharacterState,
    ConnectionState,
    ObjectAtLocation,
    ObjectPlacement,
    ObjectPossessedByCharacter,
    ObjectState,
    WorldState,
)
from llm_system.simulation.validation import (
    ValidatedWorldState,
    validate_world_state,
)


class WorldPackageKindError(ValueError):
    pass


class ActiveWorld(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    stored_world: StoredWorld
    validated_world: ValidatedWorldState

    @model_validator(mode="after")
    def require_coherent_world(self) -> Self:
        if self.stored_world.state != self.validated_world.state:
            raise ValueError("stored and validated world state must match")
        _require_compatible_packages(self.stored_world, self.validated_world.packages)
        return self


def build_initial_world(packages: ValidatedGamePackages) -> ValidatedWorldState:
    scenario = packages.scenario_package.definition
    characters: list[CharacterState] = []
    objects: list[ObjectState] = []
    for entity in scenario.entity_collection.entities:
        if isinstance(entity, (PlayerCharacterDefinition, NpcCharacterDefinition)):
            characters.append(
                CharacterState(
                    character_id=entity.id,
                    location_id=entity.initial_location_id,
                )
            )
        elif isinstance(entity, ObjectDefinition):
            placement = entity.initial_placement
            runtime_placement: ObjectPlacement
            if isinstance(placement, LocationPlacementDefinition):
                runtime_placement = ObjectAtLocation(
                    placement_type="location", location_id=placement.location_id
                )
            elif isinstance(placement, PossessedPlacementDefinition):
                runtime_placement = ObjectPossessedByCharacter(
                    placement_type="possessed_by_character",
                    character_id=placement.character_id,
                )
            objects.append(
                ObjectState(object_id=entity.id, placement=runtime_placement)
            )
    state = WorldState(
        simulation_time_seconds=0,
        characters=tuple(characters),
        objects=tuple(objects),
        connections=tuple(
            ConnectionState(connection_id=connection.id, is_available=True)
            for connection in scenario.spatial_graph.connections
        ),
        boolean_world_facts=tuple(
            BooleanWorldFactState(fact_id=fact.id, value=fact.initial_value)
            for fact in scenario.boolean_world_facts
        ),
    )
    return validate_world_state(packages, state)


def create_world(
    store: SQLiteStore,
    packages: ValidatedGamePackages,
    *,
    world_id: UUID,
) -> ActiveWorld:
    validated_world = build_initial_world(packages)
    with store.unit_of_work() as unit:
        stored_world = unit.worlds.create(
            world_id=world_id,
            rule_package=_rule_package_reference(packages),
            scenario_package=_scenario_package_reference(packages),
            state=validated_world.state,
            scheduled_queue=_initial_scheduled_queue(packages, world_id),
        )
        unit.commit()
    return ActiveWorld(
        stored_world=stored_world,
        validated_world=validated_world,
    )


def resume_world(store: SQLiteStore, package_root: Path) -> ActiveWorld:
    with store.unit_of_work() as unit:
        stored_world = unit.worlds.get()
        if stored_world is None:
            raise MissingWorldError("the singleton world does not exist")

    loaded_rule = load_game_package(
        package_root
        / "rules"
        / stored_world.rule_package.package_id
        / stored_world.rule_package.package_version
    )
    loaded_scenario = load_game_package(
        package_root
        / "scenarios"
        / stored_world.scenario_package.package_id
        / stored_world.scenario_package.package_version
    )
    if not isinstance(loaded_rule, LoadedRulePackage):
        raise WorldPackageKindError("recorded rule package is not a rule package")
    if not isinstance(loaded_scenario, LoadedScenarioPackage):
        raise WorldPackageKindError(
            "recorded scenario package is not a scenario package"
        )
    packages = validate_game_packages(loaded_rule, loaded_scenario)
    _require_compatible_packages(stored_world, packages)
    validated_world = validate_world_state(packages, stored_world.state)
    return ActiveWorld(
        stored_world=stored_world,
        validated_world=validated_world,
    )


def reset_world_for_development(
    store: SQLiteStore,
    packages: ValidatedGamePackages,
    *,
    world_id: UUID,
) -> ActiveWorld:
    validated_world = build_initial_world(packages)
    with store.unit_of_work() as unit:
        unit.clear_world_timeline_for_development()
        stored_world = unit.worlds.create(
            world_id=world_id,
            rule_package=_rule_package_reference(packages),
            scenario_package=_scenario_package_reference(packages),
            state=validated_world.state,
            scheduled_queue=_initial_scheduled_queue(packages, world_id),
        )
        unit.commit()
    return ActiveWorld(
        stored_world=stored_world,
        validated_world=validated_world,
    )


def _rule_package_reference(packages: ValidatedGamePackages) -> PackageReference:
    manifest = packages.rule_package.manifest
    return PackageReference(
        package_id=manifest.package_id,
        package_version=manifest.package_version,
    )


def _scenario_package_reference(packages: ValidatedGamePackages) -> PackageReference:
    manifest = packages.scenario_package.manifest
    return PackageReference(
        package_id=manifest.package_id,
        package_version=manifest.package_version,
    )


def _initial_scheduled_queue(
    packages: ValidatedGamePackages, world_id: UUID
) -> ScheduledActivityQueue:
    return ScheduledActivityQueue(
        activities=tuple(
            NpcScheduledActivity(
                activity_type="npc",
                activity_id=uuid5(
                    world_id,
                    (
                        "initial-npc-activity:"
                        f"{position}:{declaration.npc_id}:"
                        f"{declaration.eligible_at_seconds}"
                    ),
                ),
                eligible_at_seconds=declaration.eligible_at_seconds,
                insertion_sequence=position,
                npc_id=declaration.npc_id,
            )
            for position, declaration in enumerate(
                packages.scenario_package.definition.initial_npc_activities
            )
        )
    )


def _require_compatible_packages(
    stored_world: StoredWorld, packages: ValidatedGamePackages
) -> None:
    if stored_world.rule_package != _rule_package_reference(
        packages
    ) or stored_world.scenario_package != _scenario_package_reference(packages):
        raise WorldPackageMismatchError(
            "validated packages do not match the stored world's package ownership"
        )
