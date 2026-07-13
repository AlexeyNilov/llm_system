from __future__ import annotations

import os
from collections.abc import Callable
from typing import Literal, cast

import streamlit as st
from pydantic import ValidationError

from llm_system.api import LifecycleResponse, TurnResponse
from llm_system.player_api import (
    ApplicationApiError,
    HttpPlayerApi,
    PlayerApi,
    SafeClientError,
)
from llm_system.simulation.actions import (
    ActorActionProposal,
    CharacterTarget,
    ConnectionTarget,
    HelpActionProposal,
    LocationTarget,
    MoveActionProposal,
    ObjectTarget,
    ObserveActionProposal,
    SpeakActionProposal,
    SurroundingsTarget,
    TakeActionProposal,
    UseActionProposal,
    WaitActionProposal,
)
from llm_system.simulation.events import (
    ActorActionFailedEvent,
    ActorHelpedEvent,
    ActorMovedEvent,
    ActorObservedEvent,
    ActorSpokeEvent,
    ActorWaitedEvent,
    ObjectTakenEvent,
    ObjectUsedEvent,
)
from llm_system.simulation.perception import (
    CharacterObserved,
    ConnectionObserved,
    LocationObserved,
    ObjectObserved,
    Observation,
)

API_URL_ENVIRONMENT_VARIABLE = "LLM_SYSTEM_API_URL"
DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 5.0
HISTORY_KEY = "llm_system_player_turn_history"

ActionName = Literal["Observe", "Move", "Speak", "Take", "Use", "Help", "Wait"]
TargetName = Literal["Surroundings", "Location", "Connection", "Character", "Object"]


def render_player_page(api: PlayerApi) -> None:
    st.title("LLM System player")
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []

    try:
        lifecycle = api.resume_world()
    except ApplicationApiError as error:
        if error.status_code == 404 and error.code == "world-not-found":
            _render_create_world(api)
        else:
            _show_api_error(error)
        return
    except SafeClientError as error:
        _show_client_error(error)
        return

    _render_lifecycle(lifecycle)
    _render_action_form(api)
    _render_history()
    _render_development_reset(api)


