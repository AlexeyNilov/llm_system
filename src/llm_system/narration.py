from collections.abc import Iterable
from enum import Enum

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


class NarrationStyleVoice(str, Enum):
    DIRECT = "direct"
    OBSERVATIONAL = "observational"


class NarrationStyleSection(str, Enum):
    LOCATION = "location"
    CHARACTERS = "characters"
    OBJECTS = "objects"
    CONNECTIONS = "connections"


class NarrationStylePlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    voice: NarrationStyleVoice
    section_order: tuple[NarrationStyleSection, ...]


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


def default_narration_style_plan(
    context: PlayerNarrationContext,
) -> NarrationStylePlan:
    return NarrationStylePlan(
        voice=NarrationStyleVoice.DIRECT,
        section_order=_eligible_sections(context),
    )


def is_valid_narration_style_plan(
    context: PlayerNarrationContext, plan: NarrationStylePlan
) -> bool:
    eligible_sections = _eligible_sections(context)
    return (
        len(plan.section_order) == len(eligible_sections)
        and len(set(plan.section_order)) == len(plan.section_order)
        and set(plan.section_order) == set(eligible_sections)
    )


def render_player_narration(
    context: PlayerNarrationContext, plan: NarrationStylePlan | None = None
) -> PlayerNarration:
    effective_plan = plan or default_narration_style_plan(context)
    if not is_valid_narration_style_plan(context, effective_plan):
        raise ValueError("narration style plan must contain each eligible section once")
    sentences = [
        _render_section(context, effective_plan.voice, section)
        for section in effective_plan.section_order
    ]
    return PlayerNarration(text=" ".join(sentences))


def _eligible_sections(
    context: PlayerNarrationContext,
) -> tuple[NarrationStyleSection, ...]:
    sections = [NarrationStyleSection.LOCATION]
    if context.co_located_character_names:
        sections.append(NarrationStyleSection.CHARACTERS)
    if context.visible_object_names:
        sections.append(NarrationStyleSection.OBJECTS)
    sections.append(NarrationStyleSection.CONNECTIONS)
    return tuple(sections)


def _render_section(
    context: PlayerNarrationContext,
    voice: NarrationStyleVoice,
    section: NarrationStyleSection,
) -> str:
    if section is NarrationStyleSection.LOCATION:
        return _location_sentence(context, voice)
    if section is NarrationStyleSection.CHARACTERS:
        return _characters_sentence(context, voice)
    if section is NarrationStyleSection.OBJECTS:
        return _objects_sentence(context, voice)
    return _connections_sentence(context, voice)


def _location_sentence(
    context: PlayerNarrationContext, voice: NarrationStyleVoice
) -> str:
    if voice is NarrationStyleVoice.DIRECT:
        return f"You are at {context.current_location_name}."
    return f"Location: {context.current_location_name}."


def _characters_sentence(
    context: PlayerNarrationContext, voice: NarrationStyleVoice
) -> str:
    names = _join_names(context.co_located_character_names)
    if voice is NarrationStyleVoice.DIRECT:
        return f"Nearby: {names}."
    return f"Characters: {names}."


def _objects_sentence(
    context: PlayerNarrationContext, voice: NarrationStyleVoice
) -> str:
    names = _join_names(context.visible_object_names)
    if voice is NarrationStyleVoice.DIRECT:
        return f"Visible objects: {names}."
    return f"Objects: {names}."


def _connections_sentence(
    context: PlayerNarrationContext, voice: NarrationStyleVoice
) -> str:
    if context.outgoing_connections:
        exits = tuple(
            f"{connection.name} ({'available' if connection.is_available else 'unavailable'})"
            for connection in context.outgoing_connections
        )
        label = "Exits" if voice is NarrationStyleVoice.DIRECT else "Connections"
        return f"{label}: {_join_names(exits)}."
    if voice is NarrationStyleVoice.DIRECT:
        return "There are no visible exits."
    return "Connections: none visible."


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
