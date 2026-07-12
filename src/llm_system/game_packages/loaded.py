from typing import TypeAlias

from pydantic import BaseModel, ConfigDict

from llm_system.game_packages.models import RulePackageManifest, ScenarioPackageManifest
from llm_system.game_packages.rules import RulePackDefinition
from llm_system.game_packages.scenarios import ScenarioPackDefinition


class LoadedRulePackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    manifest: RulePackageManifest
    definition: RulePackDefinition


class LoadedScenarioPackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    manifest: ScenarioPackageManifest
    definition: ScenarioPackDefinition


LoadedGamePackage: TypeAlias = LoadedRulePackage | LoadedScenarioPackage
