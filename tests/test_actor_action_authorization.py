from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_system.game_packages import (
    CharacterArchetypeDefinition,
    DecisionPolicyDefinition,
    EntityCollectionDefinition,
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationDefinition,
    NpcCharacterDefinition,
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    validate_game_packages,
)
from llm_system.game_packages.entities import DecisionPolicyReference, GoalDefinition
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionAuthorizationError,
    ActorActionAuthorizationIssue,
    ActorActionAuthorizationIssueCode,
    ActorActionSource,
    ActorActionSubmission,
    AuthorizedActorAction,
    CharacterState,
    NpcPolicyActionSource,
    PlayerInterpreterActionSource,
    TakeActionProposal,
    ValidatedWorldState,
    WorldState,
    authorize_actor_action,
    validate_world_state,
)


def _world() -> ValidatedWorldState:
    rules = LoadedRulePackage(
        manifest=RulePackageManifest(
            schema_version=1,
            package_id="rules",
            package_version="1.0.0",
            package_type="rule",
            title="Rules",
            entrypoint="content.yaml",
        ),
        definition=RulePackDefinition(
            schema_version=1,
            object_archetypes=(),
            character_archetypes=(
                CharacterArchetypeDefinition(id="person", name="Person"),
            ),
            decision_policies=(
                DecisionPolicyDefinition(
                    id="routine", name="Routine", policy_type="rule"
                ),
            ),
        ),
    )
    scenario = LoadedScenarioPackage(
        manifest=ScenarioPackageManifest(
            schema_version=1,
            package_id="scenario",
            package_version="1.0.0",
            package_type="scenario",
            title="Scenario",
            entrypoint="content.yaml",
            required_rule_pack=RequiredRulePack(
                package_id="rules", package_version="1.0.0"
            ),
        ),
        definition=ScenarioPackDefinition(
            schema_version=1,
            spatial_graph=SpatialGraphDefinition(
                locations=(LocationDefinition(id="square", name="Square"),),
                connections=(),
            ),
            entity_collection=EntityCollectionDefinition(
                entities=(
                    PlayerCharacterDefinition(
                        entity_type="player_character",
                        id="marin",
                        name="Marin",
                        character_archetype_id="person",
                        initial_location_id="square",
                    ),
                    NpcCharacterDefinition(
                        entity_type="npc_character",
                        id="sela",
                        name="Sela",
                        character_archetype_id="person",
                        initial_location_id="square",
                        identity_summary="A guide.",
                        goals=(GoalDefinition(id="guide", description="Guide."),),
                        decision_policy=DecisionPolicyReference(
                            policy_type="rule", policy_id="routine"
                        ),
                    ),
                )
            ),
        ),
    )
    packages = validate_game_packages(rules, scenario)
    state = WorldState(
        simulation_time_seconds=0,
        characters=(
            CharacterState(character_id="marin", location_id="square"),
            CharacterState(character_id="sela", location_id="square"),
        ),
        objects=(),
        connections=(),
    )
    return validate_world_state(packages, state)


def _submission(*, actor_id: str, source: ActorActionSource) -> ActorActionSubmission:
    return ActorActionSubmission.model_validate(
        {
            "proposal_id": UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07"),
            "simulation_step_id": UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d"),
            "decision_context_id": UUID("864c0a47-0f9b-4866-a178-3380a4a5543d"),
            "source": source,
            "actor_id": actor_id,
            "proposal": TakeActionProposal(
                operation="take", object_id="not-an-authored-object"
            ),
        }
    )


def _player_submission(
    actor_id: str, interpreter_id: str = "unregistered-parser"
) -> ActorActionSubmission:
    return _submission(
        actor_id=actor_id,
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id=interpreter_id
        ),
    )


def _npc_submission(
    actor_id: str, npc_id: str, policy_id: str
) -> ActorActionSubmission:
    return _submission(
        actor_id=actor_id,
        source=NpcPolicyActionSource(
            source_type="npc_policy", npc_id=npc_id, policy_id=policy_id
        ),
    )


def _authorization_issue(
    submission: ActorActionSubmission,
) -> ActorActionAuthorizationIssue:
    with pytest.raises(ActorActionAuthorizationError) as error:
        authorize_actor_action(_world(), submission)
    assert len(error.value.issues) == 1
    return error.value.issues[0]


def test_authorized_player_submission_preserves_exact_inputs_and_interpreter_provenance() -> (
    None
):
    world = _world()
    submission = _player_submission("marin", interpreter_id="not-allowlisted")
    original_world = world.model_dump(mode="json")
    original_submission = submission.model_dump(mode="json")

    authorized = authorize_actor_action(world, submission)

    assert authorized.world is world
    assert authorized.submission is submission
    assert isinstance(authorized.submission.source, PlayerInterpreterActionSource)
    assert authorized.submission.source.interpreter_id == "not-allowlisted"
    assert world.model_dump(mode="json") == original_world
    assert submission.model_dump(mode="json") == original_submission


