from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx2
import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from llm_system.application import (
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    HttpLocalModelGateway,
    ModelMessage,
)


class CountOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    count: int


def test_functional_gateway_sends_exact_deterministic_request_and_accepts_output() -> (
    None
):
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return _provider_response('{"count":2}')

    gateway = _gateway(handler, base_url="http://model.test/")
    messages = (
        ModelMessage(role="user", content="Count the lanterns."),
        ModelMessage(role="assistant", content="I will return JSON."),
    )

    result = gateway.generate_functional(messages, CountOutput)

    schema = json.dumps(
        CountOutput.model_json_schema(), sort_keys=True, separators=(",", ":")
    )
    assert result == FunctionalGenerationResult[CountOutput](
        disposition=FunctionalGenerationDisposition.ACCEPTED,
        value=CountOutput(count=2),
        initial_attempt=FunctionalGenerationAttempt(
            content='{"count":2}', finish_reason="stop"
        ),
    )
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert str(requests[0].url) == "http://model.test/v1/chat/completions"
    assert requests[0].extensions["timeout"]["read"] == 7.5
    assert json.loads(requests[0].read()) == {
        "model": "gemma-local",
        "temperature": 0,
        "max_tokens": 321,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return only one JSON object that strictly conforms to this "
                    f"JSON Schema: {schema}"
                ),
            },
            {"role": "user", "content": "Count the lanterns."},
            {"role": "assistant", "content": "I will return JSON."},
        ],
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    assert messages == (
        ModelMessage(role="user", content="Count the lanterns."),
        ModelMessage(role="assistant", content="I will return JSON."),
    )


def test_invalid_output_gets_one_repair_with_same_context_and_can_succeed() -> None:
    requests: list[httpx2.Request] = []
    responses = iter(
        [_provider_response('{"count":"two"}'), _provider_response('{"count":2}')]
    )

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return next(responses)

    messages = (ModelMessage(role="user", content="Count them."),)
    result = _gateway(handler).generate_functional(messages, CountOutput)

    assert result.disposition is FunctionalGenerationDisposition.ACCEPTED
    assert result.value == CountOutput(count=2)
    assert (
        result.initial_attempt.failure_kind is FunctionalModelFailureKind.INVALID_OUTPUT
    )
    assert result.initial_attempt.validation_errors
    assert result.repair_attempt == FunctionalGenerationAttempt(
        content='{"count":2}', finish_reason="stop"
    )
    assert len(requests) == 2
    initial_body, repair_body = [json.loads(request.read()) for request in requests]
    assert repair_body.keys() == initial_body.keys()
    for setting in (
        "model",
        "temperature",
        "max_tokens",
        "response_format",
        "chat_template_kwargs",
    ):
        assert repair_body[setting] == initial_body[setting]
    assert repair_body["messages"][:-1] == initial_body["messages"]
    assert repair_body["messages"][-1] == {
        "role": "user",
        "content": (
            "Repair the failed output. Return only a complete replacement JSON "
            "object conforming to the same schema. Failed content: "
            '{"count":"two"}\nValidation errors:\n'
            + "\n".join(result.initial_attempt.validation_errors)
        ),
    }


@pytest.mark.parametrize(
    ("content", "finish_reason"),
    [
        (None, "stop"),
        ("   ", "stop"),
        ('{"count":2}', "length"),
        ("not-json", "stop"),
        ('{"count":"2"}', "stop"),
        ('{"count":2,"extra":3}', "stop"),
    ],
)
def test_each_invalid_output_kind_repairs_once_then_returns_ordered_failure(
    content: str | None, finish_reason: str
) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return _provider_response(content, finish_reason=finish_reason)

    result = _gateway(handler).generate_functional(
        (ModelMessage(role="user", content="Count."),), CountOutput
    )

    assert result.disposition is FunctionalGenerationDisposition.FAILED
    assert result.value is None
    assert result.initial_attempt.content == content
    assert (
        result.initial_attempt.failure_kind is FunctionalModelFailureKind.INVALID_OUTPUT
    )
    assert result.initial_attempt.validation_errors
    assert result.repair_attempt is not None
    assert (
        result.repair_attempt.failure_kind is FunctionalModelFailureKind.INVALID_OUTPUT
    )
    assert len(requests) == 2
    repair_instruction = json.loads(requests[1].read())["messages"][-1]["content"]
    assert ("<absent>" if content is None else content) in repair_instruction


