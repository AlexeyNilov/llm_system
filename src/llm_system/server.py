import math
import os
from pathlib import Path

from fastapi import FastAPI

from llm_system.api import create_app
from llm_system.application import HttpLocalModelGateway
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.persistence import SQLiteStore

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "game_packages"
DATABASE_PATH = REPOSITORY_ROOT / ".run" / "world.sqlite3"
RULE_PACKAGE_PATH = PACKAGE_ROOT / "rules/greybridge-rules/0.2.0"
SCENARIO_PACKAGE_PATH = PACKAGE_ROOT / "scenarios/storm-at-greybridge/0.2.0"


def create_runtime_app() -> FastAPI:
    gateway = _configured_gateway()
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    rule_package = load_game_package(RULE_PACKAGE_PATH)
    scenario_package = load_game_package(SCENARIO_PACKAGE_PATH)
    if not isinstance(rule_package, LoadedRulePackage):
        raise TypeError("configured rule package is not a rule package")
    if not isinstance(scenario_package, LoadedScenarioPackage):
        raise TypeError("configured scenario package is not a scenario package")
    store = SQLiteStore.open(DATABASE_PATH)
    packages = validate_game_packages(rule_package, scenario_package)
    if gateway is None:
        return create_app(
            store=store,
            package_root=PACKAGE_ROOT,
            initial_packages=packages,
            development_reset_enabled=True,
        )
    return create_app(
        store=store,
        package_root=PACKAGE_ROOT,
        initial_packages=packages,
        development_reset_enabled=True,
        gateway=gateway,
    )


def _configured_gateway() -> HttpLocalModelGateway | None:
    base_url = os.getenv("LLM_SYSTEM_MODEL_BASE_URL")
    model = os.getenv("LLM_SYSTEM_MODEL")
    timeout_seconds = os.getenv("LLM_SYSTEM_MODEL_TIMEOUT_SECONDS")
    max_tokens = os.getenv("LLM_SYSTEM_MODEL_MAX_TOKENS")
    settings = (base_url, model, timeout_seconds, max_tokens)
    if all(setting is None for setting in settings):
        return None
    if any(setting is None for setting in settings):
        raise ValueError("local gateway settings must all be configured")
    assert (
        base_url is not None
        and model is not None
        and timeout_seconds is not None
        and max_tokens is not None
    )
    if not base_url.strip():
        raise ValueError("local gateway base URL must not be blank")
    if not model.strip():
        raise ValueError("local gateway model must not be blank")
    return HttpLocalModelGateway(
        base_url=base_url,
        model=model,
        timeout_seconds=_positive_timeout_seconds(timeout_seconds),
        max_tokens=_positive_max_tokens(max_tokens),
    )


def _positive_timeout_seconds(value: str) -> float:
    try:
        timeout_seconds = float(value)
    except ValueError as error:
        raise ValueError(
            "local gateway timeout seconds must be a positive number"
        ) from error
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("local gateway timeout seconds must be a positive number")
    return timeout_seconds


def _positive_max_tokens(value: str) -> int:
    try:
        max_tokens = int(value)
    except ValueError as error:
        raise ValueError(
            "local gateway maximum tokens must be a positive integer"
        ) from error
    if max_tokens <= 0:
        raise ValueError("local gateway maximum tokens must be a positive integer")
    return max_tokens
