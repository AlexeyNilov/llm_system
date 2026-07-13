import json
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.game_packages import ValidatedGamePackages
from llm_system.simulation import (
    EnvironmentalScheduledActivity,
    NpcScheduledActivity,
    ScheduledActivity,
    ScheduledActivityQueue,
    ScheduledActivitySelection,
    SystemDirectorScheduledActivity,
    ValidatedWorldState,
    WorldState,
    select_eligible_activities,
)


def _environmental(
    suffix: int, eligible_at_seconds: int, insertion_sequence: int
) -> EnvironmentalScheduledActivity:
    return EnvironmentalScheduledActivity(
        activity_type="environmental",
        activity_id=UUID(f"00000000-0000-4000-8000-{suffix:012d}"),
        eligible_at_seconds=eligible_at_seconds,
        insertion_sequence=insertion_sequence,
        schedule_id=f"schedule-{suffix}",
    )


def _npc(
    suffix: int, eligible_at_seconds: int, insertion_sequence: int
) -> NpcScheduledActivity:
    return NpcScheduledActivity(
        activity_type="npc",
        activity_id=UUID(f"00000000-0000-4000-8000-{suffix:012d}"),
        eligible_at_seconds=eligible_at_seconds,
        insertion_sequence=insertion_sequence,
        npc_id=f"npc-{suffix}",
    )


def _director(
    suffix: int, eligible_at_seconds: int, insertion_sequence: int
) -> SystemDirectorScheduledActivity:
    return SystemDirectorScheduledActivity(
        activity_type="system_director",
        activity_id=UUID(f"00000000-0000-4000-8000-{suffix:012d}"),
        eligible_at_seconds=eligible_at_seconds,
        insertion_sequence=insertion_sequence,
        hook_id=f"hook-{suffix}",
    )


def _world(simulation_time_seconds: int) -> ValidatedWorldState:
    state = WorldState(
        simulation_time_seconds=simulation_time_seconds,
        characters=(),
        objects=(),
        connections=(),
    )
    return ValidatedWorldState.model_construct(
        packages=cast(ValidatedGamePackages, object()), state=state
    )


def _selection(
    selected_at_seconds: int,
    eligible: tuple[ScheduledActivity, ...],
    remaining: tuple[ScheduledActivity, ...],
) -> ScheduledActivitySelection:
    return ScheduledActivitySelection(
        selected_at_seconds=selected_at_seconds,
        eligible_activities=eligible,
        remaining_queue=ScheduledActivityQueue(activities=remaining),
    )


def test_selection_includes_overdue_and_exactly_due_and_preserves_future_order() -> (
    None
):
    future_later = _environmental(4, 30, 4)
    due = _npc(2, 20, 2)
    future_sooner = _director(3, 21, 3)
    overdue = _environmental(1, 10, 1)
    queue = ScheduledActivityQueue(
        activities=(future_later, due, future_sooner, overdue)
    )

    result = select_eligible_activities(_world(20), queue)

    assert result.selected_at_seconds == 20
    assert result.eligible_activities == (overdue, due)
    assert result.remaining_queue.activities == (future_later, future_sooner)


def test_selection_orders_by_time_then_phase_then_insertion_not_storage_or_uuid() -> (
    None
):
    later = _environmental(1, 11, 5)
    director = _director(2, 10, 0)
    npc_later_sequence = _npc(3, 10, 4)
    environmental = _environmental(9, 10, 3)
    npc_earlier_sequence = _npc(8, 10, 2)
    queue = ScheduledActivityQueue(
        activities=(
            later,
            director,
            npc_later_sequence,
            environmental,
            npc_earlier_sequence,
        )
    )

    result = select_eligible_activities(_world(11), queue)

    assert result.eligible_activities == (
        environmental,
        npc_earlier_sequence,
        npc_later_sequence,
        director,
        later,
    )


def test_empty_and_none_eligible_selections_reuse_exact_input_queue() -> None:
    empty = ScheduledActivityQueue(activities=())
    future = _npc(1, 11, 0)
    future_queue = ScheduledActivityQueue(activities=(future,))

    empty_result = select_eligible_activities(_world(10), empty)
    future_result = select_eligible_activities(_world(10), future_queue)

    assert empty_result.eligible_activities == ()
    assert empty_result.remaining_queue is empty
    assert future_result.eligible_activities == ()
    assert future_result.remaining_queue is future_queue


