from collections.abc import Sequence
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.simulation import (
    IntegerDrawRecord,
    IntegerDrawRequest,
    IntegerRandomSource,
    RandomDrawPurpose,
    RandomSourceContractError,
    draw_recorded_integer,
)

DRAW_ID = UUID("12345678-1234-5678-1234-567812345678")


class ScriptedIntegerSource:
    def __init__(self, results: Sequence[object]) -> None:
        self.results = results
        self.calls: list[tuple[int, int]] = []
        self.label = "unchanged"

    def draw_integer(self, *, lower_inclusive: int, upper_inclusive: int) -> int:
        self.calls.append((lower_inclusive, upper_inclusive))
        return cast(int, self.results[len(self.calls) - 1])


class RaisingIntegerSource:
    def __init__(self, error: RuntimeError) -> None:
        self.error = error
        self.calls = 0

    def draw_integer(self, *, lower_inclusive: int, upper_inclusive: int) -> int:
        self.calls += 1
        raise self.error


def _request() -> IntegerDrawRequest:
    purpose: RandomDrawPurpose = "fieldcraft-check"
    return IntegerDrawRequest(
        draw_id=DRAW_ID,
        purpose=purpose,
        lower_inclusive=-2,
        upper_inclusive=2,
    )


def test_draw_contracts_are_exact_strict_immutable_and_self_validating() -> None:
    request_fields = (
        "draw_id",
        "purpose",
        "lower_inclusive",
        "upper_inclusive",
    )
    assert tuple(IntegerDrawRequest.model_fields) == request_fields
    assert tuple(IntegerDrawRecord.model_fields) == request_fields + ("result",)

    request_payload = {
        "draw_id": DRAW_ID,
        "purpose": "fieldcraft-check",
        "lower_inclusive": -2,
        "upper_inclusive": 2,
    }
    malformed_purposes = (
        "",
        "UPPERCASE",
        "under_score",
        "two words",
        "-leading",
        "trailing-",
        "two--parts",
    )
    invalid_requests = (
        request_payload | {"extra": "forbidden"},
        request_payload | {"draw_id": str(DRAW_ID)},
        request_payload | {"lower_inclusive": True},
        request_payload | {"lower_inclusive": -2.0},
        request_payload | {"lower_inclusive": "-2"},
        request_payload | {"lower_inclusive": 2},
        request_payload | {"lower_inclusive": 3},
        *(request_payload | {"purpose": purpose} for purpose in malformed_purposes),
    )
    for payload in invalid_requests:
        with pytest.raises(ValidationError):
            IntegerDrawRequest.model_validate(payload)

    request = IntegerDrawRequest.model_validate(request_payload)
    with pytest.raises(ValidationError):
        request.purpose = "changed"

    record = IntegerDrawRecord.model_validate(request_payload | {"result": -2})
    with pytest.raises(ValidationError):
        record.result = 0

    for payload in (
        request_payload | {"result": True},
        request_payload | {"result": -2.0},
        request_payload | {"result": "-2"},
        request_payload | {"result": -3},
        request_payload | {"result": 3},
        request_payload | {"lower_inclusive": 2, "result": 2},
        request_payload | {"lower_inclusive": 3, "result": 3},
    ):
        with pytest.raises(ValidationError):
            IntegerDrawRecord.model_validate(payload)


@pytest.mark.parametrize("result", [-2, 2])
def test_draw_calls_source_once_and_preserves_exact_signed_boundary_result(
    result: int,
) -> None:
    request = _request()
    source = ScriptedIntegerSource([result])
    typed_source: IntegerRandomSource = source

    record = draw_recorded_integer(request, typed_source)

    assert record == IntegerDrawRecord(
        draw_id=DRAW_ID,
        purpose="fieldcraft-check",
        lower_inclusive=-2,
        upper_inclusive=2,
        result=result,
    )
    assert source.calls == [(-2, 2)]
    assert request == _request()
    assert source.label == "unchanged"


@pytest.mark.parametrize("result", [True, False, 1.0, "1", None, -3, 3])
def test_draw_rejects_invalid_source_result_without_coercion_or_retry(
    result: object,
) -> None:
    source = ScriptedIntegerSource([result, 0])

    with pytest.raises(RandomSourceContractError) as raised:
        draw_recorded_integer(_request(), source)

    assert str(raised.value) == "integer random source returned an invalid result"
    assert source.calls == [(-2, 2)]


def test_draw_propagates_exact_source_exception_without_retry() -> None:
    error = RuntimeError("source unavailable")
    source = RaisingIntegerSource(error)

    with pytest.raises(RuntimeError) as raised:
        draw_recorded_integer(_request(), source)

    assert raised.value is error
    assert source.calls == 1


def test_equivalent_draws_produce_equal_records_without_mutating_inputs() -> None:
    first_request = _request()
    second_request = _request()
    first_source = ScriptedIntegerSource([1])
    second_source = ScriptedIntegerSource([1])

    first_record = draw_recorded_integer(first_request, first_source)
    second_record = draw_recorded_integer(second_request, second_source)

    assert first_record == second_record
    assert first_request == second_request == _request()
    assert first_source.results == second_source.results == [1]
    assert first_source.label == second_source.label == "unchanged"
