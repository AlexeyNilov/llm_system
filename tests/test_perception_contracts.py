from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    ActorWaitedEvent,
    CharacterObserved,
    ConnectionObserved,
    EventObserved,
    LocationObserved,
    ObjectAtLocation,
    ObjectObserved,
    Observation,
    PerceptionSnapshot,
)

EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")


def _waited_event(occurred_at_seconds: int = 30) -> ActorWaitedEvent:
    return ActorWaitedEvent(
        event_type="actor_waited",
        event_id=EVENT_ID,
        outcome_id=OUTCOME_ID,
        occurred_at_seconds=occurred_at_seconds,
        actor_id="marin",
        duration_seconds=5,
    )


def test_observation_variants_preserve_exact_typed_payload_and_provenance() -> None:
    placement = ObjectAtLocation(placement_type="location", location_id="waystation")
    event = _waited_event()
    observations = (
        LocationObserved(
            observation_type="location",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=30,
            location_id="waystation",
        ),
        ConnectionObserved(
            observation_type="connection",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=30,
            connection_id="waystation-to-span",
            is_available=True,
        ),
        CharacterObserved(
            observation_type="character",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=30,
            character_id="sela",
        ),
        ObjectObserved(
            observation_type="object",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=30,
            object_id="medicine-kit",
            placement=placement,
        ),
        EventObserved(
            observation_type="event",
            source_type="canonical_event",
            observer_id="marin",
            observed_at_seconds=30,
            event=event,
        ),
    )

    assert tuple(observation.model_dump() for observation in observations) == (
        {
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "observation_type": "location",
            "source_type": "current_state",
            "location_id": "waystation",
        },
        {
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "observation_type": "connection",
            "source_type": "current_state",
            "connection_id": "waystation-to-span",
            "is_available": True,
        },
        {
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "observation_type": "character",
            "source_type": "current_state",
            "character_id": "sela",
        },
        {
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "observation_type": "object",
            "source_type": "current_state",
            "object_id": "medicine-kit",
            "placement": {
                "placement_type": "location",
                "location_id": "waystation",
            },
        },
        {
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "observation_type": "event",
            "source_type": "canonical_event",
            "event": event.model_dump(),
        },
    )
    assert observations[3].placement is placement
    assert observations[4].event is event


def test_observation_is_a_closed_discriminated_union() -> None:
    adapter: TypeAdapter[Observation] = TypeAdapter(Observation)

    observation = adapter.validate_python(
        {
            "observation_type": "character",
            "source_type": "current_state",
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "character_id": "sela",
        }
    )

    assert isinstance(observation, CharacterObserved)
    for invalid in (
        {
            "observation_type": "custom",
            "source_type": "current_state",
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "payload": {},
        },
        {
            "observation_type": "location",
            "source_type": "canonical_event",
            "observer_id": "marin",
            "observed_at_seconds": 30,
            "location_id": "waystation",
        },
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid)


def test_observations_reject_loose_scalars_and_enriched_payloads() -> None:
    invalid_observations = (
        (
            ConnectionObserved,
            {
                "observation_type": "connection",
                "source_type": "current_state",
                "observer_id": "marin",
                "observed_at_seconds": 30,
                "connection_id": "waystation-to-span",
                "is_available": 1,
            },
        ),
        (
            LocationObserved,
            {
                "observation_type": "location",
                "source_type": "current_state",
                "observer_id": "Marin",
                "observed_at_seconds": 30,
                "location_id": "waystation",
            },
        ),
        (
            CharacterObserved,
            {
                "observation_type": "character",
                "source_type": "current_state",
                "observer_id": "marin",
                "observed_at_seconds": 30,
                "character_id": "sela",
                "name": "Sela",
            },
        ),
        (
            ObjectObserved,
            {
                "observation_type": "object",
                "source_type": "current_state",
                "observer_id": "marin",
                "observed_at_seconds": 30,
                "object_id": "medicine-kit",
                "placement": {
                    "placement_type": "location",
                    "location_id": "unresolved-location",
                },
                "confidence": 1.0,
            },
        ),
    )

    for model, payload in invalid_observations:
        with pytest.raises(ValidationError):
            model.model_validate(payload)


