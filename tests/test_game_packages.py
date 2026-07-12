from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from llm_system.game_packages import (
    GamePackageLoadError,
    LoadedRulePackage,
    LoadedScenarioPackage,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    load_game_package,
)

_RULE_CONTENT = """\
schema_version: 1
object_archetypes: []
character_archetypes: []
decision_policies: []
"""
_SCENARIO_CONTENT = """\
schema_version: 1
spatial_graph:
  locations: []
  connections: []
entity_collection:
  entities: []
"""


def _write_package(
    tmp_path: Path,
    directory_type: str,
    package_id: str,
    package_version: str,
    manifest: str,
    content: str = _RULE_CONTENT,
) -> Path:
    package_directory = (
        tmp_path / "game_packages" / directory_type / package_id / package_version
    )
    package_directory.mkdir(parents=True)
    (package_directory / "content.yaml").write_text(content, encoding="utf-8")
    (package_directory / "manifest.yaml").write_text(manifest, encoding="utf-8")
    return package_directory


def _rule_manifest(entrypoint: str = "content.yaml") -> str:
    return f"""\
schema_version: 1
package_id: forest-rules
package_version: 1.2.3
package_type: rule
title: Forest Rules
entrypoint: {entrypoint}
"""


def _scenario_manifest(entrypoint: str = "content.yaml") -> str:
    return f"""\
schema_version: 1
package_id: lost-woods
package_version: 2.0.1
package_type: scenario
title: Lost Woods
entrypoint: {entrypoint}
required_rule_pack:
  package_id: forest-rules
  package_version: 1.2.3
"""


def test_load_game_package_returns_frozen_rule_manifest_definition_pair(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path, "rules", "forest-rules", "1.2.3", _rule_manifest()
    )

    loaded_package = load_game_package(package_directory)

    assert isinstance(loaded_package, LoadedRulePackage)
    assert isinstance(loaded_package.manifest, RulePackageManifest)
    assert loaded_package.manifest.package_id == "forest-rules"
    assert loaded_package.definition.schema_version == 1
    with pytest.raises(ValidationError):
        loaded_package.definition = RulePackDefinition(
            schema_version=1,
            object_archetypes=(),
            character_archetypes=(),
            decision_policies=(),
        )
    with pytest.raises(ValidationError):
        loaded_package.manifest.title = "Changed"
    with pytest.raises(ValidationError):
        loaded_package.definition.object_archetypes = ()


def test_load_game_package_returns_scenario_pair_without_resolving_dependency(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path,
        "scenarios",
        "lost-woods",
        "2.0.1",
        _scenario_manifest(),
        _SCENARIO_CONTENT,
    )

    loaded_package = load_game_package(package_directory)

    assert isinstance(loaded_package, LoadedScenarioPackage)
    assert isinstance(loaded_package.manifest, ScenarioPackageManifest)
    assert loaded_package.manifest.required_rule_pack.package_id == "forest-rules"
    assert loaded_package.definition.entity_collection.entities == ()


def test_loaded_package_wrappers_reject_mismatched_or_unknown_fields() -> None:
    rule_manifest = RulePackageManifest.model_validate(yaml.safe_load(_rule_manifest()))
    scenario_manifest = ScenarioPackageManifest.model_validate(
        yaml.safe_load(_scenario_manifest())
    )
    rule_definition = RulePackDefinition.model_validate(yaml.safe_load(_RULE_CONTENT))
    scenario_definition = ScenarioPackDefinition.model_validate(
        yaml.safe_load(_SCENARIO_CONTENT)
    )

    with pytest.raises(ValidationError):
        LoadedRulePackage.model_validate(
            {"manifest": scenario_manifest, "definition": rule_definition}
        )
    with pytest.raises(ValidationError):
        LoadedScenarioPackage.model_validate(
            {"manifest": rule_manifest, "definition": scenario_definition}
        )
    with pytest.raises(ValidationError):
        LoadedRulePackage.model_validate(
            {"manifest": rule_manifest, "definition": rule_definition, "extra": True}
        )


