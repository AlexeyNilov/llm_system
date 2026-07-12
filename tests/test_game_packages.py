from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from llm_system.game_packages import (
    PackageManifestError,
    RulePackageManifest,
    ScenarioPackageManifest,
    load_package_manifest,
)


def _write_package(
    tmp_path: Path,
    package_type: str,
    package_id: str,
    package_version: str,
    manifest: str,
) -> Path:
    package_directory = (
        tmp_path / "game_packages" / package_type / package_id / package_version
    )
    package_directory.mkdir(parents=True)
    (package_directory / "content.yaml").write_text("content: []\n", encoding="utf-8")
    (package_directory / "manifest.yaml").write_text(manifest, encoding="utf-8")
    return package_directory


def test_load_package_manifest_returns_frozen_rule_manifest_for_matching_directory(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path,
        "rules",
        "forest-rules",
        "1.2.3",
        """\
schema_version: 1
package_id: forest-rules
package_version: 1.2.3
package_type: rule
title: Forest Rules
entrypoint: content.yaml
""",
    )

    manifest = load_package_manifest(package_directory)

    assert isinstance(manifest, RulePackageManifest)
    assert manifest.package_id == "forest-rules"
    assert manifest.package_version == "1.2.3"
    assert manifest.entrypoint == "content.yaml"
    with pytest.raises(ValidationError):
        manifest.title = "Changed"


def test_load_package_manifest_returns_scenario_with_exact_rule_pack_pin(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path,
        "scenarios",
        "lost-woods",
        "2.0.1",
        """\
schema_version: 1
package_id: lost-woods
package_version: 2.0.1
package_type: scenario
title: Lost Woods
entrypoint: content.yaml
required_rule_pack:
  package_id: forest-rules
  package_version: 1.2.3
""",
    )

    manifest = load_package_manifest(package_directory)

    assert isinstance(manifest, ScenarioPackageManifest)
    assert manifest.required_rule_pack.package_id == "forest-rules"
    assert manifest.required_rule_pack.package_version == "1.2.3"


@pytest.mark.parametrize(
    "manifest",
    [
        """schema_version: 1\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\nrequired_rule_pack: {}\n""",
        """schema_version: 1\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: scenario\ntitle: Forest Rules\nentrypoint: content.yaml\n""",
        """schema_version: 1\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\nunknown: value\n""",
        """schema_version: '1'\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\n""",
        """schema_version: true\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\n""",
        """schema_version: 2\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\n""",
        """schema_version: 1\npackage_id: Forest_Rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\n""",
        """schema_version: 1\npackage_id: forest-rules\npackage_version: 1.2\npackage_type: rule\ntitle: Forest Rules\nentrypoint: content.yaml\n""",
        """schema_version: 1\npackage_id: forest-rules\npackage_version: 1.2.3\npackage_type: rule\ntitle: '   '\nentrypoint: content.yaml\n""",
    ],
)
def test_load_package_manifest_rejects_invalid_schema(
    tmp_path: Path, manifest: str
) -> None:
    package_directory = _write_package(
        tmp_path, "rules", "forest-rules", "1.2.3", manifest
    )

    with pytest.raises(PackageManifestError) as error:
        load_package_manifest(package_directory)

    assert error.value.__cause__ is not None


def test_load_package_manifest_rejects_missing_manifest(tmp_path: Path) -> None:
    missing_directory = tmp_path / "game_packages" / "rules" / "forest-rules" / "1.2.3"
    missing_directory.mkdir(parents=True)

    with pytest.raises(PackageManifestError) as error:
        load_package_manifest(missing_directory)

    assert isinstance(error.value.__cause__, FileNotFoundError)


def test_load_package_manifest_rejects_malformed_yaml(tmp_path: Path) -> None:
    malformed_directory = _write_package(
        tmp_path, "rules", "malformed-rules", "1.2.3", "entrypoint: [\n"
    )

    with pytest.raises(PackageManifestError) as error:
        load_package_manifest(malformed_directory)

    assert isinstance(error.value.__cause__, yaml.YAMLError)


def test_load_package_manifest_rejects_unsafe_yaml_tag(tmp_path: Path) -> None:
    unsafe_directory = _write_package(
        tmp_path,
        "rules",
        "unsafe-rules",
        "1.2.3",
        "!!python/object/apply:os.system ['echo unsafe']\n",
    )

    with pytest.raises(PackageManifestError) as error:
        load_package_manifest(unsafe_directory)

    assert isinstance(error.value.__cause__, yaml.YAMLError)


@pytest.mark.parametrize(
    ("directory_type", "directory_id", "directory_version"),
    [
        ("scenarios", "forest-rules", "1.2.3"),
        ("rules", "other-rules", "1.2.3"),
        ("rules", "forest-rules", "1.2.4"),
    ],
)
def test_load_package_manifest_rejects_directory_identity_mismatch(
    tmp_path: Path, directory_type: str, directory_id: str, directory_version: str
) -> None:
    package_directory = _write_package(
        tmp_path,
        directory_type,
        directory_id,
        directory_version,
        """\
schema_version: 1
package_id: forest-rules
package_version: 1.2.3
package_type: rule
title: Forest Rules
entrypoint: content.yaml
""",
    )

    with pytest.raises(PackageManifestError):
        load_package_manifest(package_directory)


@pytest.mark.parametrize(
    "entrypoint",
    ["/tmp/content.yaml", "../content.yaml", "content.json", "missing.yaml"],
)
def test_load_package_manifest_rejects_unsafe_or_missing_entrypoint(
    tmp_path: Path, entrypoint: str
) -> None:
    package_directory = _write_package(
        tmp_path,
        "rules",
        "forest-rules",
        "1.2.3",
        f"""\
schema_version: 1
package_id: forest-rules
package_version: 1.2.3
package_type: rule
title: Forest Rules
entrypoint: {entrypoint}
""",
    )

    with pytest.raises(PackageManifestError):
        load_package_manifest(package_directory)


def test_load_package_manifest_rejects_directory_entrypoint(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path,
        "rules",
        "forest-rules",
        "1.2.3",
        """\
schema_version: 1
package_id: forest-rules
package_version: 1.2.3
package_type: rule
title: Forest Rules
entrypoint: content.yaml
""",
    )
    (package_directory / "content.yaml").unlink()
    (package_directory / "content.yaml").mkdir()

    with pytest.raises(PackageManifestError):
        load_package_manifest(package_directory)


def test_load_package_manifest_rejects_symlink_escaping_entrypoint(
    tmp_path: Path,
) -> None:
    package_directory = _write_package(
        tmp_path,
        "rules",
        "forest-rules",
        "1.2.3",
        """\
schema_version: 1
package_id: forest-rules
package_version: 1.2.3
package_type: rule
title: Forest Rules
entrypoint: content.yaml
""",
    )

    (package_directory / "content.yaml").unlink()
    outside_file = tmp_path / "outside.yaml"
    outside_file.write_text("outside: true\n", encoding="utf-8")
    (package_directory / "content.yaml").symlink_to(outside_file)

    with pytest.raises(PackageManifestError):
        load_package_manifest(package_directory)
