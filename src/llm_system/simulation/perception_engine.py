from uuid import UUID

from llm_system.game_packages.entities import (
    NpcCharacterDefinition,
    ObjectDefinition,
    PlayerCharacterDefinition,
)
from llm_system.simulation._types import AuthoredId
from llm_system.simulation.events import (
    ActorActionFailedEvent,
    ActorHelpedEvent,
    ActorMovedEvent,
    ActorObservedEvent,
    ActorSpokeEvent,
    ActorWaitedEvent,
    CanonicalEvent,
    ObjectTakenEvent,
    ObjectUsedEvent,
)
from llm_system.simulation.perception import (
    CharacterObserved,
    ConnectionObserved,
    EventObserved,
    LocationObserved,
    ObjectObserved,
    Observation,
    PerceptionSnapshot,
)
from llm_system.simulation.state import (
    CharacterState,
    ObjectAtLocation,
    ObjectPossessedByCharacter,
)
from llm_system.simulation.validation import ValidatedWorldState


class PerceptionObserverNotFoundError(ValueError):
    def __init__(self, observer_id: AuthoredId) -> None:
        super().__init__(f"perception observer not found: {observer_id}")
        self.observer_id: AuthoredId = observer_id


class FutureEventFeedbackError(ValueError):
    def __init__(
        self,
        event_id: UUID,
        occurred_at_seconds: int,
        perceived_at_seconds: int,
    ) -> None:
        super().__init__(
            f"canonical event {event_id} occurred at {occurred_at_seconds}, "
            f"later than perception time {perceived_at_seconds}"
        )
        self.event_id: UUID = event_id
        self.occurred_at_seconds: int = occurred_at_seconds
        self.perceived_at_seconds: int = perceived_at_seconds


def _find_observer(
    world: ValidatedWorldState, observer_id: AuthoredId
) -> CharacterState:
    for character in world.state.characters:
        if character.character_id == observer_id:
            return character
    raise PerceptionObserverNotFoundError(observer_id)


def _event_owner_id(event: CanonicalEvent) -> AuthoredId:
    if isinstance(event, ActorSpokeEvent):
        return event.speaker_id
    if isinstance(
        event,
        (
            ActorObservedEvent,
            ActorMovedEvent,
            ObjectTakenEvent,
            ObjectUsedEvent,
            ActorHelpedEvent,
            ActorWaitedEvent,
            ActorActionFailedEvent,
        ),
    ):
        return event.actor_id


def _validate_event_times(
    events: tuple[CanonicalEvent, ...], perceived_at_seconds: int
) -> None:
    for event in events:
        if event.occurred_at_seconds > perceived_at_seconds:
            raise FutureEventFeedbackError(
                event.event_id,
                event.occurred_at_seconds,
                perceived_at_seconds,
            )


def _connection_observations(
    world: ValidatedWorldState,
    observer_id: AuthoredId,
    location_id: AuthoredId,
) -> tuple[ConnectionObserved, ...]:
    states = {state.connection_id: state for state in world.state.connections}
    connections = world.packages.scenario_package.definition.spatial_graph.connections
    return tuple(
        ConnectionObserved(
            observation_type="connection",
            source_type="current_state",
            observer_id=observer_id,
            observed_at_seconds=world.state.simulation_time_seconds,
            connection_id=connection.id,
            is_available=states[connection.id].is_available,
        )
        for connection in connections
        if connection.source_location_id == location_id
    )


def _character_observations(
    world: ValidatedWorldState,
    observer_id: AuthoredId,
    location_id: AuthoredId,
) -> tuple[CharacterObserved, ...]:
    states = {state.character_id: state for state in world.state.characters}
    entities = world.packages.scenario_package.definition.entity_collection.entities
    return tuple(
        CharacterObserved(
            observation_type="character",
            source_type="current_state",
            observer_id=observer_id,
            observed_at_seconds=world.state.simulation_time_seconds,
            character_id=entity.id,
        )
        for entity in entities
        if isinstance(entity, (PlayerCharacterDefinition, NpcCharacterDefinition))
        and entity.id != observer_id
        and states[entity.id].location_id == location_id
    )


def _object_is_visible(
    placement: ObjectAtLocation | ObjectPossessedByCharacter,
    observer_id: AuthoredId,
    location_id: AuthoredId,
) -> bool:
    return (
        isinstance(placement, ObjectAtLocation) and placement.location_id == location_id
    ) or (
        isinstance(placement, ObjectPossessedByCharacter)
        and placement.character_id == observer_id
    )


def _object_observations(
    world: ValidatedWorldState,
    observer_id: AuthoredId,
    location_id: AuthoredId,
) -> tuple[ObjectObserved, ...]:
    states = {state.object_id: state for state in world.state.objects}
    entities = world.packages.scenario_package.definition.entity_collection.entities
    return tuple(
        ObjectObserved(
            observation_type="object",
            source_type="current_state",
            observer_id=observer_id,
            observed_at_seconds=world.state.simulation_time_seconds,
            object_id=entity.id,
            placement=states[entity.id].placement,
        )
        for entity in entities
        if isinstance(entity, ObjectDefinition)
        and _object_is_visible(states[entity.id].placement, observer_id, location_id)
    )


def project_current_perception(
    world: ValidatedWorldState, observer_id: AuthoredId
) -> PerceptionSnapshot:
    observer = _find_observer(world, observer_id)
    time = world.state.simulation_time_seconds
    observations: tuple[Observation, ...] = (
        LocationObserved(
            observation_type="location",
            source_type="current_state",
            observer_id=observer_id,
            observed_at_seconds=time,
            location_id=observer.location_id,
        ),
        *_connection_observations(world, observer_id, observer.location_id),
        *_character_observations(world, observer_id, observer.location_id),
        *_object_observations(world, observer_id, observer.location_id),
    )
    return PerceptionSnapshot(
        observer_id=observer_id,
        perceived_at_seconds=time,
        observations=observations,
    )


def project_self_event_feedback(
    world: ValidatedWorldState,
    observer_id: AuthoredId,
    events: tuple[CanonicalEvent, ...],
) -> tuple[EventObserved, ...]:
    _find_observer(world, observer_id)
    time = world.state.simulation_time_seconds
    _validate_event_times(events, time)
    return tuple(
        EventObserved(
            observation_type="event",
            source_type="canonical_event",
            observer_id=observer_id,
            observed_at_seconds=time,
            event=event,
        )
        for event in events
        if _event_owner_id(event) == observer_id
    )


def project_addressed_speech_feedback(
    world: ValidatedWorldState,
    observer_id: AuthoredId,
    events: tuple[CanonicalEvent, ...],
) -> tuple[EventObserved, ...]:
    _find_observer(world, observer_id)
    time = world.state.simulation_time_seconds
    _validate_event_times(events, time)
    return tuple(
        EventObserved(
            observation_type="event",
            source_type="canonical_event",
            observer_id=observer_id,
            observed_at_seconds=time,
            event=event,
        )
        for event in events
        if isinstance(event, ActorSpokeEvent) and event.recipient_id == observer_id
    )
