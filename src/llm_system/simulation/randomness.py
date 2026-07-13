from typing import Annotated, Protocol, Self
from uuid import UUID

from pydantic import StrictInt, StringConstraints, model_validator

from llm_system.simulation._types import _StrictContract

RandomDrawPurpose = Annotated[
    str,
    StringConstraints(strict=True, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
]


def _require_non_degenerate_range(lower_inclusive: int, upper_inclusive: int) -> None:
    if lower_inclusive >= upper_inclusive:
        raise ValueError("lower_inclusive must be less than upper_inclusive")


class IntegerDrawRequest(_StrictContract):
    draw_id: UUID
    purpose: RandomDrawPurpose
    lower_inclusive: StrictInt
    upper_inclusive: StrictInt

    @model_validator(mode="after")
    def require_non_degenerate_range(self) -> Self:
        _require_non_degenerate_range(self.lower_inclusive, self.upper_inclusive)
        return self


class IntegerDrawRecord(_StrictContract):
    draw_id: UUID
    purpose: RandomDrawPurpose
    lower_inclusive: StrictInt
    upper_inclusive: StrictInt
    result: StrictInt

    @model_validator(mode="after")
    def require_valid_range_and_result(self) -> Self:
        _require_non_degenerate_range(self.lower_inclusive, self.upper_inclusive)
        if not self.lower_inclusive <= self.result <= self.upper_inclusive:
            raise ValueError("result must be inside the inclusive bounds")
        return self


class IntegerRandomSource(Protocol):
    def draw_integer(self, *, lower_inclusive: int, upper_inclusive: int) -> int: ...


class RandomSourceContractError(RuntimeError):
    pass


def draw_recorded_integer(
    request: IntegerDrawRequest, source: IntegerRandomSource
) -> IntegerDrawRecord:
    result = source.draw_integer(
        lower_inclusive=request.lower_inclusive,
        upper_inclusive=request.upper_inclusive,
    )
    if (
        not isinstance(result, int)
        or isinstance(result, bool)
        or not request.lower_inclusive <= result <= request.upper_inclusive
    ):
        raise RandomSourceContractError(
            "integer random source returned an invalid result"
        )
    return IntegerDrawRecord(
        draw_id=request.draw_id,
        purpose=request.purpose,
        lower_inclusive=request.lower_inclusive,
        upper_inclusive=request.upper_inclusive,
        result=result,
    )