def test_authorized_npc_submission_uses_configured_policy_and_ignores_proposal_actionability() -> (
    None
):
    world = _world()
    submission = _npc_submission("sela", "sela", "routine")

    authorized = authorize_actor_action(world, submission)

    assert authorized.world is world
    assert authorized.submission is submission
    assert isinstance(authorized.submission.proposal, TakeActionProposal)
    assert authorized.submission.proposal.object_id == "not-an-authored-object"


def test_unknown_actor_suppresses_all_source_specific_checks() -> None:
    issue = _authorization_issue(
        _npc_submission("missing", "different-npc", "wrong-policy")
    )

    assert (issue.code, issue.path) == (
        ActorActionAuthorizationIssueCode.UNKNOWN_ACTOR,
        "submission.actor_id",
    )


def test_player_source_cannot_submit_for_known_npc() -> None:
    issue = _authorization_issue(_player_submission("sela"))

    assert (issue.code, issue.path) == (
        ActorActionAuthorizationIssueCode.ACTOR_TYPE_MISMATCH,
        "submission.actor_id",
    )


def test_npc_source_actor_mismatch_suppresses_actor_type_and_policy_checks() -> None:
    issue = _authorization_issue(_npc_submission("marin", "sela", "wrong-policy"))

    assert (issue.code, issue.path) == (
        ActorActionAuthorizationIssueCode.SOURCE_ACTOR_MISMATCH,
        "submission.source.npc_id",
    )


def test_matching_npc_source_cannot_submit_for_player_and_suppresses_policy_check() -> (
    None
):
    issue = _authorization_issue(_npc_submission("marin", "marin", "wrong-policy"))

    assert (issue.code, issue.path) == (
        ActorActionAuthorizationIssueCode.ACTOR_TYPE_MISMATCH,
        "submission.actor_id",
    )


def test_matching_npc_source_requires_the_authored_npc_policy_identity() -> None:
    issue = _authorization_issue(_npc_submission("sela", "sela", "wrong-policy"))

    assert (issue.code, issue.path) == (
        ActorActionAuthorizationIssueCode.POLICY_MISMATCH,
        "submission.source.policy_id",
    )


def test_authorization_evidence_contracts_are_exact_strict_and_immutable() -> None:
    assert {code.value for code in ActorActionAuthorizationIssueCode} == {
        "unknown-actor",
        "source-actor-mismatch",
        "actor-type-mismatch",
        "policy-mismatch",
    }
    issue = ActorActionAuthorizationIssue(
        code=ActorActionAuthorizationIssueCode.UNKNOWN_ACTOR,
        path="submission.actor_id",
        message="intended actor is not authored",
    )

    with pytest.raises(ValidationError):
        issue.path = "submission.source"
    for invalid_issue in (
        {"code": "unknown-actor", "path": "submission.actor_id", "message": "bad"},
        {
            "code": ActorActionAuthorizationIssueCode.UNKNOWN_ACTOR,
            "path": "   ",
            "message": "bad",
        },
        {
            "code": ActorActionAuthorizationIssueCode.UNKNOWN_ACTOR,
            "path": "submission.actor_id",
            "message": "",
        },
        {
            "code": ActorActionAuthorizationIssueCode.UNKNOWN_ACTOR,
            "path": "submission.actor_id",
            "message": "bad",
            "extra": "forbidden",
        },
    ):
        with pytest.raises(ValidationError):
            ActorActionAuthorizationIssue.model_validate(invalid_issue)
    for invalid_issues in ((), [issue], ("not-an-issue",)):
        with pytest.raises((TypeError, ValueError)):
            ActorActionAuthorizationError(invalid_issues)  # type: ignore[arg-type]
    error = ActorActionAuthorizationError((issue,))
    with pytest.raises(AttributeError):
        error.issues = (issue,)  # type: ignore[misc]


def test_authorized_wrapper_contains_exactly_world_and_submission_and_is_immutable() -> (
    None
):
    world = _world()
    submission = _player_submission("marin")
    authorized = AuthorizedActorAction(world=world, submission=submission)

    assert set(AuthorizedActorAction.model_fields) == {"world", "submission"}
    with pytest.raises(ValidationError):
        authorized.world = world
    with pytest.raises(ValidationError):
        AuthorizedActorAction.model_validate(
            {"world": world, "submission": submission, "extra": "forbidden"}
        )
