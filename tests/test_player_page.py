from __future__ import annotations

import json
from collections.abc import Callable

import httpx2
import pytest
from pydantic import TypeAdapter
from streamlit.testing.v1 import AppTest

import llm_system.player_page as player_page_module
from llm_system.api import LifecycleResponse, PlayerTurnResponse
from llm_system.player_api import (
    ApplicationApiError,
    HttpPlayerApi,
    SafeClientError,
)
from llm_system.player_page import HISTORY_KEY


def test_http_client_sends_player_text_only_to_player_turn_and_validates_variants() -> (
    None
):
    requests: list[httpx2.Request] = []
    bodies = iter(_player_turn_bodies())

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if request.url.path == "/player-turn":
            return httpx2.Response(200, json=next(bodies))
        return httpx2.Response(200, json=_lifecycle_body())

    api = _http_api(handler)

    assert api.resume_world().revision == 2
    assert [api.take_player_turn("I wait.").result_type for _ in range(6)] == [
        "thought_only",
        "clarification",
        "action_completed",
        "action_progress_pending",
        "scheduled_progress_completed",
        "scheduled_progress_pending",
    ]
    assert [(request.method, request.url.path) for request in requests] == [
        ("GET", "/world"),
        *(("POST", "/player-turn") for _ in range(6)),
    ]
    assert all(
        request.read().decode() == '{"player_text":"I wait."}'
        for request in requests[1:]
    )


def test_http_client_maps_player_turn_stale_input_error() -> None:
    api = _http_api(
        lambda request: httpx2.Response(409, json={"code": "player-turn-stale"})
    )

    with pytest.raises(ApplicationApiError) as captured:
        api.take_player_turn("I wait.")

    assert (captured.value.status_code, captured.value.code) == (
        409,
        "player-turn-stale",
    )


@pytest.mark.parametrize(
    ("status_code", "body", "expected"),
    [
        (404, {"code": "world-not-found"}, (404, "world-not-found")),
        (409, {"code": "world-already-exists"}, (409, "world-already-exists")),
        (
            403,
            {"code": "development-reset-disabled"},
            (403, "development-reset-disabled"),
        ),
    ],
)
def test_http_client_maps_only_expected_lifecycle_application_errors(
    status_code: int, body: dict[str, str], expected: tuple[int, str]
) -> None:
    api = _http_api(lambda request: httpx2.Response(status_code, json=body))

    with pytest.raises(ApplicationApiError) as captured:
        api.resume_world()

    assert (captured.value.status_code, captured.value.code) == expected


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(404, json={"code": "world-already-exists"}),
        httpx2.Response(500, text="private server detail"),
    ],
)
def test_http_client_keeps_unexpected_lifecycle_errors_safe(
    response: httpx2.Response,
) -> None:
    api = _http_api(lambda request: response)

    with pytest.raises(SafeClientError) as captured:
        api.resume_world()

    assert captured.value.kind == "unexpected-response"
    assert "private server detail" not in str(captured.value)


def test_http_client_maps_transport_failure_without_leaking_detail() -> None:
    def unavailable(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("private transport detail", request=request)

    with pytest.raises(SafeClientError) as captured:
        _http_api(unavailable).resume_world()

    assert captured.value.kind == "transport-unavailable"
    assert "private transport detail" not in str(captured.value)


def test_http_client_closes_only_the_client_it_owns() -> None:
    transport = CloseTrackingTransport()
    owned_api = HttpPlayerApi(
        base_url="http://player-api.test",
        timeout_seconds=5.0,
        transport=transport,
    )
    injected_client = httpx2.Client(
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(200, json=_lifecycle_body())
        )
    )
    injected_api = HttpPlayerApi(
        base_url="http://player-api.test",
        timeout_seconds=5.0,
        client=injected_client,
    )

    owned_api.close()
    injected_api.close()

    assert transport.closed
    assert not injected_client.is_closed
    assert injected_api.resume_world().revision == 2
    injected_client.close()


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(200, text="not-json"),
        httpx2.Response(200, json={"result_type": "thought_only"}),
        httpx2.Response(200, json={"result_type": "unexpected"}),
        httpx2.Response(409, json={"code": "world-already-exists"}),
    ],
)
def test_http_client_rejects_malformed_or_unmapped_player_turn_responses(
    response: httpx2.Response,
) -> None:
    api = _http_api(lambda request: response)

    with pytest.raises(SafeClientError) as captured:
        api.take_player_turn("I wait.")

    assert captured.value.kind in {"malformed-response", "unexpected-response"}


