from typing import Any

import pytest

from llm_system import server
from llm_system.persistence import SQLiteStore


@pytest.fixture(autouse=True)
def runtime_dependencies(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(server, "LoadedRulePackage", object)
    monkeypatch.setattr(server, "LoadedScenarioPackage", object)
    monkeypatch.setattr(server, "load_game_package", lambda path: object())
    monkeypatch.setattr(
        server,
        "validate_game_packages",
        lambda rule_package, scenario_package: object(),
    )
    monkeypatch.setattr(
        SQLiteStore,
        "open",
        staticmethod(lambda database_path: object()),
    )

    def fake_create_app(**kwargs: Any) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(server, "create_app", fake_create_app)
    return captured


def test_absent_gateway_configuration_preserves_safe_create_app_fallback(
    monkeypatch: pytest.MonkeyPatch, runtime_dependencies: dict[str, Any]
) -> None:
    _clear_gateway_environment(monkeypatch)

    server.create_runtime_app()

    assert "gateway" not in runtime_dependencies


def test_complete_gateway_configuration_constructs_and_injects_gateway(
    monkeypatch: pytest.MonkeyPatch, runtime_dependencies: dict[str, Any]
) -> None:
    _set_gateway_environment(
        monkeypatch,
        base_url="http://127.0.0.1:1234",
        model="local-gemma",
        timeout_seconds="12.5",
        max_tokens="768",
    )
    captured: dict[str, Any] = {}

    class FakeGateway:
        def __init__(
            self,
            *,
            base_url: str,
            model: str,
            timeout_seconds: float,
            max_tokens: int,
        ) -> None:
            captured.update(
                base_url=base_url,
                model=model,
                timeout_seconds=timeout_seconds,
                max_tokens=max_tokens,
            )

    monkeypatch.setattr(server, "HttpLocalModelGateway", FakeGateway)

    server.create_runtime_app()

    assert captured == {
        "base_url": "http://127.0.0.1:1234",
        "model": "local-gemma",
        "timeout_seconds": 12.5,
        "max_tokens": 768,
    }
    assert isinstance(runtime_dependencies["gateway"], FakeGateway)


@pytest.mark.parametrize(
    "environment",
    [
        {"LLM_SYSTEM_MODEL_BASE_URL": "http://127.0.0.1:1234"},
        {
            "LLM_SYSTEM_MODEL_BASE_URL": "http://127.0.0.1:1234",
            "LLM_SYSTEM_MODEL": "local-gemma",
            "LLM_SYSTEM_MODEL_TIMEOUT_SECONDS": "12",
        },
    ],
)
def test_partial_gateway_configuration_fails_before_app_creation(
    monkeypatch: pytest.MonkeyPatch,
    runtime_dependencies: dict[str, Any],
    environment: dict[str, str],
) -> None:
    _clear_gateway_environment(monkeypatch)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="all be configured"):
        server.create_runtime_app()

    assert runtime_dependencies == {}


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("LLM_SYSTEM_MODEL_BASE_URL", "   "),
        ("LLM_SYSTEM_MODEL", ""),
        ("LLM_SYSTEM_MODEL_TIMEOUT_SECONDS", "0"),
        ("LLM_SYSTEM_MODEL_TIMEOUT_SECONDS", "not-a-number"),
        ("LLM_SYSTEM_MODEL_MAX_TOKENS", "0"),
        ("LLM_SYSTEM_MODEL_MAX_TOKENS", "12.5"),
    ],
)
def test_invalid_gateway_configuration_fails_before_app_creation(
    monkeypatch: pytest.MonkeyPatch,
    runtime_dependencies: dict[str, Any],
    name: str,
    value: str,
) -> None:
    _set_gateway_environment(
        monkeypatch,
        base_url="http://127.0.0.1:1234",
        model="local-gemma",
        timeout_seconds="12",
        max_tokens="768",
    )
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError):
        server.create_runtime_app()

    assert runtime_dependencies == {}


def _clear_gateway_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _gateway_environment_names():
        monkeypatch.delenv(name, raising=False)


def _set_gateway_environment(
    monkeypatch: pytest.MonkeyPatch,
    *,
    base_url: str,
    model: str,
    timeout_seconds: str,
    max_tokens: str,
) -> None:
    values = (base_url, model, timeout_seconds, max_tokens)
    for name, value in zip(_gateway_environment_names(), values, strict=True):
        monkeypatch.setenv(name, value)


def _gateway_environment_names() -> tuple[str, str, str, str]:
    return (
        "LLM_SYSTEM_MODEL_BASE_URL",
        "LLM_SYSTEM_MODEL",
        "LLM_SYSTEM_MODEL_TIMEOUT_SECONDS",
        "LLM_SYSTEM_MODEL_MAX_TOKENS",
    )
