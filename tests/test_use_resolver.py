from pathlib import Path
from uuid import UUID

import pytest

from llm_system.game_packages import (
    BooleanWorldFactDefinition,
    CharacterArchetypeDefinition,
    ConnectionDefinition,
    DecisionPolicyDefinition,
    EntityCollectionDefinition,
    LoadedRulePackage,
    LoadedScenarioPackage,
    LocationDefinition,
    NpcCharacterDefinition,
    ObjectArchetypeDefinition,
    ObjectDefinition,
    ObjectUseBindingDefinition,
    ObjectUseMechanicDefinition,
    PlayerCharacterDefinition,
    RulePackageManifest,
    RulePackDefinition,
    ScenarioPackageManifest,
    ScenarioPackDefinition,
    SpatialGraphDefinition,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.entities import (
    DecisionPolicyReference,
    GoalDefinition,
    LocationPlacementDefinition,
    PossessedPlacementDefinition,
)
from llm_system.game_packages.models import RequiredRulePack
from llm_system.simulation import (
    ActorActionSubmission,
    AuthorizedActorAction,
    BooleanWorldFactChanged,
    BooleanWorldFactState,
    CharacterState,
    CharacterTarget,
    ConnectionState,
    ConnectionTarget,
    LocationTarget,
    ObjectAtLocation,
    ObjectPossessedByCharacter,
    ObjectState,
    ObjectTarget,
    ObjectUsedEvent,
    PlayerInterpreterActionSource,
    RejectedOutcome,
    SimulationTimeChanged,
    SpeakActionProposal,
    UseActionProposal,
    ValidatedWorldState,
    WorldState,
    commit_outcome,
    resolve_use,
    validate_world_state,
)

PROPOSAL_ID = UUID("7f3fb2d3-9dbf-4529-b347-a86c66c1a62a")
OUTCOME_ID = UUID("ea5559b1-4e4b-46fd-8b14-1e71b1e14c5d")
EVENT_ID = UUID("e36f90e6-3e37-4b2f-8e44-9c4d0f1c2a07")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _object(identifier: str, possessor: str | None) -> ObjectDefinition:
    placement = (
        PossessedPlacementDefinition(placement_type="possessed", character_id=possessor)
        if possessor is not None
        else LocationPlacementDefinition(placement_type="location", location_id="room")
    )
    return ObjectDefinition(
        entity_type="object",
        id=identifier,
        name=identifier.title(),
        object_archetype_id="tool",
        initial_placement=placement,
    )


def _packages() -> tuple[LoadedRulePackage, LoadedScenarioPackage]:
    rule = LoadedRulePackage(
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
            object_archetypes=(ObjectArchetypeDefinition(id="tool", name="Tool"),),
            character_archetypes=(
                CharacterArchetypeDefinition(id="person", name="Person"),
            ),
            decision_policies=(
                DecisionPolicyDefinition(
                    id="routine", name="Routine", policy_type="rule"
                ),
            ),
            object_use_mechanics=(
                ObjectUseMechanicDefinition(
                    id="quick-use",
                    name="Quick Use",
                    object_archetype_id="tool",
                    target_type="location",
                    duration_seconds=12,
                    effect_type="set_boolean_world_fact",
                ),
                ObjectUseMechanicDefinition(
                    id="slow-use",
                    name="Slow Use",
                    object_archetype_id="tool",
                    target_type="location",
                    duration_seconds=45,
                    effect_type="set_boolean_world_fact",
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
                locations=(
                    LocationDefinition(id="room", name="Room"),
                    LocationDefinition(id="remote", name="Remote"),
                    LocationDefinition(id="elsewhere", name="Elsewhere"),
                ),
                connections=(
                    ConnectionDefinition(
                        id="room-to-remote",
                        name="Room to Remote",
                        source_location_id="room",
                        destination_location_id="remote",
                        base_traversal_seconds=1,
                    ),
                    ConnectionDefinition(
                        id="remote-to-elsewhere",
                        name="Remote to Elsewhere",
                        source_location_id="remote",
                        destination_location_id="elsewhere",
                        base_traversal_seconds=1,
                    ),
                ),
            ),
            entity_collection=EntityCollectionDefinition(
                entities=(
                    PlayerCharacterDefinition(
                        entity_type="player_character",
                        id="marin",
                        name="Marin",
                        character_archetype_id="person",
                        initial_location_id="room",
                    ),
                    NpcCharacterDefinition(
                        entity_type="npc_character",
                        id="sela",
                        name="Sela",
                        character_archetype_id="person",
                        initial_location_id="room",
                        identity_summary="A person.",
                        goals=(GoalDefinition(id="remain", description="Remain."),),
                        decision_policy=DecisionPolicyReference(
                            policy_type="rule", policy_id="routine"
                        ),
                    ),
                    _object("tool", "marin"),
                    _object("world-tool", None),
                    _object("other-tool", "sela"),
                    _object("unbound-tool", "marin"),
                )
            ),
            boolean_world_facts=(
                BooleanWorldFactDefinition(
                    id="enabled", name="Enabled", initial_value=False
                ),
                BooleanWorldFactDefinition(
                    id="signal", name="Signal", initial_value=True
                ),
            ),
            object_use_bindings=(
                ObjectUseBindingDefinition(
                    id="tool-room",
                    mechanic_id="quick-use",
                    object_id="tool",
                    target_location_id="room",
                    fact_id="enabled",
                    fact_value=True,
                ),
                ObjectUseBindingDefinition(
                    id="tool-remote",
                    mechanic_id="slow-use",
                    object_id="tool",
                    target_location_id="remote",
                    fact_id="signal",
                    fact_value=False,
                ),
                ObjectUseBindingDefinition(
                    id="world-tool-room",
                    mechanic_id="quick-use",
                    object_id="world-tool",
                    target_location_id="room",
                    fact_id="enabled",
                    fact_value=True,
                ),
                ObjectUseBindingDefinition(
                    id="other-tool-room",
                    mechanic_id="quick-use",
                    object_id="other-tool",
                    target_location_id="room",
                    fact_id="enabled",
                    fact_value=True,
                ),
            ),
        ),
    )
    return rule, scenario


def _world() -> ValidatedWorldState:
    rule, scenario = _packages()
    packages = validate_game_packages(rule, scenario)
    state = WorldState(
        simulation_time_seconds=37,
        characters=(
            CharacterState(character_id="marin", location_id="room"),
            CharacterState(character_id="sela", location_id="room"),
        ),
        objects=(
            ObjectState(
                object_id="tool",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
            ObjectState(
                object_id="world-tool",
                placement=ObjectAtLocation(
                    placement_type="location", location_id="room"
                ),
            ),
            ObjectState(
                object_id="other-tool",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="sela"
                ),
            ),
            ObjectState(
                object_id="unbound-tool",
                placement=ObjectPossessedByCharacter(
                    placement_type="possessed_by_character", character_id="marin"
                ),
            ),
        ),
        connections=(
            ConnectionState(connection_id="room-to-remote", is_available=True),
            ConnectionState(connection_id="remote-to-elsewhere", is_available=True),
        ),
        boolean_world_facts=(
            BooleanWorldFactState(fact_id="enabled", value=False),
            BooleanWorldFactState(fact_id="signal", value=True),
        ),
    )
    return validate_world_state(packages, state)


def _authorized(
    object_id: str = "tool",
    target: object | None = None,
    world: ValidatedWorldState | None = None,
) -> AuthorizedActorAction:
    use_target = target or LocationTarget(target_type="location", location_id="room")
    proposal = UseActionProposal.model_validate(
        {"operation": "use", "object_id": object_id, "target": use_target}
    )
    submission = ActorActionSubmission(
        proposal_id=PROPOSAL_ID,
        simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
        decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
        source=PlayerInterpreterActionSource(
            source_type="player_interpreter", interpreter_id="parser"
        ),
        actor_id="marin",
        proposal=proposal,
    )
    return AuthorizedActorAction(world=world or _world(), submission=submission)


def test_bound_use_returns_exact_ordered_changes_and_event() -> None:
    action = _authorized()
    proposal = action.submission.proposal
    assert isinstance(proposal, UseActionProposal)

    outcome = resolve_use(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome.status == "succeeded"
    assert outcome.reason_code == "object-used"
    assert outcome.resolved_at_seconds == 49
    assert outcome.state_changes == (
        BooleanWorldFactChanged(
            change_type="boolean_world_fact",
            fact_id="enabled",
            from_value=False,
            to_value=True,
        ),
        SimulationTimeChanged(
            change_type="simulation_time", from_seconds=37, to_seconds=49
        ),
    )
    assert outcome.events == (
        ObjectUsedEvent(
            event_type="object_used",
            event_id=EVENT_ID,
            outcome_id=OUTCOME_ID,
            occurred_at_seconds=49,
            actor_id="marin",
            object_id="tool",
            target=proposal.target,
        ),
    )
    assert outcome.events[0].target is proposal.target


def test_exact_object_location_binding_selects_its_authored_mechanic_and_fact() -> None:
    world = _world()
    state = world.state.model_copy(
        update={
            "characters": (
                world.state.characters[0].model_copy(update={"location_id": "remote"}),
                world.state.characters[1],
            )
        }
    )
    action = _authorized(
        target=LocationTarget(target_type="location", location_id="remote"),
        world=validate_world_state(world.packages, state),
    )

    outcome = resolve_use(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)

    assert outcome.status == "succeeded"
    assert outcome.resolved_at_seconds == 82
    assert outcome.state_changes[0] == BooleanWorldFactChanged(
        change_type="boolean_world_fact",
        fact_id="signal",
        from_value=True,
        to_value=False,
    )


@pytest.mark.parametrize(
    ("object_id", "target", "world_update"),
    [
        ("unknown", LocationTarget(target_type="location", location_id="room"), None),
        (
            "unbound-tool",
            LocationTarget(target_type="location", location_id="room"),
            None,
        ),
        ("tool", LocationTarget(target_type="location", location_id="elsewhere"), None),
        (
            "tool",
            ConnectionTarget(target_type="connection", connection_id="room"),
            None,
        ),
        ("tool", CharacterTarget(target_type="character", character_id="room"), None),
        ("tool", ObjectTarget(target_type="object", object_id="room"), None),
        ("room", LocationTarget(target_type="location", location_id="room"), None),
        ("tool", LocationTarget(target_type="location", location_id="marin"), None),
        (
            "world-tool",
            LocationTarget(target_type="location", location_id="room"),
            None,
        ),
        (
            "other-tool",
            LocationTarget(target_type="location", location_id="room"),
            None,
        ),
        ("tool", LocationTarget(target_type="location", location_id="room"), "remote"),
        ("tool", LocationTarget(target_type="location", location_id="room"), "applied"),
    ],
    ids=[
        "unknown-object",
        "unbound-object",
        "unbound-location",
        "connection-target",
        "character-target",
        "object-target",
        "wrong-object-namespace",
        "wrong-location-namespace",
        "world-placed",
        "other-possessor",
        "remote-actor",
        "already-applied",
    ],
)
def test_inapplicable_uses_reject_uniformly_without_effect_fields(
    object_id: str, target: object, world_update: str | None
) -> None:
    world = _world()
    if world_update == "remote":
        characters = (
            world.state.characters[0].model_copy(update={"location_id": "remote"}),
            world.state.characters[1],
        )
        world = validate_world_state(
            world.packages, world.state.model_copy(update={"characters": characters})
        )
    if world_update == "applied":
        facts = (
            world.state.boolean_world_facts[0].model_copy(update={"value": True}),
            world.state.boolean_world_facts[1],
        )
        world = validate_world_state(
            world.packages,
            world.state.model_copy(update={"boolean_world_facts": facts}),
        )

    outcome = resolve_use(
        _authorized(object_id, target, world), outcome_id=OUTCOME_ID, event_id=EVENT_ID
    )

    assert outcome == RejectedOutcome(
        status="rejected",
        outcome_id=OUTCOME_ID,
        proposal_id=PROPOSAL_ID,
        reason_code="use-not-applicable",
        resolved_at_seconds=37,
    )
    assert set(type(outcome).model_fields) == {
        "status",
        "outcome_id",
        "proposal_id",
        "reason_code",
        "resolved_at_seconds",
    }


def test_non_use_action_raises_type_error_without_outcome() -> None:
    use_action = _authorized()
    submission = use_action.submission.model_copy(
        update={
            "proposal": SpeakActionProposal(
                operation="speak", character_id="sela", utterance="Hello"
            )
        }
    )
    action = AuthorizedActorAction(world=use_action.world, submission=submission)

    with pytest.raises(TypeError, match=r"\S+"):
        resolve_use(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)


def test_success_commits_fact_and_time_while_preserving_possession_and_inputs() -> None:
    action = _authorized()
    original = action.model_dump(mode="json")
    packages = action.world.packages
    state = action.world.state
    proposal = action.submission.proposal
    mechanic = packages.rule_package.definition.object_use_mechanics[0]
    binding = packages.scenario_package.definition.object_use_bindings[0]
    object_state = state.objects[0]
    fact_state = state.boolean_world_facts[0]

    first = resolve_use(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    second = resolve_use(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    result = commit_outcome(action.world, first)

    assert first == second
    assert result.world.state.simulation_time_seconds == 49
    assert result.world.state.boolean_world_facts[0].value is True
    assert result.world.state.objects[0].placement == ObjectPossessedByCharacter(
        placement_type="possessed_by_character", character_id="marin"
    )
    assert action.model_dump(mode="json") == original
    assert action.world.packages is packages
    assert action.world.state is state
    assert action.submission.proposal is proposal
    assert packages.rule_package.definition.object_use_mechanics[0] is mechanic
    assert packages.scenario_package.definition.object_use_bindings[0] is binding
    assert state.objects[0] is object_state
    assert state.boolean_world_facts[0] is fact_state


def test_real_greybridge_packages_drive_reinforcement_over_300_seconds() -> None:
    rule = load_game_package(
        REPOSITORY_ROOT / "game_packages/rules/greybridge-rules/0.2.0"
    )
    scenario = load_game_package(
        REPOSITORY_ROOT / "game_packages/scenarios/storm-at-greybridge/0.2.0"
    )
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    packages = validate_game_packages(rule, scenario)
    world = validate_world_state(
        packages,
        WorldState(
            simulation_time_seconds=120,
            characters=(
                CharacterState(character_id="player", location_id="greybridge-span"),
                CharacterState(
                    character_id="injured-courier",
                    location_id="greybridge-waystation",
                ),
                CharacterState(
                    character_id="bridge-caretaker", location_id="greybridge-span"
                ),
            ),
            objects=(
                ObjectState(
                    object_id="medicine",
                    placement=ObjectPossessedByCharacter(
                        placement_type="possessed_by_character",
                        character_id="injured-courier",
                    ),
                ),
                ObjectState(
                    object_id="reinforcement-materials",
                    placement=ObjectPossessedByCharacter(
                        placement_type="possessed_by_character", character_id="player"
                    ),
                ),
            ),
            connections=tuple(
                ConnectionState(connection_id=item.id, is_available=True)
                for item in scenario.definition.spatial_graph.connections
            ),
            boolean_world_facts=(
                BooleanWorldFactState(fact_id="bridge-reinforced", value=False),
            ),
        ),
    )
    action = AuthorizedActorAction(
        world=world,
        submission=ActorActionSubmission(
            proposal_id=PROPOSAL_ID,
            simulation_step_id=UUID("f54e735d-d199-47ef-86e6-2df74e34bc45"),
            decision_context_id=UUID("ef6aa125-4c4f-4c07-8872-dd87f75ff13b"),
            source=PlayerInterpreterActionSource(
                source_type="player_interpreter", interpreter_id="parser"
            ),
            actor_id="player",
            proposal=UseActionProposal(
                operation="use",
                object_id="reinforcement-materials",
                target=LocationTarget(
                    target_type="location", location_id="greybridge-span"
                ),
            ),
        ),
    )

    outcome = resolve_use(action, outcome_id=OUTCOME_ID, event_id=EVENT_ID)
    committed = commit_outcome(world, outcome)

    assert outcome.status == "succeeded"
    assert outcome.resolved_at_seconds == 420
    assert committed.world.state.boolean_world_facts[0].value is True
    assert committed.world.state.simulation_time_seconds == 420
    assert committed.world.state.objects[1] is world.state.objects[1]
