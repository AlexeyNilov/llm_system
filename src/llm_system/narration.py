from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict

from llm_system.game_packages._types import NonBlankText
from llm_system.game_packages.entities import (
    ObjectDefinition,
    PlayerCharacterDefinition,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.simulation.perception import (
    CharacterObserved,
    ConnectionObserved,
    EventObserved,
    LocationObserved,
    ObjectObserved,
    PerceptionSnapshot,
)


class PlayerNarration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    text: NonBlankText


class PlayerNarrationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    current_location_name: NonBlankText
    co_located_character_names: tuple[NonBlankText, ...]
    visible_object_names: tuple[NonBlankText, ...]
    outgoing_connections: tuple["NarratedConnection", ...]


class NarratedConnection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: NonBlankText
    is_available: bool


class NarrationContextError(ValueError):
    pass


class NarrationObserverError(NarrationContextError):
    pass


class NarrationCurrentLocationError(NarrationContextError):
    pass


class UnknownObservedIdentifierNarrationError(NarrationContextError):
    pass


class EventObservationNarrationError(NarrationContextError):
    pass


def build_player_narration_context(
    packages: ValidatedGamePackages, snapshot: PerceptionSnapshot
) -> PlayerNarrationContext:
    player = _player(packages)
    if snapshot.observer_id != player.id:
        raise NarrationObserverError(
            f"narration observer is not the authored player: {snapshot.observer_id}"
        )

    locations: list[LocationObserved] = []
    characters: list[CharacterObserved] = []
    objects: list[ObjectObserved] = []
    connections: list[ConnectionObserved] = []
    for observation in snapshot.observations:
        if isinstance(observation, EventObserved):
            raise EventObservationNarrationError(
                "event observations cannot be rendered as player narration"
            )
        if isinstance(observation, LocationObserved):
            locations.append(observation)
        elif isinstance(observation, CharacterObserved):
            characters.append(observation)
        elif isinstance(observation, ObjectObserved):
            objects.append(observation)
        else:
            assert isinstance(observation, ConnectionObserved)
            connections.append(observation)

    if len(locations) != 1:
        raise NarrationCurrentLocationError(
            "player narration requires exactly one current location observation"
        )

    definition = packages.scenario_package.definition
    location_name = _name_for_identifier(
        locations[0].location_id,
        ((record.id, record.name) for record in definition.spatial_graph.locations),
    )
    character_names = tuple(
        _name_for_identifier(
            observation.character_id,
            (
                (record.id, record.name)
                for record in definition.entity_collection.entities
                if not isinstance(record, ObjectDefinition)
            ),
        )
        for observation in characters
    )
    object_names = tuple(
        _name_for_identifier(
            observation.object_id,
            (
                (record.id, record.name)
                for record in definition.entity_collection.entities
                if isinstance(record, ObjectDefinition)
            ),
        )
        for observation in objects
    )
    connection_names = tuple(
        _name_for_identifier(
            observation.connection_id,
            (
                (record.id, record.name)
                for record in definition.spatial_graph.connections
            ),
        )
        for observation in connections
    )

    return PlayerNarrationContext(
        current_location_name=location_name,
        co_located_character_names=character_names,
        visible_object_names=object_names,
        outgoing_connections=tuple(
            NarratedConnection(name=name, is_available=observation.is_available)
            for name, observation in zip(connection_names, connections, strict=True)
        ),
    )


def render_player_narration(context: PlayerNarrationContext) -> PlayerNarration:
    sentences = [f"You are at {context.current_location_name}."]
    if context.co_located_character_names:
        sentences.append(f"Nearby: {_join_names(context.co_located_character_names)}.")
    if context.visible_object_names:
        sentences.append(
            f"Visible objects: {_join_names(context.visible_object_names)}."
        )
    if context.outgoing_connections:
        exits = tuple(
            f"{connection.name} ({'available' if connection.is_available else 'unavailable'})"
            for connection in context.outgoing_connections
        )
        sentences.append(f"Exits: {_join_names(exits)}.")
    else:
        sentences.append("There are no visible exits.")
    return PlayerNarration(text=" ".join(sentences))


def _player(packages: ValidatedGamePackages) -> PlayerCharacterDefinition:
    players = tuple(
        entity
        for entity in packages.scenario_package.definition.entity_collection.entities
        if isinstance(entity, PlayerCharacterDefinition)
    )
    if len(players) != 1:
        raise NarrationObserverError("validated packages must contain one player")
    return players[0]


def _name_for_identifier(identifier: str, records: Iterable[tuple[str, str]]) -> str:
    for record_id, name in records:
        if record_id == identifier:
            return name
    raise UnknownObservedIdentifierNarrationError(
        f"observed identifier has no approved display name: {identifier}"
    )


def _join_names(names: tuple[str, ...]) -> str:
    return ", ".join(names)
