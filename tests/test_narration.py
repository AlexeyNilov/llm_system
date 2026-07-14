from pathlib import Path
from uuid import UUID

import pytest

from llm_system.game_packages import (
    LoadedRulePackage,
    LoadedScenarioPackage,
    load_game_package,
    validate_game_packages,
)
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.narration import (
    EventObservationNarrationError,
    NarrationCurrentLocationError,
    NarrationObserverError,
    PlayerNarration,
    NarrationStylePlan,
    NarrationStyleSection,
    NarrationStyleVoice,
    PlayerNarrationContext,
    UnknownObservedIdentifierNarrationError,
    build_player_narration_context,
    render_player_narration,
)
from llm_system.simulation.perception import PerceptionSnapshot


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "game_packages"


def _packages() -> ValidatedGamePackages:
    rule = load_game_package(PACKAGE_ROOT / "rules/greybridge-rules/0.2.0")
    scenario = load_game_package(PACKAGE_ROOT / "scenarios/storm-at-greybridge/0.2.0")
    assert isinstance(rule, LoadedRulePackage)
    assert isinstance(scenario, LoadedScenarioPackage)
    return validate_game_packages(rule, scenario)


def test_renderer_uses_only_observed_names_in_snapshot_group_order() -> None:
    snapshot = PerceptionSnapshot.model_validate(
        {
            "observer_id": "player",
            "perceived_at_seconds": 0,
            "observations": [
                {
                    "observation_type": "location",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "location_id": "greybridge-waystation",
                },
                {
                    "observation_type": "character",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "character_id": "injured-courier",
                },
                {
                    "observation_type": "object",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "object_id": "medicine",
                    "placement": {
                        "placement_type": "location",
                        "location_id": "greybridge-waystation",
                    },
                },
                {
                    "observation_type": "connection",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "connection_id": "waystation-to-span",
                    "is_available": True,
                },
            ],
        }
    )

    context = build_player_narration_context(_packages(), snapshot)
    narration = render_player_narration(context)

    assert context.model_dump() == {
        "current_location_name": "Greybridge Waystation",
        "co_located_character_names": ("Injured Courier",),
        "visible_object_names": ("Medicine",),
        "outgoing_connections": ({"name": "Waystation to Span", "is_available": True},),
    }
    assert narration == PlayerNarration(
        text=(
            "You are at Greybridge Waystation. Nearby: Injured Courier. "
            "Visible objects: Medicine. Exits: Waystation to Span (available)."
        )
    )


def test_renderer_rejects_unknown_observed_identifier_without_fallback() -> None:
    snapshot = PerceptionSnapshot.model_validate(
        {
            "observer_id": "player",
            "perceived_at_seconds": 0,
            "observations": [
                {
                    "observation_type": "location",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "location_id": "not-in-package",
                }
            ],
        }
    )

    with pytest.raises(UnknownObservedIdentifierNarrationError):
        build_player_narration_context(_packages(), snapshot)


def test_renderer_requires_the_authored_player_and_one_location() -> None:
    wrong_observer = PerceptionSnapshot.model_validate(
        {
            "observer_id": "injured-courier",
            "perceived_at_seconds": 0,
            "observations": [],
        }
    )
    missing_location = PerceptionSnapshot.model_validate(
        {
            "observer_id": "player",
            "perceived_at_seconds": 0,
            "observations": [],
        }
    )

    with pytest.raises(NarrationObserverError):
        build_player_narration_context(_packages(), wrong_observer)
    with pytest.raises(NarrationCurrentLocationError):
        build_player_narration_context(_packages(), missing_location)


def test_renderer_rejects_event_observations() -> None:
    snapshot = PerceptionSnapshot.model_validate(
        {
            "observer_id": "player",
            "perceived_at_seconds": 0,
            "observations": [
                {
                    "observation_type": "location",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "location_id": "greybridge-waystation",
                },
                {
                    "observation_type": "event",
                    "source_type": "canonical_event",
                    "observer_id": "player",
                    "observed_at_seconds": 0,
                    "event": {
                        "event_type": "actor_waited",
                        "event_id": UUID("00000000-0000-4000-8000-000000000001"),
                        "occurred_at_seconds": 0,
                        "actor_id": "player",
                        "duration_seconds": 1,
                        "outcome_id": UUID("00000000-0000-4000-8000-000000000002"),
                    },
                },
            ],
        }
    )

    with pytest.raises(EventObservationNarrationError):
        build_player_narration_context(_packages(), snapshot)


def test_renderer_uses_fixed_observational_templates_in_selected_order() -> None:
    context = PlayerNarrationContext(
        current_location_name="Greybridge Waystation",
        co_located_character_names=("Injured Courier",),
        visible_object_names=("Medicine",),
        outgoing_connections=(),
    )
    plan = NarrationStylePlan(
        voice=NarrationStyleVoice.OBSERVATIONAL,
        section_order=(
            NarrationStyleSection.CONNECTIONS,
            NarrationStyleSection.OBJECTS,
            NarrationStyleSection.LOCATION,
            NarrationStyleSection.CHARACTERS,
        ),
    )

    narration = render_player_narration(context, plan)

    assert narration == PlayerNarration(
        text=(
            "Connections: none visible. Objects: Medicine. "
            "Location: Greybridge Waystation. Characters: Injured Courier."
        )
    )
