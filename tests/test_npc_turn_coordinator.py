from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest

from llm_system.application import (
    NpcDecisionContext,
    UnsupportedNpcTurnError,
    coordinate_caretaker_turn,
    create_world,
)
from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import DuplicateSimulationStepIdentityError, SQLiteStore
from llm_system.simulation import WaitActionProposal


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORLD_ID = UUID("00000000-0000-4000-8000-000000000001")


def _packages() -> ValidatedGamePackages:
    rule = load_game_package(
        REPOSITORY_ROOT / "game_packages/rules/greybridge-rules/0.2.0"
    )
    scenario = load_game_package(
        REPOSITORY_ROOT / "game_packages/scenarios/storm-at-greybridge/0.2.0"
    )
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


def _store(tmp_path: Path) -> SQLiteStore:
    store = SQLiteStore.open(tmp_path / "world.sqlite3")
    create_world(store, _packages(), world_id=WORLD_ID)
    return store


def _identities() -> Iterator[UUID]:
    for number in range(2, 20):
        yield UUID(f"00000000-0000-4000-8000-{number:012d}")


def test_caretaker_turn_commits_bounded_policy_proposal_with_trusted_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    captured_contexts: list[NpcDecisionContext] = []

    def decide(context: NpcDecisionContext) -> WaitActionProposal:
        captured_contexts.append(context)
        return WaitActionProposal(operation="wait", duration_seconds=60)

    monkeypatch.setattr(
        "llm_system.application.npc_turn_coordinator.decide_greybridge_caretaker",
        decide,
    )
    identities = _identities()
    with store.unit_of_work() as unit:
        initial_world = unit.worlds.get()
        assert initial_world is not None
        initial_queue = initial_world.scheduled_queue

    result = coordinate_caretaker_turn(
        store,
        _packages(),
        npc_id="bridge-caretaker",
        policy_id="caretaker-rule-policy",
        identity_factory=lambda: next(identities),
    )

    assert result.result_type == "completed"
    assert result.completed_action.world_id == WORLD_ID
    assert result.completed_action.resulting_world_revision == 1
    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert context.npc_id == "bridge-caretaker"
    assert context.perception.observer_id == "bridge-caretaker"
    assert not hasattr(context, "world_state")
    submission = result.completed_action.trace.submission
    assert submission.actor_id == "bridge-caretaker"
    assert submission.source.source_type == "npc_policy"
    assert submission.source.npc_id == "bridge-caretaker"
    assert submission.source.policy_id == "caretaker-rule-policy"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert len(unit.traces.list_for_world(WORLD_ID)) == 1
        assert world.scheduled_queue == initial_queue


@pytest.mark.parametrize(
    ("npc_id", "policy_id"),
    [
        ("injured-courier", "courier-llm-policy"),
        ("bridge-caretaker", "courier-llm-policy"),
        ("missing", "caretaker-rule-policy"),
        ("reinforcement-materials", "caretaker-rule-policy"),
    ],
)
def test_unsupported_turn_fails_before_policy_or_identity_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    npc_id: str,
    policy_id: str,
) -> None:
    store = _store(tmp_path)
    monkeypatch.setattr(
        "llm_system.application.npc_turn_coordinator.decide_greybridge_caretaker",
        lambda context: (_ for _ in ()).throw(AssertionError("policy must not run")),
    )

    with pytest.raises(UnsupportedNpcTurnError):
        coordinate_caretaker_turn(
            store,
            _packages(),
            npc_id=npc_id,
            policy_id=policy_id,
            identity_factory=lambda: (_ for _ in ()).throw(
                AssertionError("no identity")
            ),
        )

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 0
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert unit.traces.list_for_world(WORLD_ID) == ()


def test_stale_policy_result_assigns_no_identity_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)

    def stale_decision(context: object) -> WaitActionProposal:
        with store.unit_of_work() as unit:
            world = unit.worlds.get()
            assert world is not None
            unit.worlds.replace(
                world_id=world.world_id,
                expected_revision=world.revision,
                state=world.state,
                scheduled_queue=world.scheduled_queue,
            )
            unit.commit()
        return WaitActionProposal(operation="wait", duration_seconds=60)

    monkeypatch.setattr(
        "llm_system.application.npc_turn_coordinator.decide_greybridge_caretaker",
        stale_decision,
    )

    result = coordinate_caretaker_turn(
        store,
        _packages(),
        npc_id="bridge-caretaker",
        policy_id="caretaker-rule-policy",
        identity_factory=lambda: UUID("00000000-0000-4000-8000-000000000002"),
    )

    assert result.result_type == "stale"
    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert unit.events.list_for_world(WORLD_ID) == ()
        assert unit.traces.list_for_world(WORLD_ID) == ()


def test_duplicate_step_rolls_back_caretaker_completion_atomically(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    first_identities = _identities()
    coordinate_caretaker_turn(
        store,
        _packages(),
        npc_id="bridge-caretaker",
        policy_id="caretaker-rule-policy",
        identity_factory=lambda: next(first_identities),
    )
    duplicate_step_id = UUID("00000000-0000-4000-8000-000000000004")
    identities = iter(
        (
            UUID("00000000-0000-4000-8000-000000000021"),
            UUID("00000000-0000-4000-8000-000000000022"),
            duplicate_step_id,
            UUID("00000000-0000-4000-8000-000000000023"),
            UUID("00000000-0000-4000-8000-000000000024"),
        )
    )

    with pytest.raises(DuplicateSimulationStepIdentityError):
        coordinate_caretaker_turn(
            store,
            _packages(),
            npc_id="bridge-caretaker",
            policy_id="caretaker-rule-policy",
            identity_factory=lambda: next(identities),
        )

    with store.unit_of_work() as unit:
        world = unit.worlds.get()
        assert world is not None
        assert world.revision == 1
        assert len(unit.traces.list_for_world(WORLD_ID)) == 1
