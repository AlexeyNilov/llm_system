from collections.abc import Sequence
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.application import NpcDecisionContext, decide_greybridge_caretaker
from llm_system.game_packages import GoalDefinition
from llm_system.simulation import (
    CharacterObserved,
    ConnectionObserved,
    LocationObserved,
    LocationTarget,
    MoveActionProposal,
    ObjectAtLocation,
    ObjectObserved,
    ObjectPossessedByCharacter,
    PerceptionSnapshot,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)
from llm_system.simulation.perception import Observation


_CARETAKER_ID = "bridge-caretaker"
_DECISION_CONTEXT_ID = UUID("20000000-0000-0000-0000-000000000041")
_OBSERVED_AT = 120


def _location(location_id: str) -> LocationObserved:
    return LocationObserved(
        observation_type="location",
        source_type="current_state",
        observer_id=_CARETAKER_ID,
        observed_at_seconds=_OBSERVED_AT,
        location_id=location_id,
    )


def _connection(connection_id: str, *, available: bool) -> ConnectionObserved:
    return ConnectionObserved(
        observation_type="connection",
        source_type="current_state",
        observer_id=_CARETAKER_ID,
        observed_at_seconds=_OBSERVED_AT,
        connection_id=connection_id,
        is_available=available,
    )


def _materials_at(location_id: str) -> ObjectObserved:
    return ObjectObserved(
        observation_type="object",
        source_type="current_state",
        observer_id=_CARETAKER_ID,
        observed_at_seconds=_OBSERVED_AT,
        object_id="reinforcement-materials",
        placement=ObjectAtLocation(placement_type="location", location_id=location_id),
    )


def _possessed_materials() -> ObjectObserved:
    return ObjectObserved(
        observation_type="object",
        source_type="current_state",
        observer_id=_CARETAKER_ID,
        observed_at_seconds=_OBSERVED_AT,
        object_id="reinforcement-materials",
        placement=ObjectPossessedByCharacter(
            placement_type="possessed_by_character", character_id=_CARETAKER_ID
        ),
    )


def _context(
    observations: Sequence[Observation], *, npc_id: str = _CARETAKER_ID
) -> NpcDecisionContext:
    return NpcDecisionContext(
        decision_context_id=_DECISION_CONTEXT_ID,
        npc_id=npc_id,
        identity_summary="The caretaker responsible for the bridge.",
        goals=(
            GoalDefinition(id="preserve-bridge", description="Preserve the bridge."),
        ),
        current_plan="Retrieve materials and reinforce the span.",
        perception=PerceptionSnapshot(
            observer_id=npc_id,
            perceived_at_seconds=_OBSERVED_AT,
            observations=tuple(observations),
        ),
    )


@pytest.mark.parametrize(
    ("observations", "expected"),
    [
        (
            (_location("greybridge-span"), _possessed_materials()),
            UseActionProposal(
                operation="use",
                object_id="reinforcement-materials",
                target=LocationTarget(
                    target_type="location", location_id="greybridge-span"
                ),
            ),
        ),
        (
            (
                _possessed_materials(),
                _location("greybridge-waystation"),
                _connection("waystation-to-span", available=True),
            ),
            MoveActionProposal(operation="move", connection_id="waystation-to-span"),
        ),
        (
            (
                _materials_at("greybridge-waystation"),
                _location("greybridge-waystation"),
            ),
            TakeActionProposal(operation="take", object_id="reinforcement-materials"),
        ),
        (
            (
                _connection("span-to-waystation", available=True),
                _location("greybridge-span"),
            ),
            MoveActionProposal(operation="move", connection_id="span-to-waystation"),
        ),
    ],
    ids=("use-at-span", "return-to-span", "take-materials", "seek-materials"),
)
def test_caretaker_proposes_each_active_rule_from_typed_observations(
    observations: tuple[Observation, ...],
    expected: UseActionProposal | MoveActionProposal | TakeActionProposal,
) -> None:
    assert decide_greybridge_caretaker(_context(observations)) == expected


@pytest.mark.parametrize(
    "observations",
    [
        (
            _location("greybridge-waystation"),
            _possessed_materials(),
            _connection("waystation-to-span", available=False),
        ),
        (_location("greybridge-span"),),
        (_materials_at("greybridge-waystation"),),
        (_location("far-bank"), _connection("span-to-waystation", available=True)),
    ],
    ids=("unavailable-return", "missing-seek-connection", "missing-location", "safe"),
)
def test_caretaker_waits_when_required_evidence_is_unavailable_or_missing(
    observations: tuple[Observation, ...],
) -> None:
    assert decide_greybridge_caretaker(_context(observations)) == WaitActionProposal(
        operation="wait", duration_seconds=60
    )


def test_caretaker_uses_priority_independently_of_observation_order_and_extras() -> (
    None
):
    observations: tuple[Observation, ...] = (
        _connection("span-to-waystation", available=True),
        _materials_at("greybridge-span"),
        _location("greybridge-waystation"),
        _connection("waystation-to-span", available=True),
        _possessed_materials(),
        CharacterObserved(
            observation_type="character",
            source_type="current_state",
            observer_id=_CARETAKER_ID,
            observed_at_seconds=_OBSERVED_AT,
            character_id="injured-courier",
        ),
        _location("greybridge-span"),
        _possessed_materials(),
    )
    expected = UseActionProposal(
        operation="use",
        object_id="reinforcement-materials",
        target=LocationTarget(target_type="location", location_id="greybridge-span"),
    )

    assert decide_greybridge_caretaker(_context(observations)) == expected
    assert (
        decide_greybridge_caretaker(_context(tuple(reversed(observations)))) == expected
    )


def test_caretaker_rejects_a_context_for_another_npc() -> None:
    with pytest.raises(
        ValueError, match="^caretaker policy requires bridge-caretaker$"
    ):
        decide_greybridge_caretaker(_context((), npc_id="injured-courier"))


def test_decision_context_is_strict_immutable_and_requires_matching_perception() -> (
    None
):
    context = _context(())

    with pytest.raises(ValidationError, match="Instance is frozen"):
        context.current_plan = "A replacement plan."
    with pytest.raises(ValidationError, match="at least 1 item"):
        NpcDecisionContext(
            decision_context_id=_DECISION_CONTEXT_ID,
            npc_id=_CARETAKER_ID,
            identity_summary="The caretaker.",
            goals=(),
            current_plan=None,
            perception=context.perception,
        )
    with pytest.raises(ValidationError, match="perception observer must match NPC"):
        NpcDecisionContext(
            decision_context_id=_DECISION_CONTEXT_ID,
            npc_id="injured-courier",
            identity_summary="The courier.",
            goals=(GoalDefinition(id="cross", description="Cross the bridge."),),
            current_plan=None,
            perception=context.perception,
        )
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        NpcDecisionContext.model_validate({**context.model_dump(), "world_state": {}})


def test_caretaker_is_repeatable_without_replacing_or_mutating_input() -> None:
    context = _context(
        (
            _location("greybridge-waystation"),
            _materials_at("greybridge-waystation"),
        )
    )
    before = context.model_dump()
    goals = context.goals
    perception = context.perception

    first = decide_greybridge_caretaker(context)
    second = decide_greybridge_caretaker(context)

    assert first == second
    assert context.model_dump() == before
    assert context.goals is goals
    assert context.perception is perception
