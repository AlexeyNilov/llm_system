from enum import StrEnum
from typing import NoReturn, assert_never

from pydantic import BaseModel, ConfigDict

from llm_system.game_packages._types import NonBlankText
from llm_system.game_packages.entities import (
    NpcCharacterDefinition,
    PlayerCharacterDefinition,
)
from llm_system.simulation.actions import (
    ActorActionSubmission,
    NpcPolicyActionSource,
    PlayerInterpreterActionSource,
)
from llm_system.simulation.validation import ValidatedWorldState


class ActorActionAuthorizationIssueCode(StrEnum):
    UNKNOWN_ACTOR = "unknown-actor"
    SOURCE_ACTOR_MISMATCH = "source-actor-mismatch"
    ACTOR_TYPE_MISMATCH = "actor-type-mismatch"
    POLICY_MISMATCH = "policy-mismatch"


class ActorActionAuthorizationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: ActorActionAuthorizationIssueCode
    path: NonBlankText
    message: NonBlankText


class ActorActionAuthorizationError(Exception):
    def __init__(self, issues: tuple[ActorActionAuthorizationIssue, ...]) -> None:
        if type(issues) is not tuple or not all(
            isinstance(issue, ActorActionAuthorizationIssue) for issue in issues
        ):
            raise TypeError(
                "authorization issues must be a tuple of ActorActionAuthorizationIssue"
            )
        if not issues:
            raise ValueError("authorization error requires at least one issue")
        super().__init__("actor action authorization failed")
        self._issues = issues

    @property
    def issues(self) -> tuple[ActorActionAuthorizationIssue, ...]:
        return self._issues


class AuthorizedActorAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    world: ValidatedWorldState
    submission: ActorActionSubmission


AuthoredCharacter = PlayerCharacterDefinition | NpcCharacterDefinition


def _find_actor(world: ValidatedWorldState, actor_id: str) -> AuthoredCharacter | None:
    entities = world.packages.scenario_package.definition.entity_collection.entities
    return next(
        (
            entity
            for entity in entities
            if isinstance(entity, (PlayerCharacterDefinition, NpcCharacterDefinition))
            and entity.id == actor_id
        ),
        None,
    )


def _deny(code: ActorActionAuthorizationIssueCode, path: str, message: str) -> NoReturn:
    issue = ActorActionAuthorizationIssue(code=code, path=path, message=message)
    raise ActorActionAuthorizationError((issue,))


def _authorize_player_source(actor: AuthoredCharacter) -> None:
    if not isinstance(actor, PlayerCharacterDefinition):
        _deny(
            ActorActionAuthorizationIssueCode.ACTOR_TYPE_MISMATCH,
            "submission.actor_id",
            "player-interpreter source requires the authored player character",
        )


def _authorize_npc_source(
    actor: AuthoredCharacter,
    submission: ActorActionSubmission,
    source: NpcPolicyActionSource,
) -> None:
    if source.npc_id != submission.actor_id:
        _deny(
            ActorActionAuthorizationIssueCode.SOURCE_ACTOR_MISMATCH,
            "submission.source.npc_id",
            "source NPC does not match the intended actor",
        )
    actor = _authorize_npc_actor(actor)
    _authorize_npc_policy(actor, source)


def _authorize_npc_actor(actor: AuthoredCharacter) -> NpcCharacterDefinition:
    if not isinstance(actor, NpcCharacterDefinition):
        _deny(
            ActorActionAuthorizationIssueCode.ACTOR_TYPE_MISMATCH,
            "submission.actor_id",
            "NPC-policy source requires an authored NPC",
        )
    return actor


def _authorize_npc_policy(
    actor: NpcCharacterDefinition, source: NpcPolicyActionSource
) -> None:
    if source.policy_id != actor.decision_policy.policy_id:
        _deny(
            ActorActionAuthorizationIssueCode.POLICY_MISMATCH,
            "submission.source.policy_id",
            "source policy does not match the authored NPC decision policy",
        )


def authorize_actor_action(
    world: ValidatedWorldState, submission: ActorActionSubmission
) -> AuthorizedActorAction:
    actor = _find_actor(world, submission.actor_id)
    if actor is None:
        _deny(
            ActorActionAuthorizationIssueCode.UNKNOWN_ACTOR,
            "submission.actor_id",
            "intended actor is not authored in the validated world",
        )
    source = submission.source
    if isinstance(source, PlayerInterpreterActionSource):
        _authorize_player_source(actor)
    elif isinstance(source, NpcPolicyActionSource):
        _authorize_npc_source(actor, submission, source)
    else:
        assert_never(source)
    return AuthorizedActorAction(world=world, submission=submission)
