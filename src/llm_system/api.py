from collections.abc import Callable
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from llm_system.application import (
    ActiveWorld,
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


class TurnResponse(_StrictApiModel):
    world_id: UUID
    resulting_world_revision: NonNegativeRevision
    simulation_step_id: UUID
    outcome_status: Literal["rejected", "failed", "succeeded"]
    reason_code: OutcomeReasonCode
    current_perception: PerceptionSnapshot
    self_event_feedback: tuple[EventObserved, ...]


class ApplicationErrorResponse(_StrictApiModel):
    code: Literal[
        "world-not-found",
        "world-already-exists",
        "development-reset-disabled",
    ]


def create_app(
    *,
    store: SQLiteStore,
    package_root: Path,
    initial_packages: ValidatedGamePackages,
    identity_factory: Callable[[], UUID] = uuid4,
    development_reset_enabled: bool = False,
) -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

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


def _error_response(
    status_code: int,
    code: Literal[
        "world-not-found",
        "world-already-exists",
        "development-reset-disabled",
    ],
) -> JSONResponse:
    body = ApplicationErrorResponse(code=code)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