def test_event_observation_accepts_same_time_and_past_events_unchanged() -> None:
    same_time_event = _waited_event(30)
    past_event = _waited_event(20)

    same_time = EventObserved(
        observation_type="event",
        source_type="canonical_event",
        observer_id="marin",
        observed_at_seconds=30,
        event=same_time_event,
    )
    past = EventObserved(
        observation_type="event",
        source_type="canonical_event",
        observer_id="marin",
        observed_at_seconds=30,
        event=past_event,
    )

    assert same_time.event is same_time_event
    assert past.event is past_event


def test_event_observation_rejects_an_event_from_the_future() -> None:
    with pytest.raises(ValidationError, match="event"):
        EventObserved(
            observation_type="event",
            source_type="canonical_event",
            observer_id="marin",
            observed_at_seconds=30,
            event=_waited_event(31),
        )


def test_perception_snapshot_accepts_empty_and_consistent_observations() -> None:
    empty = PerceptionSnapshot(
        observer_id="marin", perceived_at_seconds=30, observations=()
    )
    observations = (
        LocationObserved(
            observation_type="location",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=30,
            location_id="waystation",
        ),
        CharacterObserved(
            observation_type="character",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=30,
            character_id="sela",
        ),
    )
    populated = PerceptionSnapshot(
        observer_id="marin", perceived_at_seconds=30, observations=observations
    )

    assert empty.observations == ()
    assert populated.observations == observations


def test_perception_snapshot_normalizes_lists_and_preserves_order_and_duplicates() -> (
    None
):
    location = LocationObserved(
        observation_type="location",
        source_type="current_state",
        observer_id="marin",
        observed_at_seconds=30,
        location_id="waystation",
    )
    character = CharacterObserved(
        observation_type="character",
        source_type="current_state",
        observer_id="marin",
        observed_at_seconds=30,
        character_id="sela",
    )

    snapshot = PerceptionSnapshot.model_validate(
        {
            "observer_id": "marin",
            "perceived_at_seconds": 30,
            "observations": [character, location, character],
        }
    )

    assert isinstance(snapshot.observations, tuple)
    assert snapshot.observations == (character, location, character)
    assert snapshot.observations[0] is snapshot.observations[2]


def test_perception_snapshot_rejects_observer_and_time_mismatches() -> None:
    mismatches = (
        LocationObserved(
            observation_type="location",
            source_type="current_state",
            observer_id="sela",
            observed_at_seconds=30,
            location_id="waystation",
        ),
        LocationObserved(
            observation_type="location",
            source_type="current_state",
            observer_id="marin",
            observed_at_seconds=29,
            location_id="waystation",
        ),
    )

    for observation in mismatches:
        with pytest.raises(ValidationError, match=r"(observer|time)") as error:
            PerceptionSnapshot(
                observer_id="marin",
                perceived_at_seconds=30,
                observations=(observation,),
            )
        assert str(error.value).strip()


def test_perception_snapshot_accepts_only_exact_lists_or_tuples() -> None:
    with pytest.raises(ValidationError, match="lists or tuples"):
        PerceptionSnapshot.model_validate(
            {
                "observer_id": "marin",
                "perceived_at_seconds": 30,
                "observations": set(),
            }
        )


def test_observations_and_snapshots_are_immutable() -> None:
    observation = LocationObserved(
        observation_type="location",
        source_type="current_state",
        observer_id="marin",
        observed_at_seconds=30,
        location_id="waystation",
    )
    snapshot = PerceptionSnapshot(
        observer_id="marin", perceived_at_seconds=30, observations=(observation,)
    )

    with pytest.raises(ValidationError):
        observation.location_id = "span"
    with pytest.raises(ValidationError):
        snapshot.perceived_at_seconds = 31