@pytest.mark.parametrize(
    ("directory_type", "package_id", "package_version", "manifest"),
    [
        ("rules", "forest-rules", "1.2.3", _rule_manifest("content.json")),
        ("scenarios", "forest-rules", "1.2.3", _rule_manifest()),
        ("rules", "other-rules", "1.2.3", _rule_manifest()),
        ("rules", "forest-rules", "1.2.4", _rule_manifest()),
        (
            "rules",
            "forest-rules",
            "1.2.3",
            _rule_manifest() + "unknown: value\n",
        ),
    ],
)
def test_load_game_package_rejects_invalid_or_directory_inconsistent_manifest(
    tmp_path: Path,
    directory_type: str,
    package_id: str,
    package_version: str,
    manifest: str,
) -> None:
    package_directory = _write_package(
        tmp_path, directory_type, package_id, package_version, manifest
    )

    with pytest.raises(GamePackageLoadError) as error:
        load_game_package(package_directory)

    assert error.value.__cause__ is not None


@pytest.mark.parametrize(
    ("manifest", "content"),
    [
        (_rule_manifest(), _SCENARIO_CONTENT),
        (_scenario_manifest(), _RULE_CONTENT),
        (_rule_manifest(), "schema_version: [\n"),
    ],
)
def test_load_game_package_uses_manifest_type_and_fails_atomically(
    tmp_path: Path, manifest: str, content: str
) -> None:
    directory_type = "scenarios" if "package_type: scenario" in manifest else "rules"
    package_id = "lost-woods" if directory_type == "scenarios" else "forest-rules"
    package_version = "2.0.1" if directory_type == "scenarios" else "1.2.3"
    package_directory = _write_package(
        tmp_path, directory_type, package_id, package_version, manifest, content
    )

    with pytest.raises(GamePackageLoadError) as error:
        load_game_package(package_directory)

    assert error.value.__cause__ is not None


@pytest.mark.parametrize(
    "entrypoint", ["/tmp/content.yaml", "../content.yaml", "missing.yaml"]
)
def test_load_game_package_rejects_unsafe_or_missing_entrypoint(
    tmp_path: Path, entrypoint: str
) -> None:
    package_directory = _write_package(
        tmp_path, "rules", "forest-rules", "1.2.3", _rule_manifest(entrypoint)
    )

    with pytest.raises(GamePackageLoadError) as error:
        load_game_package(package_directory)

    assert error.value.__cause__ is not None


def test_load_game_package_rejects_unsafe_yaml_without_executing_it(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path,
        "rules",
        "forest-rules",
        "1.2.3",
        _rule_manifest(),
        "!!python/object/apply:os.system ['echo unsafe']\n",
    )

    with pytest.raises(GamePackageLoadError) as error:
        load_game_package(package_directory)

    assert isinstance(error.value.__cause__, yaml.YAMLError)


def test_load_game_package_rejects_missing_manifest(tmp_path: Path) -> None:
    missing_directory = tmp_path / "game_packages" / "rules" / "forest-rules" / "1.2.3"
    missing_directory.mkdir(parents=True)

    with pytest.raises(GamePackageLoadError) as missing_error:
        load_game_package(missing_directory)

    assert isinstance(missing_error.value.__cause__, FileNotFoundError)


def test_load_game_package_rejects_malformed_manifest(tmp_path: Path) -> None:
    malformed_directory = _write_package(
        tmp_path, "rules", "malformed-rules", "1.2.3", "entrypoint: [\n"
    )

    with pytest.raises(GamePackageLoadError) as malformed_error:
        load_game_package(malformed_directory)

    assert isinstance(malformed_error.value.__cause__, yaml.YAMLError)


def test_load_game_package_rejects_directory_entrypoint(tmp_path: Path) -> None:
    package_directory = _write_package(
        tmp_path, "rules", "forest-rules", "1.2.3", _rule_manifest()
    )
    (package_directory / "content.yaml").unlink()
    (package_directory / "content.yaml").mkdir()

    with pytest.raises(GamePackageLoadError) as error:
        load_game_package(package_directory)

    assert error.value.__cause__ is not None


def test_load_game_package_rejects_symlink_escaping_entrypoint(tmp_path: Path) -> None:
    package_directory = _write_package(
        tmp_path, "rules", "forest-rules", "1.2.3", _rule_manifest()
    )
    (package_directory / "content.yaml").unlink()
    outside_file = tmp_path / "outside.yaml"
    outside_file.write_text(_RULE_CONTENT, encoding="utf-8")
    (package_directory / "content.yaml").symlink_to(outside_file)

    with pytest.raises(GamePackageLoadError) as error:
        load_game_package(package_directory)

    assert error.value.__cause__ is not None
