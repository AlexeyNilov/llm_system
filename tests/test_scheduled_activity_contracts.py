import json
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    EnvironmentalScheduledActivity,
    NpcScheduledActivity,
    ScheduledActivity,
    ScheduledActivityQueue,
    SystemDirectorScheduledActivity,
)


ENVIRONMENTAL_ID = UUID("11111111-1111-4111-8111-111111111111")
NPC_ID = UUID("22222222-2222-4222-8222-222222222222")
DIRECTOR_ID = UUID("33333333-3333-4333-8333-333333333333")


def test_scheduled_activity_union_parses_and_round_trips_exact_variants() -> None:
    adapter: TypeAdapter[ScheduledActivity] = TypeAdapter(ScheduledActivity)
    activities = (
        adapter.validate_python(
            {
                "activity_type": "environmental",
                "activity_id": ENVIRONMENTAL_ID,
                "eligible_at_seconds": 30,
                "insertion_sequence": 2,
                "schedule_id": "rising-flood",
            }
        ),
        adapter.validate_python(
            {
                "activity_type": "npc",
                "activity_id": NPC_ID,
                "eligible_at_seconds": 15,
                "insertion_sequence": 0,
                "npc_id": "sela",
            }
        ),
        adapter.validate_python(
            {
                "activity_type": "system_director",
                "activity_id": DIRECTOR_ID,
                "eligible_at_seconds": 30,
                "insertion_sequence": 1,
                "hook_id": "world-created",
            }
        ),
    )

    assert tuple(type(activity) for activity in activities) == (
        EnvironmentalScheduledActivity,
        NpcScheduledActivity,
        SystemDirectorScheduledActivity,
    )
    for activity in activities:
        assert adapter.validate_json(activity.model_dump_json()) == activity
    assert adapter.json_schema()["discriminator"]["propertyName"] == "activity_type"


def test_activity_variants_require_injected_identity_and_exact_reference_fields() -> (
    None
):
    environmental = EnvironmentalScheduledActivity(
        activity_type="environmental",
        activity_id=ENVIRONMENTAL_ID,
        eligible_at_seconds=0,
        insertion_sequence=0,
        schedule_id="rising-flood",
    )
    npc = NpcScheduledActivity(
        activity_type="npc",
        activity_id=NPC_ID,
        eligible_at_seconds=0,
        insertion_sequence=1,
        npc_id="sela",
    )
    director = SystemDirectorScheduledActivity(
        activity_type="system_director",
        activity_id=DIRECTOR_ID,
        eligible_at_seconds=0,
        insertion_sequence=2,
        hook_id="world-created",
    )

    assert environmental.schedule_id == "rising-flood"
    assert npc.npc_id == "sela"
    assert director.hook_id == "world-created"
    complete_environmental = {
        "activity_type": "environmental",
        "activity_id": ENVIRONMENTAL_ID,
        "eligible_at_seconds": 0,
        "insertion_sequence": 0,
        "schedule_id": "rising-flood",
    }
    for missing_field in (
        "activity_id",
        "eligible_at_seconds",
        "insertion_sequence",
        "schedule_id",
    ):
        incomplete = complete_environmental | {missing_field: None}
        incomplete.pop(missing_field)
        with pytest.raises(ValidationError):
            EnvironmentalScheduledActivity.model_validate(incomplete)
    with pytest.raises(ValidationError):
        NpcScheduledActivity.model_validate(
            {
                "activity_type": "npc",
                "activity_id": NPC_ID,
                "eligible_at_seconds": 0,
                "insertion_sequence": 1,
                "schedule_id": "rising-flood",
            }
        )


def test_scheduled_activity_union_rejects_unknown_variant() -> None:
    adapter: TypeAdapter[ScheduledActivity] = TypeAdapter(ScheduledActivity)

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "activity_type": "generic",
                "activity_id": ENVIRONMENTAL_ID,
                "eligible_at_seconds": 0,
                "insertion_sequence": 0,
            }
        )


