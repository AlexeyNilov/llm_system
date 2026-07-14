from typing import Literal, Protocol, cast

import httpx2
from pydantic import TypeAdapter, ValidationError

from llm_system.api import (
    ApplicationErrorResponse,
    LifecycleResponse,
    PlayerTurnResponse,
)


class PlayerApi(Protocol):
    def create_world(self) -> LifecycleResponse: ...

    def resume_world(self) -> LifecycleResponse: ...

    def reset_world(self) -> LifecycleResponse: ...

    def take_player_turn(self, player_text: str) -> PlayerTurnResponse: ...


class PlayerApiError(Exception):
    pass


class ApplicationApiError(PlayerApiError):
    def __init__(self, *, status_code: int, code: str) -> None:
        super().__init__(f"API request failed ({status_code}, {code})")
        self.status_code = status_code
        self.code = code


ClientFailureKind = Literal[
    "transport-unavailable", "malformed-response", "unexpected-response"
]


class SafeClientError(PlayerApiError):
    def __init__(self, kind: ClientFailureKind) -> None:
        super().__init__(kind)
        self.kind = kind


class HttpPlayerApi:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        client: httpx2.Client | None = None,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        if client is not None and transport is not None:
            raise ValueError("client and transport cannot both be provided")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._owns_client = client is None
        self._client = (
            client if client is not None else httpx2.Client(transport=transport)
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create_world(self) -> LifecycleResponse:
        return self._request("POST", "/world", LifecycleResponse)

    def resume_world(self) -> LifecycleResponse:
        return self._request("GET", "/world", LifecycleResponse)

    def reset_world(self) -> LifecycleResponse:
        return self._request("POST", "/development/reset", LifecycleResponse)

    def take_player_turn(self, player_text: str) -> PlayerTurnResponse:
        return self._request(
            "POST",
            "/player-turn",
            _PLAYER_TURN_RESPONSE_ADAPTER,
            json={"player_text": player_text},
        )

    def _request[ResponseModel: LifecycleResponse | PlayerTurnResponse](
        self,
        method: Literal["GET", "POST"],
        path: str,
        response_model: type[ResponseModel] | TypeAdapter[ResponseModel],
        *,
        json: object | None = None,
    ) -> ResponseModel:
        try:
            if json is None:
                response = self._client.request(
                    method,
                    f"{self._base_url}{path}",
                    timeout=self._timeout_seconds,
                )
            else:
                response = self._client.request(
                    method,
                    f"{self._base_url}{path}",
                    timeout=self._timeout_seconds,
                    json=json,
                )
        except httpx2.RequestError as error:
            raise SafeClientError("transport-unavailable") from error

        if response.status_code == 200:
            try:
                if isinstance(response_model, TypeAdapter):
                    return response_model.validate_json(response.content)
                return cast(
                    ResponseModel, response_model.model_validate_json(response.content)
                )
            except (ValidationError, ValueError) as error:
                raise SafeClientError("malformed-response") from error

        mapped_codes = {
            403: "development-reset-disabled",
            404: "world-not-found",
            409: "world-already-exists",
        }
        if path == "/player-turn":
            mapped_codes[409] = "player-turn-stale"
        expected_code = mapped_codes.get(response.status_code)
        if expected_code is not None:
            try:
                application_error = ApplicationErrorResponse.model_validate_json(
                    response.content
                )
            except (ValidationError, ValueError) as error:
                raise SafeClientError("malformed-response") from error
            if application_error.code == expected_code:
                raise ApplicationApiError(
                    status_code=response.status_code,
                    code=application_error.code,
                )
        raise SafeClientError("unexpected-response")


_PLAYER_TURN_RESPONSE_ADAPTER: TypeAdapter[PlayerTurnResponse] = TypeAdapter(
    PlayerTurnResponse
)
