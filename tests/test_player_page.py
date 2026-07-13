from __future__ import annotations

import json
from collections.abc import Callable
from typing import cast

import httpx2
import pytest
from streamlit.testing.v1 import AppTest

import llm_system.player_page as player_page_module
from llm_system.api import LifecycleResponse, TurnResponse
from llm_system.player_api import (
    ApplicationApiError,
    HttpPlayerApi,
    SafeClientError,
)
from llm_system.player_page import ActionName, HISTORY_KEY, build_proposal
from llm_system.simulation.actions import ActorActionProposal


def test_http_client_sends_the_exact_four_requests_and_validates_successes() -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if request.url.path == "/turn":
            return httpx2.Response(200, json=_turn_body())
        return httpx2.Response(200, json=_lifecycle_body())

    api = _http_api(handler)

    assert api.resume_world().revision == 2
    assert api.create_world().world_id == _lifecycle().world_id
    assert api.reset_world().simulation_time_seconds == 15
    turn = api.take_turn(build_proposal("Wait", duration_seconds=3))

    assert turn.outcome_status == "failed"
    assert [(request.method, request.url.path) for request in requests] == [
        ("GET", "/world"),
        ("POST", "/world"),
        ("POST", "/development/reset"),
        ("POST", "/turn"),
    ]
    assert requests[1].content == b""
    assert requests[2].content == b""
    assert requests[3].read().decode() == (
        '{"proposal":{"operation":"wait","duration_seconds":3}}'
    )
    for request in requests:
        assert request.url.host == "player-api.test"
        assert request.extensions["timeout"]["read"] == 5.0


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
def test_http_client_preserves_only_mapped_application_error_status_and_code(
    status_code: int, body: dict[str, str], expected: tuple[int, str]
) -> None:
    api = _http_api(lambda request: httpx2.Response(status_code, json=body))

    with pytest.raises(ApplicationApiError) as captured:
        api.resume_world()

    assert (captured.value.status_code, captured.value.code) == expected


@pytest.mark.parametrize(
    ("response", "kind"),
    [
        (httpx2.Response(200, text="not-json"), "malformed-response"),
        (httpx2.Response(200, json={"revision": 2}), "malformed-response"),
        (
            httpx2.Response(404, json={"code": "world-already-exists"}),
            "unexpected-response",
        ),
        (httpx2.Response(422, text="private server detail"), "unexpected-response"),
        (httpx2.Response(500, text="private server detail"), "unexpected-response"),
    ],
)
def test_http_client_rejects_untrusted_or_unrecognized_responses_safely(
    response: httpx2.Response, kind: str
) -> None:
    api = _http_api(lambda request: response)

    with pytest.raises(SafeClientError, match=kind) as captured:
        api.resume_world()

    assert captured.value.kind == kind
    assert "private server detail" not in str(captured.value)


