import json
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from llm_system.simulation import (
    ActorWaitedEvent,
    CharacterLocationChanged,
    ConnectionAvailabilityChanged,
    FailedOutcome,
    ObjectAtLocation,
    ObjectPlacementChanged,
    ObjectPossessedByCharacter,
    Outcome,
    RejectedOutcome,
    SimulationTimeChanged,
    SucceededOutcome,
)

OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")


def _base(status: str) -> dict[str, object]:
    return {
        "status": status,
        "outcome_id": str(OUTCOME_ID),
        "proposal_id": str(PROPOSAL_ID),
        "reason_code": "action-resolved",
        "resolved_at_seconds": 30,
    }


def _wait_event(**overrides: object) -> dict[str, object]:
    return {
        "event_type": "actor_waited",
        "event_id": str(EVENT_ID),
        "outcome_id": str(OUTCOME_ID),
        "occurred_at_seconds": 30,
        "actor_id": "marin",
        "duration_seconds": 30,
    } | overrides


def _valid_attempt(status: str) -> dict[str, object]:
    return _base(status) | {
        "state_changes": [
            {"change_type": "simulation_time", "from_seconds": 0, "to_seconds": 30}
        ],
        "events": [_wait_event()],
    }


def test_outcome_discriminates_all_variants_and_strict_json_round_trips() -> None:
    adapter: TypeAdapter[Outcome] = TypeAdapter(Outcome)
    payloads = (
        _base("rejected"),
        _valid_attempt("failed"),
        _valid_attempt("succeeded"),
    )

    outcomes = tuple(adapter.validate_json(json.dumps(payload)) for payload in payloads)

    assert tuple(type(outcome) for outcome in outcomes) == (
        RejectedOutcome,
        FailedOutcome,
        SucceededOutcome,
    )
    assert outcomes[0].outcome_id == OUTCOME_ID
    failed = outcomes[1]
    assert isinstance(failed, FailedOutcome)
    assert isinstance(failed.state_changes, tuple)
    assert isinstance(failed.events, tuple)
    assert isinstance(failed.events[0], ActorWaitedEvent)
    for outcome, payload in zip(outcomes, payloads, strict=True):
        assert adapter.dump_python(outcome, mode="json") == payload


def test_rejection_omits_effects_and_valid_attempts_require_explicit_tuples() -> None:
    rejected = RejectedOutcome.model_validate(
        _base("rejected") | {"outcome_id": OUTCOME_ID, "proposal_id": PROPOSAL_ID}
    )

    assert set(type(rejected).model_fields) == {
        "status",
        "outcome_id",
        "proposal_id",
        "reason_code",
        "resolved_at_seconds",
    }
    for effect in ("state_changes", "events"):
        with pytest.raises(ValidationError):
            RejectedOutcome.model_validate(rejected.model_dump() | {effect: ()})
        with pytest.raises(ValidationError):
            FailedOutcome.model_validate(
                {
                    **_valid_attempt("failed"),
                    "outcome_id": OUTCOME_ID,
                    "proposal_id": PROPOSAL_ID,
                    effect: None,
                }
            )
    for model, status in ((FailedOutcome, "failed"), (SucceededOutcome, "succeeded")):
        payload = _base(status) | {
            "outcome_id": OUTCOME_ID,
            "proposal_id": PROPOSAL_ID,
            "state_changes": (),
            "events": (),
        }
        outcome = model.model_validate(payload)
        assert outcome.state_changes == ()
        assert outcome.events == ()
        for missing in ("state_changes", "events"):
            with pytest.raises(ValidationError):
                model.model_validate(
                    {key: value for key, value in payload.items() if key != missing}
                )