def test_player_page_shows_each_completed_input_and_only_returned_facts() -> None:
    api = FakePlayerApi(results=list(_player_turn_results()))
    app = AppTest.from_function(_test_page, args=(api,)).run()

    assert len(app.selectbox) == 0
    assert len(app.text_input) == 0
    for prompt in ("I consider.", "Can I cross?", "I wait.", "I wait again."):
        app.chat_input[0].set_value(prompt).run()

    assert api.player_texts == [
        "I consider.",
        "Can I cross?",
        "I wait.",
        "I wait again.",
    ]
    assert [
        entry.player_text for entry in app.session_state[HISTORY_KEY]
    ] == api.player_texts
    rendered = [element.value for element in app.text]
    assert "Thought: I should listen." in rendered
    assert "Clarification: What do you mean by cross?" in rendered
    assert "Outcome status: failed" in rendered
    assert "Reason code: destination-blocked" in rendered
    assert "The waystation is quiet." in rendered
    assert "Self-event feedback:" in rendered
    assert all("proposal" not in value.lower() for value in rendered)
    assert all("trace" not in value.lower() for value in rendered)
    assert all("observer_id" not in value.lower() for value in rendered)


def test_scheduled_progress_discards_uninterpreted_text_but_displays_status() -> None:
    api = FakePlayerApi(results=list(_player_turn_results()[4:]))
    app = AppTest.from_function(_test_page, args=(api,)).run()

    app.chat_input[0].set_value("I try to move.").run()
    app.chat_input[0].set_value("I try again.").run()

    assert api.player_texts == ["I try to move.", "I try again."]
    assert [entry.player_text for entry in app.session_state[HISTORY_KEY]] == [
        None,
        None,
    ]
    rendered = [element.value for element in app.text]
    assert "Scheduled progress completed." in rendered
    assert "Scheduled progress remains pending." in rendered
    assert "I try to move." not in rendered
    assert "I try again." not in rendered


@pytest.mark.parametrize(
    ("turn_error", "visible_error"),
    [
        (
            ApplicationApiError(status_code=409, code="player-turn-stale"),
            "Application error (409): player-turn-stale",
        ),
        (SafeClientError("transport-unavailable"), "The API is unavailable."),
    ],
)
def test_failed_page_turn_keeps_history_and_shows_the_failure(
    turn_error: ApplicationApiError | SafeClientError, visible_error: str
) -> None:
    api = FakePlayerApi(turn_error=turn_error)
    app = AppTest.from_function(_test_page, args=(api,)).run()
    prior_history = [_history_entry("Earlier thought.", _player_turn_results()[0])]
    app.session_state[HISTORY_KEY] = prior_history

    app.chat_input[0].set_value("I wait.").run()

    assert app.session_state[HISTORY_KEY] == prior_history
    assert [error.value for error in app.error] == [visible_error]


def test_missing_world_create_and_confirmation_gated_reset_clear_history() -> None:
    api = FakePlayerApi(world_exists=False)
    app = AppTest.from_function(_test_page, args=(api,)).run()
    app.session_state[HISTORY_KEY] = [
        _history_entry("Earlier.", _player_turn_results()[0])
    ]

    app.button[0].click().run()

    assert api.create_calls == 1
    assert app.session_state[HISTORY_KEY] == []
    app.session_state[HISTORY_KEY] = [
        _history_entry("Earlier.", _player_turn_results()[0])
    ]
    app.checkbox[0].check().run()
    next(button for button in app.button if button.label == "Reset world").click().run()
    assert api.reset_calls == 1
    assert app.session_state[HISTORY_KEY] == []


def test_failed_confirmed_reset_keeps_chat_history_and_shows_failure() -> None:
    api = FakePlayerApi(
        reset_error=ApplicationApiError(
            status_code=403, code="development-reset-disabled"
        )
    )
    app = AppTest.from_function(_test_page, args=(api,)).run()
    history = [_history_entry("Earlier thought.", _player_turn_results()[0])]
    app.session_state[HISTORY_KEY] = history

    app.checkbox[0].check().run()
    next(button for button in app.button if button.label == "Reset world").click().run()

    assert app.session_state[HISTORY_KEY] == history
    assert [error.value for error in app.error] == [
        "Application error (403): development-reset-disabled"
    ]


