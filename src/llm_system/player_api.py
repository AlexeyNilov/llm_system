from typing import Literal, Protocol, cast

import httpx2
from pydantic import ValidationError

from llm_system.api import ApplicationErrorResponse, LifecycleResponse, TurnResponse
from llm_system.simulation.actions import ActorActionProposal


class PlayerApi(Protocol):
    def create_world(self) -> LifecycleResponse: ...

    def resume_world(self) -> LifecycleResponse: ...

    def reset_world(self) -> LifecycleResponse: ...

    def take_turn(self, proposal: ActorActionProposal) -> TurnResponse: ...


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

    def take_turn(self, proposal: ActorActionProposal) -> TurnResponse:
        return self._request(
            "POST",
            "/turn",
            TurnResponse,
            json={"proposal": proposal.model_dump(mode="json")},
        )

    def _request[ResponseModel: LifecycleResponse | TurnResponse](
        self,
        method: Literal["GET", "POST"],
        path: str,
        response_model: type[ResponseModel],
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
                return cast(
                    ResponseModel,
                    response_model.model_validate_json(response.content),
                )
            except (ValidationError, ValueError) as error:
                raise SafeClientError("malformed-response") from error

        mapped_codes = {
            403: "development-reset-disabled",
            404: "world-not-found",
            409: "world-already-exists",
        }
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
