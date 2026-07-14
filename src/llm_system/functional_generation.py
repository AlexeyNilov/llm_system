from enum import Enum
from typing import Generic, Literal, Protocol, Self, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

OutputT = TypeVar("OutputT", bound=BaseModel)


class FunctionalGenerationDisposition(str, Enum):
    ACCEPTED = "accepted"
    FAILED = "failed"


class FunctionalModelFailureKind(str, Enum):
    TRANSPORT_UNAVAILABLE = "transport-unavailable"
    SERVICE_ERROR = "service-error"
    MALFORMED_RESPONSE = "malformed-response"
    INVALID_OUTPUT = "invalid-output"


class ModelMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    role: Literal["system", "user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be blank")
        return value


class FunctionalGenerationAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    content: str | None = None
    finish_reason: str | None = None
    failure_kind: FunctionalModelFailureKind | None = None
    validation_errors: tuple[str, ...] = ()

    @field_validator("validation_errors")
    @classmethod
    def reject_blank_validation_errors(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            raise ValueError("validation errors must not be blank")
        return values

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        if self.failure_kind is None:
            if (
                self.finish_reason != "stop"
                or self.content is None
                or not self.content.strip()
                or self.validation_errors
            ):
                raise ValueError(
                    "a successful attempt requires stopped non-blank content"
                )
            return self
        if self.failure_kind is FunctionalModelFailureKind.INVALID_OUTPUT:
            if not self.validation_errors:
                raise ValueError("invalid output requires validation errors")
            return self
        if (
            self.content is not None
            or self.finish_reason is not None
            or self.validation_errors
        ):
            raise ValueError("provider failures cannot expose candidate evidence")
        return self


class FunctionalGenerationResult(BaseModel, Generic[OutputT]):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    disposition: FunctionalGenerationDisposition
    value: OutputT | None = None
    initial_attempt: FunctionalGenerationAttempt
    repair_attempt: FunctionalGenerationAttempt | None = None

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        final_attempt = self.repair_attempt or self.initial_attempt
        invalid_initial = (
            self.initial_attempt.failure_kind
            is FunctionalModelFailureKind.INVALID_OUTPUT
        )
        if invalid_initial != (self.repair_attempt is not None):
            raise ValueError("invalid initial output requires exactly one repair")
        if self.disposition is FunctionalGenerationDisposition.ACCEPTED:
            if self.value is None or final_attempt.failure_kind is not None:
                raise ValueError(
                    "accepted results require a value and successful final attempt"
                )
            return self
        if self.value is not None or final_attempt.failure_kind is None:
            raise ValueError(
                "failed results require no value and a failed final attempt"
            )
        return self


class FunctionalModelGateway(Protocol):
    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]: ...
