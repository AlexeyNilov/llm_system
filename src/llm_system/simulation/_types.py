from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

AuthoredId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


class _StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
