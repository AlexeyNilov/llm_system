from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from llm_system.simulation._types import _StrictContract
from llm_system.simulation.changes import (
    CharacterLocationChanged,
    ConnectionAvailabilityChanged,
    ObjectPlacementChanged,
    SimulationTimeChanged,
    StateChange,
)
from llm_system.simulation.events import CanonicalEvent
from llm_system.simulation.state import NonNegativeSeconds

OutcomeReasonCode = Annotated[
    str,
    StringConstraints(strict=True, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
]


class _Outcome(_StrictContract):
    outcome_id: UUID
    proposal_id: UUID
    reason_code: OutcomeReasonCode
    resolved_at_seconds: NonNegativeSeconds


class RejectedOutcome(_Outcome):
    status: Literal["rejected"]


class _ValidAttemptOutcome(_Outcome):
    state_changes: tuple[StateChange, ...]
    events: tuple[CanonicalEvent, ...]

    @model_validator(mode="after")
    def require_consistent_effects(self) -> Self:
        _validate_events(self)
        _validate_change_conflicts(self.state_changes)
        return self


class FailedOutcome(_ValidAttemptOutcome):
    status: Literal["failed"]


class SucceededOutcome(_ValidAttemptOutcome):
    status: Literal["succeeded"]


Outcome = Annotated[
    RejectedOutcome | FailedOutcome | SucceededOutcome,
    Field(discriminator="status"),
]


def _validate_events(outcome: _ValidAttemptOutcome) -> None:
    event_ids: set[UUID] = set()
    for event in outcome.events:
        if event.outcome_id != outcome.outcome_id:
            raise ValueError("event outcome identity must match its containing outcome")
        if event.occurred_at_seconds != outcome.resolved_at_seconds:
            raise ValueError("event occurrence time must match outcome completion time")
        if event.event_id in event_ids:
            raise ValueError("event identities must be unique within an outcome")
        event_ids.add(event.event_id)


def _validate_change_conflicts(changes: tuple[StateChange, ...]) -> None:
    conflict_keys: set[tuple[str, str]] = set()
    for change in changes:
        key = _change_conflict_key(change)
        if key in conflict_keys:
            raise ValueError(
                "state-change conflict keys must be unique within an outcome"
            )
        conflict_keys.add(key)


def _change_conflict_key(change: StateChange) -> tuple[str, str]:
    if isinstance(change, CharacterLocationChanged):
        return ("character_location", change.character_id)
    if isinstance(change, ObjectPlacementChanged):
        return ("object_placement", change.object_id)
    if isinstance(change, ConnectionAvailabilityChanged):
        return ("connection_availability", change.connection_id)
    if isinstance(change, SimulationTimeChanged):
        return ("simulation_time", "singleton")
    raise AssertionError("unreachable closed state-change variant")
