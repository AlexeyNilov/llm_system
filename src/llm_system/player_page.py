from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st

from llm_system.api import (
    ActionCompletedPlayerTurnResponse,
    ActionProgressPendingPlayerTurnResponse,
    ClarificationPlayerTurnResponse,
    LifecycleResponse,
    PlayerTurnResponse,
    ScheduledProgressCompletedPlayerTurnResponse,
    ScheduledProgressPendingPlayerTurnResponse,
    ThoughtOnlyPlayerTurnResponse,
)
from llm_system.player_api import (
    ApplicationApiError,
    HttpPlayerApi,
    PlayerApi,
    SafeClientError,
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

API_URL_ENVIRONMENT_VARIABLE = "LLM_SYSTEM_API_URL"
DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 5.0
HISTORY_KEY = "llm_system_player_turn_history"


@dataclass(frozen=True)
class PlayerTurnHistoryEntry:
    player_text: str | None
    response: PlayerTurnResponse


def render_player_page(api: PlayerApi) -> None:
    st.title("LLM System player")
    st.session_state.setdefault(HISTORY_KEY, [])

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
    _render_history()
    _render_player_turn_input(api)
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


def _render_player_turn_input(api: PlayerApi) -> None:
    player_text = st.chat_input("What do you think or attempt?")
    if player_text is None or not player_text.strip():
        return
    try:
        with st.spinner("Resolving player turn..."):
            response = api.take_player_turn(player_text)
    except ApplicationApiError as error:
        _show_api_error(error)
    except SafeClientError as error:
        _show_client_error(error)
    else:
        completed_text = player_text if _input_was_completed(response) else None
        history = [*_history(), PlayerTurnHistoryEntry(completed_text, response)]
        st.session_state[HISTORY_KEY] = history
        st.rerun()


def _render_history() -> None:
    for entry in _history():
        if entry.player_text is not None:
            with st.chat_message("user"):
                st.text(entry.player_text)
        with st.chat_message("assistant"):
            _render_response(entry.response)


def _input_was_completed(response: PlayerTurnResponse) -> bool:
    return not isinstance(
        response,
        (
            ScheduledProgressCompletedPlayerTurnResponse,
            ScheduledProgressPendingPlayerTurnResponse,
        ),
    )


def _render_response(response: PlayerTurnResponse) -> None:
    if isinstance(response, ThoughtOnlyPlayerTurnResponse):
        st.text(f"Thought: {response.private_thought}")
    elif isinstance(response, ClarificationPlayerTurnResponse):
        st.text(f"Clarification: {response.clarification}")
    elif isinstance(response, ScheduledProgressCompletedPlayerTurnResponse):
        st.text("Scheduled progress completed.")
        st.text(response.narration)
    elif isinstance(response, ScheduledProgressPendingPlayerTurnResponse):
        st.text("Scheduled progress remains pending.")
    else:
        if isinstance(response, ActionProgressPendingPlayerTurnResponse):
            st.text("Action committed; scheduled progress remains pending.")
        else:
            assert isinstance(response, ActionCompletedPlayerTurnResponse)
            st.text("Action completed.")
        if response.private_thought is not None:
            st.text(f"Thought: {response.private_thought}")
        st.text(f"Outcome status: {response.outcome_status}")
        st.text(f"Reason code: {response.reason_code}")
        st.text(response.narration)
        st.text("Self-event feedback:")
        for feedback in response.self_event_feedback:
            st.text(f"- {_format_event(feedback.event)}")


def _render_development_reset(api: PlayerApi) -> None:
    with st.expander("Developer tools"):
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


def _history() -> tuple[PlayerTurnHistoryEntry, ...]:
    return tuple(st.session_state[HISTORY_KEY])


def _clear_history() -> None:
    st.session_state[HISTORY_KEY] = []


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
