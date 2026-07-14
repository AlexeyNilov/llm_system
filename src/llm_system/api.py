from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal, TypeAlias
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from llm_system.application import (
    ActiveWorld,
    ActionCompletedPlayerTurnResult,
    ClarificationPlayerTurnResult,
    FunctionalGenerationAttempt,
    FunctionalGenerationDisposition,
    FunctionalGenerationResult,
    FunctionalModelFailureKind,
    FunctionalModelGateway,
    ModelMessage,
    StalePlayerTurnResult,
    ThoughtOnlyPlayerTurnResult,
    coordinate_player_turn,
    create_world,
    execute_actor_action_step,
    reset_world_for_development,
    resume_world,
)
from llm_system.game_packages.entities import PlayerCharacterDefinition
from llm_system.game_packages.validation import ValidatedGamePackages
from llm_system.persistence import ExistingWorldError, MissingWorldError, SQLiteStore
from llm_system.persistence.records import NonNegativeRevision, PackageReference
from llm_system.simulation.actions import (
    ActorActionProposal,
    ActorActionSubmission,
    NonBlankText,
    PlayerInterpreterActionSource,
)
from llm_system.simulation.outcomes import OutcomeReasonCode
from llm_system.simulation.perception import EventObserved, PerceptionSnapshot
from llm_system.simulation.state import NonNegativeSeconds


class _StrictApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class LifecycleResponse(_StrictApiModel):
    world_id: UUID
    revision: NonNegativeRevision
    simulation_time_seconds: NonNegativeSeconds
    rule_package: PackageReference
    scenario_package: PackageReference


class TurnRequest(_StrictApiModel):
    proposal: ActorActionProposal


class PlayerTurnRequest(_StrictApiModel):
    player_text: NonBlankText


class TurnResponse(_StrictApiModel):
    world_id: UUID
    resulting_world_revision: NonNegativeRevision
    simulation_step_id: UUID
    outcome_status: Literal["rejected", "failed", "succeeded"]
    reason_code: OutcomeReasonCode
    current_perception: PerceptionSnapshot
    self_event_feedback: tuple[EventObserved, ...]


class ThoughtOnlyPlayerTurnResponse(_StrictApiModel):
    result_type: Literal["thought_only"]
    private_thought: NonBlankText


class ClarificationPlayerTurnResponse(_StrictApiModel):
    result_type: Literal["clarification"]
    clarification: NonBlankText


class ActionCompletedPlayerTurnResponse(TurnResponse):
    result_type: Literal["action_completed"]
    private_thought: NonBlankText | None


PlayerTurnResponse: TypeAlias = Annotated[
    ThoughtOnlyPlayerTurnResponse
    | ClarificationPlayerTurnResponse
    | ActionCompletedPlayerTurnResponse,
    Field(discriminator="result_type"),
]


class ApplicationErrorResponse(_StrictApiModel):
    code: Literal[
        "world-not-found",
        "world-already-exists",
        "development-reset-disabled",
        "player-turn-stale",
    ]


class _UnavailableFunctionalGateway:
    def generate_functional[ResultT: BaseModel](
        self, messages: tuple[ModelMessage, ...], output_model: type[ResultT]
    ) -> FunctionalGenerationResult[ResultT]:
        del messages, output_model
        return FunctionalGenerationResult[ResultT](
            disposition=FunctionalGenerationDisposition.FAILED,
            initial_attempt=FunctionalGenerationAttempt(
                failure_kind=FunctionalModelFailureKind.TRANSPORT_UNAVAILABLE
            ),
        )