def test_http_client_maps_transport_failure_without_exposing_detail() -> None:
    def unavailable(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("secret transport detail", request=request)

    with pytest.raises(SafeClientError) as captured:
        _http_api(unavailable).resume_world()

    assert captured.value.kind == "transport-unavailable"
    assert "secret" not in str(captured.value)


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


def test_main_closes_its_owned_client_when_rendering_is_interrupted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = CloseTrackingApi()

    def make_api(*, base_url: str, timeout_seconds: float) -> CloseTrackingApi:
        assert base_url == "http://configured-api.test"
        assert timeout_seconds == 5.0
        return api

    def interrupted_render(render_api: object) -> None:
        assert render_api is api
        raise RenderInterrupted

    monkeypatch.setenv("LLM_SYSTEM_API_URL", "http://configured-api.test")
    monkeypatch.setattr(player_page_module, "HttpPlayerApi", make_api)
    monkeypatch.setattr(player_page_module, "render_player_page", interrupted_render)

    with pytest.raises(RenderInterrupted):
        player_page_module.main()

    assert api.close_calls == 1


@pytest.mark.parametrize(
    ("action", "arguments", "expected"),
    [
        (
            "Observe",
            {"target_type": "Surroundings"},
            {"operation": "observe", "target": {"target_type": "surroundings"}},
        ),
        (
            "Observe",
            {"target_type": "Location", "target_id": "bridge"},
            {
                "operation": "observe",
                "target": {"target_type": "location", "location_id": "bridge"},
            },
        ),
        (
            "Observe",
            {"target_type": "Connection", "target_id": "north-road"},
            {
                "operation": "observe",
                "target": {
                    "target_type": "connection",
                    "connection_id": "north-road",
                },
            },
        ),
        (
            "Observe",
            {"target_type": "Character", "target_id": "courier"},
            {
                "operation": "observe",
                "target": {"target_type": "character", "character_id": "courier"},
            },
        ),
        (
            "Observe",
            {"target_type": "Object", "target_id": "rope"},
            {
                "operation": "observe",
                "target": {"target_type": "object", "object_id": "rope"},
            },
        ),
        (
            "Move",
            {"connection_id": "north-road"},
            {"operation": "move", "connection_id": "north-road"},
        ),
        (
            "Speak",
            {"character_id": "courier", "utterance": "Hold fast"},
            {"operation": "speak", "character_id": "courier", "utterance": "Hold fast"},
        ),
        ("Take", {"object_id": "rope"}, {"operation": "take", "object_id": "rope"}),
        (
            "Use",
            {"object_id": "rope", "target_type": "Location", "target_id": "bridge"},
            {
                "operation": "use",
                "object_id": "rope",
                "target": {"target_type": "location", "location_id": "bridge"},
            },
        ),
        (
            "Use",
            {
                "object_id": "rope",
                "target_type": "Connection",
                "target_id": "north-road",
            },
            {
                "operation": "use",
                "object_id": "rope",
                "target": {
                    "target_type": "connection",
                    "connection_id": "north-road",
                },
            },
        ),
        (
            "Use",
            {"object_id": "rope", "target_type": "Character", "target_id": "courier"},
            {
                "operation": "use",
                "object_id": "rope",
                "target": {"target_type": "character", "character_id": "courier"},
            },
        ),
        (
            "Use",
            {"object_id": "rope", "target_type": "Object", "target_id": "hook"},
            {
                "operation": "use",
                "object_id": "rope",
                "target": {"target_type": "object", "object_id": "hook"},
            },
        ),
        (
            "Help",
            {"character_id": "courier"},
            {"operation": "help", "character_id": "courier"},
        ),
        ("Wait", {"duration_seconds": 3}, {"operation": "wait", "duration_seconds": 3}),
    ],
)
def test_each_action_control_maps_to_its_strict_proposal(
    action: str, arguments: dict[str, object], expected: dict[str, object]
) -> None:
    proposal = build_proposal(cast(ActionName, action), **arguments)  # type: ignore[arg-type]

    assert proposal.model_dump(mode="json") == expected


@pytest.mark.parametrize(
    ("action", "arguments"),
    [
        ("Move", {"connection_id": " "}),
        ("Speak", {"character_id": "courier", "utterance": " "}),
        ("Use", {"object_id": "rope", "target_type": "Object", "target_id": ""}),
        ("Wait", {"duration_seconds": 0}),
    ],
)
def test_incomplete_actions_are_rejected_before_submission(
    action: str, arguments: dict[str, object]
) -> None:
    with pytest.raises(ValueError):
        build_proposal(cast(ActionName, action), **arguments)  # type: ignore[arg-type]


def test_player_page_submits_a_typed_turn_and_renders_committed_fields_in_order() -> (
    None
):
    api = FakePlayerApi()
    app = AppTest.from_function(_test_page, args=(api,)).run()

    assert app.selectbox[0].options == [
        "Observe",
        "Move",
        "Speak",
        "Take",
        "Use",
        "Help",
        "Wait",
    ]
    assert len(app.text_input) == 0
    app.selectbox[0].select("Wait").run()
    app.number_input[0].set_value(3)
    app.button(key="FormSubmitter:player-action-form-Submit action").click().run()

    assert [proposal.model_dump(mode="json") for proposal in api.proposals] == [
        {"operation": "wait", "duration_seconds": 3}
    ]
    rendered = [element.value for element in app.text]
    assert "Outcome status: failed" in rendered
    assert "Reason code: destination-blocked" in rendered
    assert rendered.index("- Location: bridge") < rendered.index(
        "- Connection: north-road (available)"
    )
    assert "- Actor waited: player; duration 3 seconds" in rendered
    assert len(app.session_state[HISTORY_KEY]) == 1


def test_local_page_validation_shows_an_error_and_sends_no_turn() -> None:
    api = FakePlayerApi()
    app = AppTest.from_function(_test_page, args=(api,)).run()
    app.selectbox[0].select("Move").run()

    app.button(key="FormSubmitter:player-action-form-Submit action").click().run()

    assert api.proposals == []
    assert [error.value for error in app.error] == [
        "Enter valid values for every required action field."
    ]


@pytest.mark.parametrize(
    ("turn_error", "visible_error"),
    [
        (
            ApplicationApiError(status_code=404, code="world-not-found"),
            "Application error (404): world-not-found",
        ),
        (SafeClientError("transport-unavailable"), "The API is unavailable."),
    ],
)
def test_failed_page_turn_keeps_existing_history_and_shows_the_failure(
    turn_error: ApplicationApiError | SafeClientError, visible_error: str
) -> None:
    api = FakePlayerApi(turn_error=turn_error)
    app = AppTest.from_function(_test_page, args=(api,)).run()
    prior_history = [_turn()]
    app.session_state[HISTORY_KEY] = prior_history

    app.selectbox[0].select("Wait").run()
    app.number_input[0].set_value(3)
    app.button(key="FormSubmitter:player-action-form-Submit action").click().run()

    assert app.session_state[HISTORY_KEY] == prior_history
    assert [error.value for error in app.error] == [visible_error]
    assert "Outcome status: failed" in [element.value for element in app.text]


def test_failed_confirmed_reset_keeps_history_and_shows_no_success() -> None:
    api = FakePlayerApi(
        reset_error=ApplicationApiError(
            status_code=403, code="development-reset-disabled"
        )
    )
    app = AppTest.from_function(_test_page, args=(api,)).run()
    prior_history = [_turn()]
    app.session_state[HISTORY_KEY] = prior_history

    app.checkbox[0].check().run()
    next(button for button in app.button if button.label == "Reset world").click().run()

    assert api.reset_calls == 1
    assert app.session_state[HISTORY_KEY] == prior_history
    assert [error.value for error in app.error] == [
        "Application error (403): development-reset-disabled"
    ]
    assert "Outcome status: failed" in [element.value for element in app.text]


def test_missing_world_create_and_confirmation_gated_reset_clear_history() -> None:
    api = FakePlayerApi(world_exists=False)
    app = AppTest.from_function(_test_page, args=(api,)).run()
    app.session_state[HISTORY_KEY] = [_turn()]

    assert [button.label for button in app.button] == ["Create world"]
    app.button[0].click().run()

    assert api.create_calls == 1
    assert app.session_state[HISTORY_KEY] == []
    reset_button = next(
        button for button in app.button if button.label == "Reset world"
    )
    assert reset_button.disabled
    app.checkbox[0].check().run()
    app.session_state[HISTORY_KEY] = [_turn()]
    next(button for button in app.button if button.label == "Reset world").click().run()
    assert api.reset_calls == 1
    assert app.session_state[HISTORY_KEY] == []


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
        turn_error: ApplicationApiError | SafeClientError | None = None,
        reset_error: ApplicationApiError | SafeClientError | None = None,
    ) -> None:
        self.world_exists = world_exists
        self.turn_error = turn_error
        self.reset_error = reset_error
        self.create_calls = 0
        self.reset_calls = 0
        self.proposals: list[ActorActionProposal] = []

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

    def take_turn(self, proposal: ActorActionProposal) -> TurnResponse:
        self.proposals.append(proposal)
        if self.turn_error is not None:
            raise self.turn_error
        return _turn()


