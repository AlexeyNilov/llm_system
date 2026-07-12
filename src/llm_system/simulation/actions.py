from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

AuthoredId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


def _validate_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("text must not be blank")
    return value


NonBlankText = Annotated[
    str,
    Field(min_length=1),
    AfterValidator(_validate_non_blank),
]
PositiveSeconds = Annotated[int, Field(gt=0)]


class _StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SurroundingsTarget(_StrictContract):
    target_type: Literal["surroundings"]


class LocationTarget(_StrictContract):
    target_type: Literal["location"]
    location_id: AuthoredId


class ConnectionTarget(_StrictContract):
    target_type: Literal["connection"]
    connection_id: AuthoredId


class CharacterTarget(_StrictContract):
    target_type: Literal["character"]
    character_id: AuthoredId


class ObjectTarget(_StrictContract):
    target_type: Literal["object"]
    object_id: AuthoredId


ObservationTarget = Annotated[
    SurroundingsTarget
    | LocationTarget
    | ConnectionTarget
    | CharacterTarget
    | ObjectTarget,
    Field(discriminator="target_type"),
]
UseTarget = Annotated[
    LocationTarget | ConnectionTarget | CharacterTarget | ObjectTarget,
    Field(discriminator="target_type"),
]


class ObserveActionProposal(_StrictContract):
    operation: Literal["observe"]
    target: ObservationTarget


class MoveActionProposal(_StrictContract):
    operation: Literal["move"]
    connection_id: AuthoredId


class SpeakActionProposal(_StrictContract):
    operation: Literal["speak"]
    character_id: AuthoredId
    utterance: NonBlankText


class TakeActionProposal(_StrictContract):
    operation: Literal["take"]
    object_id: AuthoredId


class UseActionProposal(_StrictContract):
    operation: Literal["use"]
    object_id: AuthoredId
    target: UseTarget


class HelpActionProposal(_StrictContract):
    operation: Literal["help"]
    character_id: AuthoredId


class WaitActionProposal(_StrictContract):
    operation: Literal["wait"]
    duration_seconds: PositiveSeconds


ActorActionProposal = Annotated[
    ObserveActionProposal
    | MoveActionProposal
    | SpeakActionProposal
    | TakeActionProposal
    | UseActionProposal
    | HelpActionProposal
    | WaitActionProposal,
    Field(discriminator="operation"),
]


class PlayerInterpreterActionSource(_StrictContract):
    source_type: Literal["player_interpreter"]
    interpreter_id: NonBlankText


class NpcPolicyActionSource(_StrictContract):
    source_type: Literal["npc_policy"]
    npc_id: AuthoredId
    policy_id: AuthoredId


ActorActionSource = Annotated[
    PlayerInterpreterActionSource | NpcPolicyActionSource,
    Field(discriminator="source_type"),
]


class ActorActionSubmission(_StrictContract):
    proposal_id: UUID
    simulation_step_id: UUID
    decision_context_id: UUID
    source: ActorActionSource
    actor_id: AuthoredId
    proposal: ActorActionProposal