def create_app(
    *,
    store: SQLiteStore,
    package_root: Path,
    initial_packages: ValidatedGamePackages,
    identity_factory: Callable[[], UUID] = uuid4,
    development_reset_enabled: bool = False,
    gateway: FunctionalModelGateway | None = None,
) -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    player_turn_gateway: FunctionalModelGateway = (
        gateway if gateway is not None else _UnavailableFunctionalGateway()
    )

    @app.exception_handler(MissingWorldError)
    async def handle_missing_world(
        request: Request, error: MissingWorldError
    ) -> JSONResponse:
        del request, error
        return _error_response(404, "world-not-found")

    @app.post("/world", response_model=LifecycleResponse)
    def post_world() -> LifecycleResponse | JSONResponse:
        try:
            active_world = create_world(
                store, initial_packages, world_id=identity_factory()
            )
        except ExistingWorldError:
            return _error_response(409, "world-already-exists")
        return _lifecycle_response(active_world)

    @app.get("/world", response_model=LifecycleResponse)
    def get_world() -> LifecycleResponse:
        return _lifecycle_response(resume_world(store, package_root))

    @app.post("/development/reset", response_model=LifecycleResponse)
    def post_development_reset() -> LifecycleResponse | JSONResponse:
        if not development_reset_enabled:
            return _error_response(403, "development-reset-disabled")
        active_world = reset_world_for_development(
            store, initial_packages, world_id=identity_factory()
        )
        return _lifecycle_response(active_world)

    @app.post("/turn", response_model=TurnResponse)
    def post_turn(request: TurnRequest) -> TurnResponse:
        active_world = resume_world(store, package_root)
        player = _sole_player(active_world.validated_world.packages)
        proposal_id = identity_factory()
        simulation_step_id = identity_factory()
        decision_context_id = identity_factory()
        outcome_id = identity_factory()
        event_id = identity_factory()
        completed = execute_actor_action_step(
            store,
            active_world.validated_world.packages,
            ActorActionSubmission(
                proposal_id=proposal_id,
                simulation_step_id=simulation_step_id,
                decision_context_id=decision_context_id,
                source=PlayerInterpreterActionSource(
                    source_type="player_interpreter",
                    interpreter_id="structured-api",
                ),
                actor_id=player.id,
                proposal=request.proposal,
            ),
            outcome_id=outcome_id,
            event_id=event_id,
        )
        trace = completed.trace
        return TurnResponse(
            world_id=completed.world_id,
            resulting_world_revision=completed.resulting_world_revision,
            simulation_step_id=trace.simulation_step_id,
            outcome_status=trace.outcome.status,
            reason_code=trace.outcome.reason_code,
            current_perception=trace.current_perception,
            self_event_feedback=trace.self_event_feedback,
        )

    @app.post("/player-turn", response_model=PlayerTurnResponse)
    def post_player_turn(
        request: PlayerTurnRequest,
    ) -> PlayerTurnResponse | JSONResponse:
        player = _sole_player(initial_packages)
        result = coordinate_player_turn(
            store,
            initial_packages,
            player_turn_gateway,
            player_text=request.player_text,
            player_id=player.id,
            identity_factory=identity_factory,
        )
        if isinstance(result, StalePlayerTurnResult):
            return _error_response(409, "player-turn-stale")
        return _player_turn_response(result)

    return app


def _lifecycle_response(active_world: ActiveWorld) -> LifecycleResponse:
    stored = active_world.stored_world
    return LifecycleResponse(
        world_id=stored.world_id,
        revision=stored.revision,
        simulation_time_seconds=stored.state.simulation_time_seconds,
        rule_package=stored.rule_package,
        scenario_package=stored.scenario_package,
    )


def _sole_player(packages: ValidatedGamePackages) -> PlayerCharacterDefinition:
    players = tuple(
        entity
        for entity in packages.scenario_package.definition.entity_collection.entities
        if isinstance(entity, PlayerCharacterDefinition)
    )
    if len(players) != 1:
        raise RuntimeError("validated scenario must contain exactly one player")
    return players[0]


def _player_turn_response(
    result: (
        ThoughtOnlyPlayerTurnResult
        | ClarificationPlayerTurnResult
        | ActionCompletedPlayerTurnResult
    ),
) -> PlayerTurnResponse:
    if isinstance(result, ThoughtOnlyPlayerTurnResult):
        return ThoughtOnlyPlayerTurnResponse(
            result_type="thought_only", private_thought=result.private_thought
        )
    if isinstance(result, ClarificationPlayerTurnResult):
        return ClarificationPlayerTurnResponse(
            result_type="clarification", clarification=result.clarification
        )
    trace = result.completed_action.trace
    return ActionCompletedPlayerTurnResponse(
        result_type="action_completed",
        world_id=result.completed_action.world_id,
        resulting_world_revision=result.completed_action.resulting_world_revision,
        simulation_step_id=trace.simulation_step_id,
        outcome_status=trace.outcome.status,
        reason_code=trace.outcome.reason_code,
        current_perception=trace.current_perception,
        self_event_feedback=trace.self_event_feedback,
        private_thought=result.private_thought,
    )


def _error_response(
    status_code: int,
    code: Literal[
        "world-not-found",
        "world-already-exists",
        "development-reset-disabled",
        "player-turn-stale",
    ],
) -> JSONResponse:
    body = ApplicationErrorResponse(code=code)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