class CloseTrackingTransport(httpx2.BaseTransport):
    def __init__(self) -> None:
        self.closed = False

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=_lifecycle_body())

    def close(self) -> None:
        self.closed = True


class CloseTrackingApi:
    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class RenderInterrupted(BaseException):
    pass


def _http_api(
    handler: Callable[[httpx2.Request], httpx2.Response],
) -> HttpPlayerApi:
    transport = httpx2.MockTransport(handler)
    client = httpx2.Client(transport=transport)
    return HttpPlayerApi(
        base_url="http://player-api.test/",
        timeout_seconds=5.0,
        client=client,
    )


def _lifecycle() -> LifecycleResponse:
    return LifecycleResponse.model_validate_json(json.dumps(_lifecycle_body()))


def _lifecycle_body() -> dict[str, object]:
    return {
        "world_id": "00000000-0000-4000-8000-000000000001",
        "revision": 2,
        "simulation_time_seconds": 15,
        "rule_package": {
            "package_id": "greybridge-rules",
            "package_version": "0.2.0",
        },
        "scenario_package": {
            "package_id": "storm-at-greybridge",
            "package_version": "0.2.0",
        },
    }


def _turn() -> TurnResponse:
    return TurnResponse.model_validate_json(json.dumps(_turn_body()))


def _turn_body() -> dict[str, object]:
    return {
        "world_id": "00000000-0000-4000-8000-000000000001",
        "resulting_world_revision": 3,
        "simulation_step_id": "00000000-0000-4000-8000-000000000002",
        "outcome_status": "failed",
        "reason_code": "destination-blocked",
        "current_perception": {
            "observer_id": "player",
            "perceived_at_seconds": 18,
            "observations": [
                {
                    "observation_type": "location",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 18,
                    "location_id": "bridge",
                },
                {
                    "observation_type": "connection",
                    "source_type": "current_state",
                    "observer_id": "player",
                    "observed_at_seconds": 18,
                    "connection_id": "north-road",
                    "is_available": True,
                },
            ],
        },
        "self_event_feedback": [
            {
                "observation_type": "event",
                "source_type": "canonical_event",
                "observer_id": "player",
                "observed_at_seconds": 18,
                "event": {
                    "event_type": "actor_waited",
                    "event_id": "00000000-0000-4000-8000-000000000003",
                    "outcome_id": "00000000-0000-4000-8000-000000000004",
                    "occurred_at_seconds": 18,
                    "actor_id": "player",
                    "duration_seconds": 3,
                },
            }
        ],
    }