def test_reasoning_content_is_ignored_when_content_is_absent() -> None:
    responses = iter(
        [
            _provider_response(None, reasoning_content='{"count":999}'),
            _provider_response('{"count":3}'),
        ]
    )
    result = _gateway(lambda request: next(responses)).generate_functional(
        (ModelMessage(role="user", content="Count."),), CountOutput
    )

    assert result.value == CountOutput(count=3)
    assert result.initial_attempt.content is None
    assert "999" not in " ".join(result.initial_attempt.validation_errors)


@pytest.mark.parametrize(
    ("response", "failure_kind"),
    [
        (
            httpx2.Response(503, text="private provider detail"),
            FunctionalModelFailureKind.SERVICE_ERROR,
        ),
        (
            httpx2.Response(200, text="not-json"),
            FunctionalModelFailureKind.MALFORMED_RESPONSE,
        ),
        (
            httpx2.Response(200, json={"choices": []}),
            FunctionalModelFailureKind.MALFORMED_RESPONSE,
        ),
        (
            httpx2.Response(
                200,
                json={"choices": [{"finish_reason": 7, "message": {}}]},
            ),
            FunctionalModelFailureKind.MALFORMED_RESPONSE,
        ),
    ],
)
def test_provider_failures_are_safe_and_never_repaired(
    response: httpx2.Response, failure_kind: FunctionalModelFailureKind
) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return response

    result = _gateway(handler).generate_functional(
        (ModelMessage(role="user", content="Count."),), CountOutput
    )

    assert result == FunctionalGenerationResult[CountOutput](
        disposition=FunctionalGenerationDisposition.FAILED,
        initial_attempt=FunctionalGenerationAttempt(failure_kind=failure_kind),
    )
    assert len(requests) == 1
    assert "private provider detail" not in repr(result)