def main() -> None:
    api = HttpPlayerApi(
        base_url=os.environ.get(API_URL_ENVIRONMENT_VARIABLE, DEFAULT_API_URL),
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        render_player_page(api)
    finally:
        api.close()


def build_proposal(
    action: ActionName,
    *,
    target_type: TargetName | None = None,
    target_id: str = "",
    connection_id: str = "",
    character_id: str = "",
    object_id: str = "",
    utterance: str = "",
    duration_seconds: int = 0,
) -> ActorActionProposal:
    if action == "Observe":
        if target_type == "Surroundings":
            return ObserveActionProposal(
                operation="observe",
                target=SurroundingsTarget(target_type="surroundings"),
            )
        return ObserveActionProposal(
            operation="observe", target=_target(target_type, target_id)
        )
    if action == "Move":
        _require_non_blank(connection_id)
        return MoveActionProposal(operation="move", connection_id=connection_id)
    if action == "Speak":
        _require_non_blank(character_id)
        _require_non_blank(utterance)
        return SpeakActionProposal(
            operation="speak", character_id=character_id, utterance=utterance
        )
    if action == "Take":
        _require_non_blank(object_id)
        return TakeActionProposal(operation="take", object_id=object_id)
    if action == "Use":
        _require_non_blank(object_id)
        use_target = cast(
            LocationTarget | ConnectionTarget | CharacterTarget | ObjectTarget,
            _target(target_type, target_id, allow_surroundings=False),
        )
        return UseActionProposal(
            operation="use",
            object_id=object_id,
            target=use_target,
        )
    if action == "Help":
        _require_non_blank(character_id)
        return HelpActionProposal(operation="help", character_id=character_id)
    if duration_seconds <= 0:
        raise ValueError("duration must be positive")
    return WaitActionProposal(operation="wait", duration_seconds=duration_seconds)


def format_observation(observation: Observation) -> str:
    if isinstance(observation, LocationObserved):
        return f"Location: {observation.location_id}"
    if isinstance(observation, ConnectionObserved):
        availability = "available" if observation.is_available else "unavailable"
        return f"Connection: {observation.connection_id} ({availability})"
    if isinstance(observation, CharacterObserved):
        return f"Character: {observation.character_id}"
    if isinstance(observation, ObjectObserved):
        placement = observation.placement
        if placement.placement_type == "location":
            placement_text = f"location {placement.location_id}"
        else:
            placement_text = f"possessed by {placement.character_id}"
        return f"Object: {observation.object_id} ({placement_text})"
    return _format_event(observation.event)


def _render_create_world(api: PlayerApi) -> None:
    st.info("No world exists.")
    if st.button("Create world"):
        try:
            with st.spinner("Creating world..."):
                api.create_world()
        except ApplicationApiError as error:
            _show_api_error(error)
        except SafeClientError as error:
            _show_client_error(error)
        else:
            _clear_history()
            st.rerun()


def _render_lifecycle(lifecycle: LifecycleResponse) -> None:
    st.subheader("Active world")
    st.text(f"World UUID: {lifecycle.world_id}")
    st.text(f"Revision: {lifecycle.revision}")
    st.text(f"Simulation time: {lifecycle.simulation_time_seconds} seconds")
    st.text(
        "Rule package: "
        f"{lifecycle.rule_package.package_id} {lifecycle.rule_package.package_version}"
    )
    st.text(
        "Scenario package: "
        f"{lifecycle.scenario_package.package_id} "
        f"{lifecycle.scenario_package.package_version}"
    )


def _render_action_form(api: PlayerApi) -> None:
    st.subheader("Player action")
    action: ActionName = st.selectbox(
        "Action", ("Observe", "Move", "Speak", "Take", "Use", "Help", "Wait")
    )
    values: dict[str, object] = {}
    with st.form("player-action-form"):
        if action == "Observe":
            target_type: TargetName = st.selectbox(
                "Observe target type",
                ("Surroundings", "Location", "Connection", "Character", "Object"),
            )
            values["target_type"] = target_type
            if target_type != "Surroundings":
                values["target_id"] = st.text_input(f"{target_type} identifier")
        elif action == "Move":
            values["connection_id"] = st.text_input("Connection identifier")
        elif action == "Speak":
            values["character_id"] = st.text_input("Character identifier")
            values["utterance"] = st.text_input("Utterance")
        elif action == "Take":
            values["object_id"] = st.text_input("Object identifier")
        elif action == "Use":
            values["object_id"] = st.text_input("Object identifier")
            use_target: TargetName = st.selectbox(
                "Use target type", ("Location", "Connection", "Character", "Object")
            )
            values["target_type"] = use_target
            values["target_id"] = st.text_input(f"Target {use_target} identifier")
        elif action == "Help":
            values["character_id"] = st.text_input("Character identifier")
        else:
            values["duration_seconds"] = int(
                st.number_input("Duration in seconds", min_value=1, value=1, step=1)
            )
        submitted = st.form_submit_button("Submit action")

    if not submitted:
        return
    try:
        proposal = build_proposal(action, **values)  # type: ignore[arg-type]
    except (ValidationError, ValueError):
        st.error("Enter valid values for every required action field.")
        return
    try:
        with st.spinner("Resolving committed turn..."):
            response = api.take_turn(proposal)
    except ApplicationApiError as error:
        _show_api_error(error)
    except SafeClientError as error:
        _show_client_error(error)
    else:
        history = list(_history())
        history.append(response)
        st.session_state[HISTORY_KEY] = history
        st.rerun()


def _render_history() -> None:
    st.subheader("Committed turn history")
    for index, response in enumerate(_history(), start=1):
        st.markdown(f"**Turn {index}**")
        st.text(f"Outcome status: {response.outcome_status}")
        st.text(f"Reason code: {response.reason_code}")
        st.text("Current observations:")
        for observation in response.current_perception.observations:
            st.text(f"- {format_observation(observation)}")
        st.text("Self-event feedback:")
        for feedback in response.self_event_feedback:
            st.text(f"- {_format_event(feedback.event)}")


def _render_development_reset(api: PlayerApi) -> None:
    st.divider()
    st.subheader("Development reset")
    confirmed = st.checkbox("Confirm destructive world reset", value=False)
    if st.button("Reset world", disabled=not confirmed):
        try:
            with st.spinner("Resetting world..."):
                api.reset_world()
        except ApplicationApiError as error:
            _show_api_error(error)
        except SafeClientError as error:
            _show_client_error(error)
        else:
            _clear_history()
            st.rerun()


def _history() -> tuple[TurnResponse, ...]:
    return tuple(st.session_state[HISTORY_KEY])


def _clear_history() -> None:
    st.session_state[HISTORY_KEY] = []


def _target(
    target_type: TargetName | None,
    target_id: str,
    *,
    allow_surroundings: bool = True,
) -> (
    SurroundingsTarget
    | LocationTarget
    | ConnectionTarget
    | CharacterTarget
    | ObjectTarget
):
    if target_type == "Surroundings" and allow_surroundings:
        return SurroundingsTarget(target_type="surroundings")
    _require_non_blank(target_id)
    constructors: dict[
        TargetName,
        Callable[
            [str], LocationTarget | ConnectionTarget | CharacterTarget | ObjectTarget
        ],
    ] = {
        "Location": lambda value: LocationTarget(
            target_type="location", location_id=value
        ),
        "Connection": lambda value: ConnectionTarget(
            target_type="connection", connection_id=value
        ),
        "Character": lambda value: CharacterTarget(
            target_type="character", character_id=value
        ),
        "Object": lambda value: ObjectTarget(target_type="object", object_id=value),
    }
    if target_type not in constructors:
        raise ValueError("target type is required")
    return constructors[target_type](target_id)


def _require_non_blank(value: str) -> None:
    if not value.strip():
        raise ValueError("required text is blank")


def _format_event(
    event: ActorObservedEvent
    | ActorMovedEvent
    | ActorSpokeEvent
    | ObjectTakenEvent
    | ObjectUsedEvent
    | ActorHelpedEvent
    | ActorWaitedEvent
    | ActorActionFailedEvent,
) -> str:
    if isinstance(event, ActorObservedEvent):
        return f"Actor observed: {event.actor_id}; target {event.target.target_type}"
    if isinstance(event, ActorMovedEvent):
        return (
            f"Actor moved: {event.actor_id}; connection {event.connection_id}; "
            f"from {event.from_location_id}; to {event.to_location_id}"
        )
    if isinstance(event, ActorSpokeEvent):
        return (
            f"Actor spoke: {event.speaker_id}; recipient {event.recipient_id}; "
            f"utterance {event.utterance}"
        )
    if isinstance(event, ObjectTakenEvent):
        return f"Object taken: {event.object_id}; actor {event.actor_id}"
    if isinstance(event, ObjectUsedEvent):
        return (
            f"Object used: {event.object_id}; actor {event.actor_id}; "
            f"target {event.target.target_type}"
        )
    if isinstance(event, ActorHelpedEvent):
        return (
            f"Actor helped: {event.actor_id}; character {event.assisted_character_id}"
        )
    if isinstance(event, ActorWaitedEvent):
        return (
            f"Actor waited: {event.actor_id}; duration {event.duration_seconds} seconds"
        )
    return (
        f"Actor action failed: {event.actor_id}; operation {event.attempted_operation}"
    )


def _show_api_error(error: ApplicationApiError) -> None:
    st.error(f"Application error ({error.status_code}): {error.code}")


def _show_client_error(error: SafeClientError) -> None:
    messages = {
        "transport-unavailable": "The API is unavailable.",
        "malformed-response": "The API returned an invalid response.",
        "unexpected-response": "The API returned an unexpected response.",
    }
    st.error(messages[error.kind])


if __name__ == "__main__":
    main()
