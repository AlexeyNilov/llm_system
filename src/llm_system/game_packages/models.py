from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

PackageId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
PackageVersion = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
    ),
]


class RequiredRulePack(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    package_id: PackageId
    package_version: PackageVersion


class BasePackageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal[1]
    package_id: PackageId
    package_version: PackageVersion
    title: str = Field(min_length=1)
    entrypoint: str = Field(min_length=1)

    @field_validator("schema_version", mode="before")
    @classmethod
    def schema_version_must_be_an_integer_literal(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("schema_version must be an integer literal")
        return value

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class RulePackageManifest(BasePackageManifest):
    package_type: Literal["rule"]


class ScenarioPackageManifest(BasePackageManifest):
    package_type: Literal["scenario"]
    required_rule_pack: RequiredRulePack


PackageManifest = Annotated[
    RulePackageManifest | ScenarioPackageManifest,
    Field(discriminator="package_type"),
]