def test_activity_variants_are_strict_frozen_and_reject_executable_or_phase_fields() -> (
    None
):
    activity = NpcScheduledActivity(
        activity_type="npc",
        activity_id=NPC_ID,
        eligible_at_seconds=10,
        insertion_sequence=3,
        npc_id="sela",
    )

    with pytest.raises(ValidationError):
        activity.eligible_at_seconds = 11
    for invalid_update in (
        {"eligible_at_seconds": "10"},
        {"activity_id": str(NPC_ID)},
        {"npc_id": "Sela"},
        {"phase_priority": 1},
        {"callback": "run"},
        {"proposal": {"operation": "wait"}},
    ):
        with pytest.raises(ValidationError):
            NpcScheduledActivity.model_validate(
                {
                    "activity_type": "npc",
                    "activity_id": NPC_ID,
                    "eligible_at_seconds": 10,
                    "insertion_sequence": 3,
                    "npc_id": "sela",
                    **invalid_update,
                }
            )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("eligible_at_seconds", -1),
        ("eligible_at_seconds", True),
        ("eligible_at_seconds", 1.0),
        ("insertion_sequence", -1),
        ("insertion_sequence", True),
        ("insertion_sequence", 1.0),
    ),
)
def test_activity_rejects_invalid_time_and_sequence(field: str, value: object) -> None:
    data = {
        "activity_type": "environmental",
        "activity_id": ENVIRONMENTAL_ID,
        "eligible_at_seconds": 0,
        "insertion_sequence": 0,
        "schedule_id": "rising-flood",
    }
    data[field] = value

    with pytest.raises(ValidationError):
        EnvironmentalScheduledActivity.model_validate(data)


def test_queue_normalizes_json_lists_and_is_immutable() -> None:
    queue = ScheduledActivityQueue.model_validate_json(
        json.dumps(
            {
                "activities": [
                    {
                        "activity_type": "npc",
                        "activity_id": str(NPC_ID),
                        "eligible_at_seconds": 10,
                        "insertion_sequence": 0,
                        "npc_id": "sela",
                    }
                ]
            }
        )
    )

    assert isinstance(queue.activities, tuple)
    assert isinstance(queue.activities[0], NpcScheduledActivity)
    with pytest.raises(ValidationError):
        queue.activities = ()


def test_queue_allows_empty_equal_time_and_preserves_unsorted_storage_order() -> None:
    empty = ScheduledActivityQueue(activities=())
    activities = (
        SystemDirectorScheduledActivity(
            activity_type="system_director",
            activity_id=DIRECTOR_ID,
            eligible_at_seconds=20,
            insertion_sequence=2,
            hook_id="world-created",
        ),
        EnvironmentalScheduledActivity(
            activity_type="environmental",
            activity_id=ENVIRONMENTAL_ID,
            eligible_at_seconds=20,
            insertion_sequence=1,
            schedule_id="rising-flood",
        ),
        NpcScheduledActivity(
            activity_type="npc",
            activity_id=NPC_ID,
            eligible_at_seconds=10,
            insertion_sequence=0,
            npc_id="sela",
        ),
    )
    queue = ScheduledActivityQueue(activities=activities)

    assert empty.activities == ()
    assert queue.activities == activities


def test_queue_rejects_collection_shapes_other_than_lists_and_tuples() -> None:
    invalid_shapes: tuple[object, ...] = ({}, "activities", None)
    for activities in invalid_shapes:
        with pytest.raises(ValidationError):
            ScheduledActivityQueue.model_validate({"activities": activities})
    with pytest.raises(ValidationError):
        ScheduledActivityQueue.model_validate({"activities": (), "sorted": True})


def test_queue_rejects_duplicate_activity_identity() -> None:
    with pytest.raises(ValidationError, match="activity_id"):
        ScheduledActivityQueue(
            activities=(
                EnvironmentalScheduledActivity(
                    activity_type="environmental",
                    activity_id=ENVIRONMENTAL_ID,
                    eligible_at_seconds=10,
                    insertion_sequence=0,
                    schedule_id="rising-flood",
                ),
                NpcScheduledActivity(
                    activity_type="npc",
                    activity_id=ENVIRONMENTAL_ID,
                    eligible_at_seconds=10,
                    insertion_sequence=1,
                    npc_id="unresolved-npc",
                ),
            )
        )


def test_queue_rejects_duplicate_insertion_sequence() -> None:
    with pytest.raises(ValidationError, match="insertion_sequence"):
        ScheduledActivityQueue(
            activities=(
                EnvironmentalScheduledActivity(
                    activity_type="environmental",
                    activity_id=ENVIRONMENTAL_ID,
                    eligible_at_seconds=10,
                    insertion_sequence=0,
                    schedule_id="unresolved-schedule",
                ),
                SystemDirectorScheduledActivity(
                    activity_type="system_director",
                    activity_id=DIRECTOR_ID,
                    eligible_at_seconds=10,
                    insertion_sequence=0,
                    hook_id="unresolved-hook",
                ),
            )
        )
