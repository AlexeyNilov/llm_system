from __future__ import annotations

import json
from typing import TypeVar

import httpx2
from pydantic import BaseModel, ValidationError

from llm_system.functional_generation import (
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    FunctionalModelGateway,
    ModelMessage,
)

OutputT = TypeVar("OutputT", bound=BaseModel)

__all__ = [
    "FunctionalGenerationAttempt",
    "FunctionalGenerationDisposition",
    "FunctionalGenerationResult",
    "FunctionalModelFailureKind",
    "FunctionalModelGateway",
    "HttpLocalModelGateway",
    "ModelMessage",
]


class HttpLocalModelGateway:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
        client: httpx2.Client | None = None,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        if client is not None and transport is not None:
            raise ValueError("client and transport cannot both be provided")
        if not base_url.strip():
            raise ValueError("base_url must not be blank")
        if not model.strip():
            raise ValueError("model must not be blank")
        if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if (
            isinstance(max_tokens, bool)
            or not isinstance(max_tokens, int)
            or max_tokens <= 0
        ):
            raise ValueError("max_tokens must be a positive integer")

        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens
        self._owns_client = client is None
        self._client = (
            client if client is not None else httpx2.Client(transport=transport)
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def generate_functional[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> FunctionalGenerationResult[ResultT]:
        if not isinstance(messages, tuple):
            raise TypeError("messages must be an immutable tuple")
        if not messages:
            raise ValueError("messages must not be empty")
        if not all(isinstance(message, ModelMessage) for message in messages):
            raise TypeError("every message must be a ModelMessage")
        if not isinstance(output_model, type) or not issubclass(
            output_model, BaseModel
        ):
            raise TypeError("output_model must be a Pydantic BaseModel class")

        schema_instruction = _schema_instruction(output_model)
        request_messages = (
            ModelMessage(role="system", content=schema_instruction),
            *messages,
        )
        initial_attempt, value = self._request_attempt(request_messages, output_model)
        if value is not None:
            return FunctionalGenerationResult[ResultT](
                disposition=FunctionalGenerationDisposition.ACCEPTED,
                value=value,
                initial_attempt=initial_attempt,
            )
        if (
            initial_attempt.failure_kind
            is not FunctionalModelFailureKind.INVALID_OUTPUT
        ):
            return FunctionalGenerationResult[ResultT](
                disposition=FunctionalGenerationDisposition.FAILED,
                initial_attempt=initial_attempt,
            )

        repair_messages = (
            *request_messages,
            ModelMessage(role="user", content=_repair_instruction(initial_attempt)),
        )
        repair_attempt, repaired_value = self._request_attempt(
            repair_messages, output_model
        )
        if repaired_value is not None:
            return FunctionalGenerationResult[ResultT](
                disposition=FunctionalGenerationDisposition.ACCEPTED,
                value=repaired_value,
                initial_attempt=initial_attempt,
                repair_attempt=repair_attempt,
            )
        return FunctionalGenerationResult[ResultT](
            disposition=FunctionalGenerationDisposition.FAILED,
            initial_attempt=initial_attempt,
            repair_attempt=repair_attempt,
        )

    def _request_attempt[ResultT: BaseModel](
        self,
        messages: tuple[ModelMessage, ...],
        output_model: type[ResultT],
    ) -> tuple[FunctionalGenerationAttempt, ResultT | None]:
        try:
            response = self._client.post(
                f"{self._base_url}/v1/chat/completions",
                timeout=self._timeout_seconds,
                json={
                    "model": self._model,
                    "temperature": 0,
                    "max_tokens": self._max_tokens,
                    "messages": [
                        message.model_dump(mode="json") for message in messages
                    ],
                    "response_format": {"type": "json_object"},
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
        except httpx2.RequestError:
            return (
                FunctionalGenerationAttempt(
                    failure_kind=FunctionalModelFailureKind.TRANSPORT_UNAVAILABLE
                ),
                None,
            )

        if response.status_code != 200:
            return (
                FunctionalGenerationAttempt(
                    failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
                ),
                None,
            )

        provider_fields = _provider_fields(response)
        if provider_fields is None:
            return (
                FunctionalGenerationAttempt(
                    failure_kind=FunctionalModelFailureKind.MALFORMED_RESPONSE
                ),
                None,
            )
        content, finish_reason = provider_fields
        validation_errors = _candidate_errors(content, finish_reason)
        if validation_errors:
            return (
                FunctionalGenerationAttempt(
                    content=content,
                    finish_reason=finish_reason,
                    failure_kind=FunctionalModelFailureKind.INVALID_OUTPUT,
                    validation_errors=validation_errors,
                ),
                None,
            )

        assert content is not None
        try:
            value = output_model.model_validate_json(content, strict=True)
        except (ValidationError, ValueError) as error:
            return (
                FunctionalGenerationAttempt(
                    content=content,
                    finish_reason=finish_reason,
                    failure_kind=FunctionalModelFailureKind.INVALID_OUTPUT,
                    validation_errors=_normalize_validation_error(error),
                ),
                None,
            )
        return FunctionalGenerationAttempt(
            content=content, finish_reason=finish_reason
        ), value


def _schema_instruction(output_model: type[BaseModel]) -> str:
    compact_schema = json.dumps(
        output_model.model_json_schema(), sort_keys=True, separators=(",", ":")
    )
    return (
        "Return only one JSON object that strictly conforms to this JSON Schema: "
        f"{compact_schema}"
    )


def _repair_instruction(attempt: FunctionalGenerationAttempt) -> str:
    failed_content = "<absent>" if attempt.content is None else attempt.content
    return (
        "Repair the failed output. Return only a complete replacement JSON object "
        "conforming to the same schema. Failed content: "
        f"{failed_content}\nValidation errors:\n" + "\n".join(attempt.validation_errors)
    )


def _provider_fields(response: httpx2.Response) -> tuple[str | None, str] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    choices = body.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        return None
    choice = choices[0]
    if not isinstance(choice, dict):
        return None
    finish_reason = choice.get("finish_reason")
    message = choice.get("message")
    if not isinstance(finish_reason, str) or not isinstance(message, dict):
        return None
    content = message.get("content")
    if content is not None and not isinstance(content, str):
        return None
    return content, finish_reason


def _candidate_errors(content: str | None, finish_reason: str) -> tuple[str, ...]:
    errors: list[str] = []
    if finish_reason != "stop":
        errors.append(f"finish_reason: expected 'stop', got {finish_reason!r}")
    if content is None:
        errors.append("content: missing")
    elif not content.strip():
        errors.append("content: blank")
    return tuple(errors)


def _normalize_validation_error(error: ValidationError | ValueError) -> tuple[str, ...]:
    if isinstance(error, ValidationError):
        normalized: list[str] = []
        for detail in error.errors(
            include_url=False, include_context=False, include_input=False
        ):
            location = ".".join(str(part) for part in detail["loc"]) or "$"
            normalized.append(f"{location}: {detail['type']}: {detail['msg']}")
        return tuple(normalized) or ("$: invalid output",)
    return (f"$: invalid_json: {error}",)
