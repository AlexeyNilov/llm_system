import json
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    ActorActionFailedEvent,
    ActorHelpedEvent,
    ActorMovedEvent,
    ActorObservedEvent,
    ActorSpokeEvent,
    ActorWaitedEvent,
    CanonicalEvent,
    CharacterTarget,
    ObjectAtLocation,
    ObjectTakenEvent,
    ObjectUsedEvent,
)

EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")


def _base(event_type: str) -> dict[str, object]:
    return {
        "event_type": event_type,
        "event_id": str(EVENT_ID),
        "outcome_id": str(OUTCOME_ID),
        "occurred_at_seconds": 30,
    }


def _python_base(event_type: str) -> dict[str, object]:
    return _base(event_type) | {"event_id": EVENT_ID, "outcome_id": OUTCOME_ID}


def test_canonical_event_discriminates_and_json_round_trips_all_variants() -> None:
    adapter: TypeAdapter[CanonicalEvent] = TypeAdapter(CanonicalEvent)
    payloads = (
        _base("actor_observed")
        | {"actor_id": "marin", "target": {"target_type": "surroundings"}},
        _base("actor_moved")
        | {
            "actor_id": "marin",
            "connection_id": "market-to-dock",
            "from_location_id": "market",
            "to_location_id": "dock",
        },
        _base("actor_spoke")
        | {"speaker_id": "marin", "recipient_id": "sela", "utterance": "Hello."},
        _base("object_taken")
        | {
            "actor_id": "marin",
            "object_id": "medicine-kit",
            "previous_placement": {
                "placement_type": "location",
                "location_id": "market",
            },
        },
        _base("object_used")
        | {
            "actor_id": "marin",
            "object_id": "medicine-kit",
            "target": {"target_type": "character", "character_id": "sela"},
        },
        _base("actor_helped") | {"actor_id": "marin", "assisted_character_id": "sela"},
        _base("actor_waited") | {"actor_id": "marin", "duration_seconds": 5},
        _base("actor_action_failed")
        | {"actor_id": "marin", "attempted_operation": "move"},
    )

    events = tuple(adapter.validate_json(json.dumps(payload)) for payload in payloads)

    assert tuple(type(event) for event in events) == (
        ActorObservedEvent,
        ActorMovedEvent,
        ActorSpokeEvent,
        ObjectTakenEvent,
        ObjectUsedEvent,
        ActorHelpedEvent,
        ActorWaitedEvent,
        ActorActionFailedEvent,
    )
    assert events[0].event_id == EVENT_ID
    assert events[0].outcome_id == OUTCOME_ID
    taken_event = events[3]
    used_event = events[4]
    assert isinstance(taken_event, ObjectTakenEvent)
    assert isinstance(used_event, ObjectUsedEvent)
    assert isinstance(taken_event.previous_placement, ObjectAtLocation)
    assert isinstance(used_event.target, CharacterTarget)
    for event, payload in zip(events, payloads, strict=True):
        assert adapter.dump_python(event, mode="json") == payload


def test_event_identity_time_and_payload_scalars_are_required_and_strict() -> None:
    valid_wait = _base("actor_waited") | {"actor_id": "marin", "duration_seconds": 1}
    invalid = (
        {key: value for key, value in valid_wait.items() if key != "event_id"},
        valid_wait | {"event_id": "not-a-uuid"},
        valid_wait | {"occurred_at_seconds": True},
        valid_wait | {"occurred_at_seconds": -1},
        valid_wait | {"duration_seconds": True},
        valid_wait | {"duration_seconds": 0},
        valid_wait | {"visibility": "player"},
    )
    for payload in invalid:
        with pytest.raises(ValidationError):
            TypeAdapter(CanonicalEvent).validate_python(payload)


def test_operation_specific_leaf_invariants_and_failed_operation_vocabulary() -> None:
    with pytest.raises(ValidationError):
        ActorMovedEvent.model_validate(
            _python_base("actor_moved")
            | {
                "actor_id": "marin",
                "connection_id": "market-to-dock",
                "from_location_id": "market",
                "to_location_id": "market",
            }
        )
    with pytest.raises(ValidationError):
        ActorSpokeEvent.model_validate(
            _python_base("actor_spoke")
            | {"speaker_id": "marin", "recipient_id": "marin", "utterance": "   "}
        )
    for operation in ("observe", "move", "speak", "take", "use", "help", "wait"):
        event = ActorActionFailedEvent.model_validate(
            _python_base("actor_action_failed")
            | {"actor_id": "marin", "attempted_operation": operation}
        )
        assert event.attempted_operation == operation
    with pytest.raises(ValidationError):
        ActorActionFailedEvent.model_validate(
            _python_base("actor_action_failed")
            | {"actor_id": "marin", "attempted_operation": "attack"}
        )


def test_events_are_immutable_factual_leaves_without_presentation_or_outcome_aggregate() -> (
    None
):
    event = ActorObservedEvent.model_validate(
        _python_base("actor_observed")
        | {"actor_id": "marin", "target": {"target_type": "surroundings"}}
    )

    assert set(type(event).model_fields) == {
        "event_type",
        "event_id",
        "outcome_id",
        "occurred_at_seconds",
        "actor_id",
        "target",
    }
    with pytest.raises(ValidationError):
        event.actor_id = "sela"
    with pytest.raises(ValidationError):
        ActorObservedEvent.model_validate(
            event.model_dump() | {"narration": "Marin looked around."}
        )
