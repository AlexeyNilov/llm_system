from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import TypeAdapter

from llm_system.game_packages.errors import PackageManifestError
from llm_system.game_packages.models import PackageManifest

_MANIFEST_ADAPTER: TypeAdapter[PackageManifest] = TypeAdapter(PackageManifest)
_PACKAGE_DIRECTORIES = {"rule": "rules", "scenario": "scenarios"}


def load_package_manifest(package_directory: Path) -> PackageManifest:
    """Load a trusted manifest from one exact-version game package directory."""
    try:
        resolved_directory = _validate_package_directory(package_directory)
        manifest_data = _load_yaml(resolved_directory / "manifest.yaml")
        manifest = _MANIFEST_ADAPTER.validate_python(manifest_data, strict=True)
        _validate_directory_identity(resolved_directory, manifest)
        _validate_entrypoint(resolved_directory, manifest.entrypoint)
    except Exception as error:
        raise PackageManifestError("invalid game package manifest") from error
    return manifest


def _validate_package_directory(package_directory: Path) -> Path:
    if not package_directory.is_dir():
        raise NotADirectoryError(package_directory)
    return package_directory.resolve(strict=True)


def _load_yaml(manifest_path: Path) -> object:
    with manifest_path.open(encoding="utf-8") as manifest_file:
        return yaml.safe_load(manifest_file)


def _validate_directory_identity(
    package_directory: Path, manifest: PackageManifest
) -> None:
    package_kind = _PACKAGE_DIRECTORIES[manifest.package_type]
    expected_parts = (
        "game_packages",
        package_kind,
        manifest.package_id,
        manifest.package_version,
    )
    if package_directory.parts[-4:] != expected_parts:
        raise ValueError("package directory does not match manifest identity")


def _validate_entrypoint(package_directory: Path, entrypoint: str) -> None:
    entrypoint_path = Path(entrypoint)
    if entrypoint_path.is_absolute() or ".." in entrypoint_path.parts:
        raise ValueError("entrypoint must be a contained relative path")
    if entrypoint_path.suffix != ".yaml":
        raise ValueError("entrypoint must be a YAML file")
    resolved_entrypoint = (package_directory / entrypoint_path).resolve(strict=True)
    if not resolved_entrypoint.is_relative_to(package_directory):
        raise ValueError("entrypoint resolves outside its package directory")
    if not resolved_entrypoint.is_file():
        raise ValueError("entrypoint must be a regular file")