def test_transport_failure_is_safe_and_never_repaired() -> None:
    requests: list[httpx2.Request] = []

    def unavailable(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        raise httpx2.ConnectError("secret exception detail", request=request)

    result = _gateway(unavailable).generate_functional(
        (ModelMessage(role="user", content="Count."),), CountOutput
    )

    assert result.initial_attempt == FunctionalGenerationAttempt(
        failure_kind=FunctionalModelFailureKind.TRANSPORT_UNAVAILABLE
    )
    assert result.repair_attempt is None
    assert len(requests) == 1
    assert "secret" not in repr(result)


def test_equal_calls_and_mock_responses_are_repeatable() -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return _provider_response('{"count":4}')

    gateway = _gateway(handler)
    messages = (ModelMessage(role="user", content="Count."),)

    first = gateway.generate_functional(messages, CountOutput)
    second = gateway.generate_functional(messages, CountOutput)

    assert first == second
    assert requests[0].read() == requests[1].read()
    assert CountOutput.model_json_schema() == CountOutput.model_json_schema()


def test_configuration_messages_and_result_evidence_are_strict_and_coherent() -> None:
    with pytest.raises((ValidationError, ValueError)):
        ModelMessage(role="user", content="   ")
    with pytest.raises(ValidationError):
        ModelMessage.model_validate({"role": "tool", "content": "x"})
    with pytest.raises(ValidationError):
        FunctionalGenerationAttempt(
            content='{"count":1}',
            finish_reason="stop",
            failure_kind=FunctionalModelFailureKind.INVALID_OUTPUT,
            validation_errors=(),
        )
    with pytest.raises(ValidationError):
        FunctionalGenerationResult[CountOutput](
            disposition=FunctionalGenerationDisposition.ACCEPTED,
            initial_attempt=FunctionalGenerationAttempt(
                failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
            ),
        )
    with pytest.raises(ValidationError):
        FunctionalGenerationResult[CountOutput](
            disposition=FunctionalGenerationDisposition.FAILED,
            value=CountOutput(count=1),
            initial_attempt=FunctionalGenerationAttempt(
                content='{"count":1}', finish_reason="stop"
            ),
        )

    for kwargs in (
        {"model": " "},
        {"timeout_seconds": 0},
        {"max_tokens": 0},
        {"max_tokens": True},
    ):
        with pytest.raises(ValueError):
            _configured_gateway(**kwargs)
    client = httpx2.Client(transport=httpx2.MockTransport(_unused_handler))
    with pytest.raises(ValueError):
        _configured_gateway(
            client=client, transport=httpx2.MockTransport(_unused_handler)
        )
    client.close()


def test_result_requires_repair_exactly_for_an_invalid_initial_output() -> None:
    invalid_attempt = FunctionalGenerationAttempt(
        content='{"count":"two"}',
        finish_reason="stop",
        failure_kind=FunctionalModelFailureKind.INVALID_OUTPUT,
        validation_errors=("count: int_type: Input should be a valid integer",),
    )
    service_attempt = FunctionalGenerationAttempt(
        failure_kind=FunctionalModelFailureKind.SERVICE_ERROR
    )

    with pytest.raises(ValidationError, match="requires exactly one repair"):
        FunctionalGenerationResult[CountOutput](
            disposition=FunctionalGenerationDisposition.FAILED,
            initial_attempt=invalid_attempt,
        )
    with pytest.raises(ValidationError, match="requires exactly one repair"):
        FunctionalGenerationResult[CountOutput](
            disposition=FunctionalGenerationDisposition.FAILED,
            initial_attempt=service_attempt,
            repair_attempt=service_attempt,
        )


def test_generate_requires_a_non_empty_tuple_and_pydantic_output_model() -> None:
    gateway = _gateway(_unused_handler)

    with pytest.raises(ValueError):
        gateway.generate_functional((), CountOutput)
    with pytest.raises(TypeError):
        gateway.generate_functional(
            [ModelMessage(role="user", content="Count.")],  # type: ignore[arg-type]
            CountOutput,
        )
    with pytest.raises(TypeError):
        gateway.generate_functional(  # type: ignore[type-var]
            (ModelMessage(role="user", content="Count."),), dict
        )


def test_gateway_closes_only_the_client_it_owns() -> None:
    transport = CloseTrackingTransport()
    owned_gateway = _configured_gateway(transport=transport)
    injected_client = httpx2.Client(transport=httpx2.MockTransport(_unused_handler))
    injected_gateway = _configured_gateway(client=injected_client)

    owned_gateway.close()
    injected_gateway.close()

    assert transport.closed
    assert not injected_client.is_closed
    injected_client.close()


class CloseTrackingTransport(httpx2.BaseTransport):
    def __init__(self) -> None:
        self.closed = False

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        return _provider_response('{"count":1}')

    def close(self) -> None:
        self.closed = True


def _gateway(
    handler: Callable[[httpx2.Request], httpx2.Response],
    *,
    base_url: str = "http://model.test",
) -> HttpLocalModelGateway:
    return _configured_gateway(
        base_url=base_url, transport=httpx2.MockTransport(handler)
    )


def _configured_gateway(**overrides: Any) -> HttpLocalModelGateway:
    kwargs: dict[str, Any] = {
        "base_url": "http://model.test",
        "model": "gemma-local",
        "timeout_seconds": 7.5,
        "max_tokens": 321,
    }
    kwargs.update(overrides)
    return HttpLocalModelGateway(**kwargs)


def _provider_response(
    content: str | None,
    *,
    finish_reason: str = "stop",
    reasoning_content: str | None = None,
) -> httpx2.Response:
    message: dict[str, object] = {"role": "assistant"}
    if content is not None:
        message["content"] = content
    if reasoning_content is not None:
        message["reasoning_content"] = reasoning_content
    return httpx2.Response(
        200,
        json={
            "choices": [
                {"finish_reason": finish_reason, "message": message, "index": 0}
            ],
            "provider_extra": "ignored",
        },
    )


def _unused_handler(request: httpx2.Request) -> httpx2.Response:
    raise AssertionError("request was not expected")