def test_main_closes_its_owned_client_when_rendering_is_interrupted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = CloseTrackingApi()

    def make_api(*, base_url: str, timeout_seconds: float) -> CloseTrackingApi:
        assert base_url == "http://configured-api.test"
        assert timeout_seconds == 5.0
        return api

    monkeypatch.setenv("LLM_SYSTEM_API_URL", "http://configured-api.test")
    monkeypatch.setattr(player_page_module, "HttpPlayerApi", make_api)
    monkeypatch.setattr(
        player_page_module,
        "render_player_page",
        lambda render_api: (_ for _ in ()).throw(RenderInterrupted()),
    )

    with pytest.raises(RenderInterrupted):
        player_page_module.main()

    assert api.close_calls == 1


def _test_page(api: object) -> None:
    from typing import cast

    from llm_system.player_api import PlayerApi
    from llm_system.player_page import render_player_page

    render_player_page(cast(PlayerApi, api))


class FakePlayerApi:
    def __init__(
        self,
        *,
        world_exists: bool = True,
        results: list[PlayerTurnResponse] | None = None,
        turn_error: ApplicationApiError | SafeClientError | None = None,
        reset_error: ApplicationApiError | SafeClientError | None = None,
    ) -> None:
        self.world_exists = world_exists
        self.results = results or [_player_turn_results()[0]]
        self.turn_error = turn_error
        self.reset_error = reset_error
        self.create_calls = 0
        self.reset_calls = 0
        self.player_texts: list[str] = []

    def create_world(self) -> LifecycleResponse:
        self.create_calls += 1
        self.world_exists = True
        return _lifecycle()

    def resume_world(self) -> LifecycleResponse:
        if not self.world_exists:
            raise ApplicationApiError(status_code=404, code="world-not-found")
        return _lifecycle()

    def reset_world(self) -> LifecycleResponse:
        self.reset_calls += 1
        if self.reset_error is not None:
            raise self.reset_error
        return _lifecycle()

    def take_player_turn(self, player_text: str) -> PlayerTurnResponse:
        self.player_texts.append(player_text)
        if self.turn_error is not None:
            raise self.turn_error
        return self.results.pop(0)


class CloseTrackingApi:
    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class CloseTrackingTransport(httpx2.BaseTransport):
    def __init__(self) -> None:
        self.closed = False

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=_lifecycle_body())

    def close(self) -> None:
        self.closed = True


class RenderInterrupted(BaseException):
    pass


def _http_api(
    handler: Callable[[httpx2.Request], httpx2.Response],
) -> HttpPlayerApi:
    return HttpPlayerApi(
        base_url="http://player-api.test/",
        timeout_seconds=5.0,
        client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


def _lifecycle() -> LifecycleResponse:
    return LifecycleResponse.model_validate_json(json.dumps(_lifecycle_body()))


def _lifecycle_body() -> dict[str, object]:
    return {
        "world_id": "00000000-0000-4000-8000-000000000001",
        "revision": 2,
        "simulation_time_seconds": 15,
        "rule_package": {"package_id": "greybridge-rules", "package_version": "0.2.0"},
        "scenario_package": {
            "package_id": "storm-at-greybridge",
            "package_version": "0.2.0",
        },
    }


def _player_turn_results() -> tuple[PlayerTurnResponse, ...]:
    adapter: TypeAdapter[PlayerTurnResponse] = TypeAdapter(PlayerTurnResponse)
    return tuple(
        adapter.validate_json(json.dumps(body)) for body in _player_turn_bodies()
    )


def _history_entry(player_text: str, response: PlayerTurnResponse) -> object:
    from llm_system.player_page import PlayerTurnHistoryEntry

    return PlayerTurnHistoryEntry(player_text=player_text, response=response)


def _player_turn_bodies() -> tuple[dict[str, object], ...]:
    completed = {
        "world_id": "00000000-0000-4000-8000-000000000001",
        "resulting_world_revision": 3,
        "simulation_step_id": "00000000-0000-4000-8000-000000000002",
        "outcome_status": "failed",
        "reason_code": "destination-blocked",
        "current_perception": {
            "observer_id": "player",
            "perceived_at_seconds": 18,
            "observations": [],
        },
        "self_event_feedback": [],
        "narration": "The waystation is quiet.",
    }
    return (
        {"result_type": "thought_only", "private_thought": "I should listen."},
        {"result_type": "clarification", "clarification": "What do you mean by cross?"},
        {"result_type": "action_completed", **completed, "private_thought": None},
        {
            "result_type": "action_progress_pending",
            **completed,
            "private_thought": "Wait.",
        },
        {
            "result_type": "scheduled_progress_completed",
            "world_id": completed["world_id"],
            "resulting_world_revision": 4,
            "current_perception": completed["current_perception"],
            "narration": completed["narration"],
        },
        {"result_type": "scheduled_progress_pending"},
    )
