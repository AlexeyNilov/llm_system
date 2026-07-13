from pathlib import Path

from fastapi import FastAPI

from llm_system.api import create_app
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
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    rule_package = load_game_package(RULE_PACKAGE_PATH)
    scenario_package = load_game_package(SCENARIO_PACKAGE_PATH)
    if not isinstance(rule_package, LoadedRulePackage):
        raise TypeError("configured rule package is not a rule package")
    if not isinstance(scenario_package, LoadedScenarioPackage):
        raise TypeError("configured scenario package is not a scenario package")
    return create_app(
        store=SQLiteStore.open(DATABASE_PATH),
        package_root=PACKAGE_ROOT,
        initial_packages=validate_game_packages(rule_package, scenario_package),
        development_reset_enabled=True,
    )