def test_some_and_all_eligible_create_new_queue_and_retain_exact_activities() -> None:
    due = _npc(1, 10, 0)
    future = _environmental(2, 11, 1)
    some_queue = ScheduledActivityQueue(activities=(future, due))
    all_queue = ScheduledActivityQueue(activities=(due,))

    some_result = select_eligible_activities(_world(10), some_queue)
    all_result = select_eligible_activities(_world(10), all_queue)

    assert some_result.eligible_activities[0] is due
    assert some_result.remaining_queue is not some_queue
    assert some_result.remaining_queue.activities[0] is future
    assert all_result.remaining_queue is not all_queue
    assert all_result.remaining_queue.activities == ()


def test_selection_result_normalizes_serialized_eligible_list_to_tuple() -> None:
    due = _npc(1, 10, 0)
    result = ScheduledActivitySelection.model_validate_json(
        json.dumps(
            {
                "selected_at_seconds": 10,
                "eligible_activities": [due.model_dump(mode="json")],
                "remaining_queue": {"activities": []},
            }
        )
    )

    assert isinstance(result.eligible_activities, tuple)
    assert result.eligible_activities == (due,)


def test_selection_result_is_strict_frozen_and_has_exact_fields() -> None:
    result = _selection(10, (), ())

    assert tuple(ScheduledActivitySelection.model_fields) == (
        "selected_at_seconds",
        "eligible_activities",
        "remaining_queue",
    )
    with pytest.raises(ValidationError):
        result.selected_at_seconds = 11
    with pytest.raises(ValidationError):
        ScheduledActivitySelection.model_validate(
            {
                "selected_at_seconds": "10",
                "eligible_activities": [],
                "remaining_queue": {"activities": []},
            }
        )
    with pytest.raises(ValidationError):
        ScheduledActivitySelection.model_validate(
            {
                "selected_at_seconds": 10,
                "eligible_activities": [],
                "remaining_queue": {"activities": []},
                "claimed": True,
            }
        )


@pytest.mark.parametrize("invalid_shape", ({}, "activities", None, set()))
def test_selection_result_rejects_non_list_or_tuple_eligible_collection(
    invalid_shape: object,
) -> None:
    with pytest.raises(ValidationError, match="eligible_activities"):
        ScheduledActivitySelection.model_validate(
            {
                "selected_at_seconds": 10,
                "eligible_activities": invalid_shape,
                "remaining_queue": {"activities": []},
            }
        )


def test_selection_result_rejects_future_eligible_activity() -> None:
    with pytest.raises(ValidationError, match="eligible activities must be due"):
        _selection(10, (_npc(1, 11, 0),), ())


def test_selection_result_rejects_due_remaining_activity() -> None:
    with pytest.raises(ValidationError, match="remaining activities must be future"):
        _selection(10, (), (_npc(1, 10, 0),))


def test_selection_result_rejects_incorrect_eligible_order() -> None:
    environmental = _environmental(1, 10, 1)
    npc = _npc(2, 10, 0)

    with pytest.raises(ValidationError, match="scheduler order"):
        _selection(10, (npc, environmental), ())


def test_selection_result_reports_order_before_due_remaining_activity() -> None:
    environmental = _environmental(1, 10, 1)
    npc = _npc(2, 10, 0)
    due_remaining = _director(3, 10, 2)

    with pytest.raises(ValidationError, match="scheduler order"):
        _selection(10, (npc, environmental), (due_remaining,))


def test_selection_result_rejects_duplicate_identity_across_partition() -> None:
    eligible = _environmental(1, 10, 0)
    remaining = NpcScheduledActivity(
        activity_type="npc",
        activity_id=eligible.activity_id,
        eligible_at_seconds=11,
        insertion_sequence=1,
        npc_id="npc-1",
    )

    with pytest.raises(ValidationError, match="unique activity_id"):
        _selection(10, (eligible,), (remaining,))


def test_selection_result_rejects_duplicate_sequence_across_partition() -> None:
    eligible = _environmental(1, 10, 0)
    remaining = _npc(2, 11, 0)

    with pytest.raises(ValidationError, match="unique insertion_sequence"):
        _selection(10, (eligible,), (remaining,))


def test_selection_is_deterministic_and_does_not_mutate_inputs() -> None:
    due = _npc(1, 10, 0)
    future = _environmental(2, 11, 1)
    world = _world(10)
    queue = ScheduledActivityQueue(activities=(future, due))
    original_state = world.state.model_dump()
    original_queue = queue.model_dump()

    first = select_eligible_activities(world, queue)
    second = select_eligible_activities(world, queue)

    assert first == second
    assert first.eligible_activities[0] is due
    assert world.state.model_dump() == original_state
    assert queue.model_dump() == original_queue