def test_identity_time_reason_status_and_immutability_are_strict() -> None:
    valid = _base("rejected") | {"outcome_id": OUTCOME_ID, "proposal_id": PROPOSAL_ID}
    malformed = (
        "",
        "UPPERCASE",
        "under_score",
        "two words",
        "-leading",
        "trailing-",
        "two--parts",
    )
    invalid = (
        {key: value for key, value in valid.items() if key != "outcome_id"},
        valid | {"outcome_id": "not-a-uuid"},
        valid | {"proposal_id": "not-a-uuid"},
        valid | {"resolved_at_seconds": True},
        valid | {"resolved_at_seconds": -1},
        valid | {"status": "failed"},
        valid | {"explanation": "done"},
        *(valid | {"reason_code": reason} for reason in malformed),
    )
    for payload in invalid:
        with pytest.raises(ValidationError):
            RejectedOutcome.model_validate(payload)

    outcome = RejectedOutcome.model_validate(
        valid | {"reason_code": "resolver-specific-42"}
    )
    with pytest.raises(ValidationError):
        outcome.reason_code = "changed"
    with pytest.raises(ValidationError):
        TypeAdapter(Outcome).validate_python(valid | {"status": "cancelled"})


def test_nested_events_require_matching_cause_time_and_unique_identity() -> None:
    for event in (
        _wait_event(outcome_id=str(PROPOSAL_ID)),
        _wait_event(occurred_at_seconds=29),
    ):
        with pytest.raises(ValidationError):
            TypeAdapter(Outcome).validate_json(
                json.dumps(_base("failed") | {"state_changes": [], "events": [event]})
            )
    with pytest.raises(ValidationError):
        TypeAdapter(Outcome).validate_json(
            json.dumps(
                _base("succeeded")
                | {"state_changes": [], "events": [_wait_event(), _wait_event()]}
            )
        )


def test_duplicate_change_conflict_keys_are_rejected() -> None:
    duplicate_pairs = (
        (
            CharacterLocationChanged(
                change_type="character_location",
                character_id="marin",
                from_location_id="market",
                to_location_id="dock",
            ),
            CharacterLocationChanged(
                change_type="character_location",
                character_id="marin",
                from_location_id="dock",
                to_location_id="tower",
            ),
        ),
        (
            ObjectPlacementChanged(
                change_type="object_placement",
                object_id="medicine-kit",
                from_placement=ObjectAtLocation(
                    placement_type="location", location_id="market"
                ),
                to_placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
            ObjectPlacementChanged(
                change_type="object_placement",
                object_id="medicine-kit",
                from_placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
                to_placement=ObjectAtLocation(
                    placement_type="location", location_id="dock"
                ),
            ),
        ),
        (
            ConnectionAvailabilityChanged(
                change_type="connection_availability",
                connection_id="market-to-dock",
                from_available=True,
                to_available=False,
            ),
            ConnectionAvailabilityChanged(
                change_type="connection_availability",
                connection_id="market-to-dock",
                from_available=False,
                to_available=True,
            ),
        ),
        (
            SimulationTimeChanged(
                change_type="simulation_time", from_seconds=0, to_seconds=10
            ),
            SimulationTimeChanged(
                change_type="simulation_time", from_seconds=10, to_seconds=30
            ),
        ),
    )
    for changes in duplicate_pairs:
        with pytest.raises(ValidationError):
            FailedOutcome(
                status="failed",
                outcome_id=OUTCOME_ID,
                proposal_id=PROPOSAL_ID,
                reason_code="attempt-failed",
                resolved_at_seconds=30,
                state_changes=changes,
                events=(),
            )


def test_independent_changes_are_allowed_without_state_dependent_checks() -> None:
    changes = (
        CharacterLocationChanged(
            change_type="character_location",
            character_id="marin",
            from_location_id="unknown-place",
            to_location_id="dock",
        ),
        CharacterLocationChanged(
            change_type="character_location",
            character_id="sela",
            from_location_id="market",
            to_location_id="dock",
        ),
        ConnectionAvailabilityChanged(
            change_type="connection_availability",
            connection_id="market-to-dock",
            from_available=True,
            to_available=False,
        ),
        SimulationTimeChanged(
            change_type="simulation_time", from_seconds=7, to_seconds=8
        ),
    )

    outcome = SucceededOutcome(
        status="succeeded",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="action-succeeded",
        resolved_at_seconds=99,
        state_changes=changes,
        events=(),
    )

    assert outcome.state_changes == changes
