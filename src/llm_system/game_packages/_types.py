from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints

RecordId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


def _validate_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("text must not be blank")
    return value


NonBlankText = Annotated[
    str,
    Field(min_length=1),
    AfterValidator(_validate_non_blank),
]
