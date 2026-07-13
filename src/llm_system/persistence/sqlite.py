from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path
from types import TracebackType
from typing import Literal, Self
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from llm_system.persistence.errors import (
    DuplicateEventIdentityError,
    DuplicateSimulationStepIdentityError,
    ExistingWorldError,
    MissingWorldError,
    StaleWorldRevisionError,
    StoredRecordDecodingError,
    UnitOfWorkFailedError,
    UnsupportedPayloadSchemaVersionError,
    UnsupportedSchemaVersionError,
    WorldIdentityMismatchError,
    WorldRevisionMismatchError,
)
from llm_system.persistence.records import (
    PackageReference,
    StoredCanonicalEvent,
    StoredActorActionStepTrace,
    StoredWorld,
)
from llm_system.simulation.events import CanonicalEvent
from llm_system.simulation.scheduling import ScheduledActivityQueue
from llm_system.simulation.state import WorldState
from llm_system.simulation.traces import CompletedActorActionStepTrace

SQLITE_SCHEMA_VERSION = 2
WORLD_PAYLOAD_SCHEMA_VERSION: Literal[1] = 1

_CANONICAL_EVENT_ADAPTER: TypeAdapter[CanonicalEvent] = TypeAdapter(CanonicalEvent)

_SCHEMA_V1 = (
    """
CREATE TABLE current_world (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    payload_schema_version INTEGER NOT NULL,
    world_id TEXT NOT NULL UNIQUE,
    revision INTEGER NOT NULL CHECK (revision >= 0),
    rule_package_id TEXT NOT NULL,
    rule_package_version TEXT NOT NULL,
    scenario_package_id TEXT NOT NULL,
    scenario_package_version TEXT NOT NULL,
    state_json TEXT NOT NULL,
    scheduled_queue_json TEXT NOT NULL
)
""",
    """
CREATE TABLE canonical_events (
    insertion_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,
    resulting_world_revision INTEGER NOT NULL CHECK (resulting_world_revision >= 0),
    event_id TEXT NOT NULL UNIQUE,
    outcome_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at_seconds INTEGER NOT NULL CHECK (occurred_at_seconds >= 0),
    event_json TEXT NOT NULL
)
    """,
)

_TRACE_SCHEMA_V2 = """
CREATE TABLE simulation_step_traces (
    insertion_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,
    resulting_world_revision INTEGER NOT NULL CHECK (resulting_world_revision >= 0),
    simulation_step_id TEXT NOT NULL UNIQUE,
    outcome_id TEXT NOT NULL,
    outcome_status TEXT NOT NULL CHECK (outcome_status IN ('rejected', 'failed', 'succeeded')),
    trace_json TEXT NOT NULL
)
"""

_SCHEMA_V2 = (*_SCHEMA_V1, _TRACE_SCHEMA_V2)


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    @classmethod
    def open(cls, path: str | Path) -> Self:
        database_path = Path(path)
        connection = sqlite3.connect(database_path, isolation_level=None)
        try:
            version = _schema_version(connection)
            if version not in (0, 1, SQLITE_SCHEMA_VERSION):
                raise UnsupportedSchemaVersionError(version)
            if version == 0:
                existing_table = connection.execute(
                    """
                    SELECT 1 FROM sqlite_master
                    WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                    LIMIT 1
                    """
                ).fetchone()
                if existing_table is not None:
                    raise UnsupportedSchemaVersionError(version)
                connection.execute("BEGIN IMMEDIATE")
                try:
                    for statement in _SCHEMA_V2:
                        connection.execute(statement)
                    connection.execute(f"PRAGMA user_version = {SQLITE_SCHEMA_VERSION}")
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
            elif version == 1:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(_TRACE_SCHEMA_V2)
                    connection.execute(f"PRAGMA user_version = {SQLITE_SCHEMA_VERSION}")
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
        finally:
            connection.close()
        return cls(database_path)

    def unit_of_work(self) -> SQLiteUnitOfWork:
        return SQLiteUnitOfWork(self._path)


class SQLiteUnitOfWork:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._connection: sqlite3.Connection | None = None
        self._committed = False
        self._failed = False
        self.worlds: SQLiteWorldRepository
        self.events: SQLiteEventRepository
        self.traces: SQLiteTraceRepository

    def __enter__(self) -> Self:
        if self._connection is not None:
            raise RuntimeError("unit of work cannot be entered more than once")
        connection = sqlite3.connect(self._path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        self._connection = connection
        self.worlds = SQLiteWorldRepository(
            connection, self._mark_failed, self._require_active_transaction
        )
        self.events = SQLiteEventRepository(
            connection, self._mark_failed, self._require_active_transaction
        )
        self.traces = SQLiteTraceRepository(
            connection, self._mark_failed, self._require_active_transaction
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        connection = self._require_connection()
        try:
            if not self._committed:
                connection.rollback()
        finally:
            connection.close()

    def commit(self) -> None:
        connection = self._require_connection()
        if self._failed:
            connection.rollback()
            raise UnitOfWorkFailedError("cannot commit a failed unit of work")
        connection.commit()
        self._committed = True

    def clear_world_timeline_for_development(self) -> None:
        self._require_active_transaction()
        connection = self._require_connection()
        current = connection.execute(
            "SELECT 1 FROM current_world WHERE singleton = 1"
        ).fetchone()
        if current is None:
            self._mark_failed()
            raise MissingWorldError("the singleton world does not exist")
        try:
            connection.execute("DELETE FROM simulation_step_traces")
            connection.execute("DELETE FROM canonical_events")
            connection.execute("DELETE FROM current_world WHERE singleton = 1")
        except sqlite3.DatabaseError:
            self._mark_failed()
            raise

    def _mark_failed(self) -> None:
        self._failed = True

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("unit of work has not been entered")
        return self._connection

    def _require_active_transaction(self) -> None:
        connection = self._require_connection()
        if self._committed or not connection.in_transaction:
            raise RuntimeError("unit of work transaction is no longer active")


class SQLiteWorldRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
        mark_failed: Callable[[], None],
        require_active: Callable[[], None],
    ) -> None:
        self._connection = connection
        self._mark_failed = mark_failed
        self._require_active = require_active

    def get(self) -> StoredWorld | None:
        self._require_active()
        row = self._connection.execute(
            """
            SELECT payload_schema_version, world_id, revision,
                   rule_package_id, rule_package_version,
                   scenario_package_id, scenario_package_version,
                   state_json, scheduled_queue_json
            FROM current_world
            WHERE singleton = 1
            """
        ).fetchone()
        if row is None:
            return None
        try:
            return _decode_world(row)
        except (StoredRecordDecodingError, UnsupportedPayloadSchemaVersionError):
            self._mark_failed()
            raise

    def create(
        self,
        *,
        world_id: UUID,
        rule_package: PackageReference,
        scenario_package: PackageReference,
        state: WorldState,
        scheduled_queue: ScheduledActivityQueue,
    ) -> StoredWorld:
        self._require_active()
        world = StoredWorld(
            payload_schema_version=WORLD_PAYLOAD_SCHEMA_VERSION,
            world_id=world_id,
            revision=0,
            rule_package=rule_package,
            scenario_package=scenario_package,
            state=state,
            scheduled_queue=scheduled_queue,
        )
        try:
            self._connection.execute(
                """
                INSERT INTO current_world (
                    singleton, payload_schema_version, world_id, revision,
                    rule_package_id, rule_package_version,
                    scenario_package_id, scenario_package_version,
                    state_json, scheduled_queue_json
                ) VALUES (1, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                """,
                (
                    world.payload_schema_version,
                    str(world.world_id),
                    world.rule_package.package_id,
                    world.rule_package.package_version,
                    world.scenario_package.package_id,
                    world.scenario_package.package_version,
                    world.state.model_dump_json(),
                    world.scheduled_queue.model_dump_json(),
                ),
            )
        except sqlite3.IntegrityError as error:
            self._mark_failed()
            raise ExistingWorldError("the singleton world already exists") from error
        return world

    def replace(
        self,
        *,
        world_id: UUID,
        expected_revision: int,
        state: WorldState,
        scheduled_queue: ScheduledActivityQueue,
    ) -> StoredWorld:
        self._require_active()
        current = self.get()
        if current is None:
            self._mark_failed()
            raise MissingWorldError("the singleton world does not exist")
        if current.world_id != world_id:
            self._mark_failed()
            raise WorldIdentityMismatchError(
                "world identity does not match current world"
            )
        if current.revision != expected_revision:
            self._mark_failed()
            raise StaleWorldRevisionError(
                f"expected world revision {expected_revision}, found {current.revision}"
            )
        next_revision = current.revision + 1
        cursor = self._connection.execute(
            """
            UPDATE current_world
            SET revision = ?, state_json = ?, scheduled_queue_json = ?
            WHERE singleton = 1 AND world_id = ? AND revision = ?
            """,
            (
                next_revision,
                state.model_dump_json(),
                scheduled_queue.model_dump_json(),
                str(world_id),
                expected_revision,
            ),
        )
        if cursor.rowcount != 1:
            self._mark_failed()
            raise StaleWorldRevisionError("current world changed during replacement")
        return current.model_copy(
            update={
                "revision": next_revision,
                "state": state,
                "scheduled_queue": scheduled_queue,
            }
        )


class SQLiteEventRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
        mark_failed: Callable[[], None],
        require_active: Callable[[], None],
    ) -> None:
        self._connection = connection
        self._mark_failed = mark_failed
        self._require_active = require_active

    def append(
        self,
        *,
        world_id: UUID,
        resulting_world_revision: int,
        events: Sequence[CanonicalEvent],
    ) -> tuple[StoredCanonicalEvent, ...]:
        self._require_active()
        current = self._connection.execute(
            "SELECT world_id, revision FROM current_world WHERE singleton = 1"
        ).fetchone()
        if current is None:
            self._mark_failed()
            raise MissingWorldError("the singleton world does not exist")
        if current["world_id"] != str(world_id):
            self._mark_failed()
            raise WorldIdentityMismatchError("event world does not match current world")
        if current["revision"] != resulting_world_revision:
            self._mark_failed()
            raise WorldRevisionMismatchError(
                "events must be associated with the current resulting world revision"
            )

        stored: list[StoredCanonicalEvent] = []
        try:
            for event in events:
                cursor = self._connection.execute(
                    """
                    INSERT INTO canonical_events (
                        world_id, resulting_world_revision, event_id, outcome_id,
                        event_type, occurred_at_seconds, event_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(world_id),
                        resulting_world_revision,
                        str(event.event_id),
                        str(event.outcome_id),
                        event.event_type,
                        event.occurred_at_seconds,
                        _CANONICAL_EVENT_ADAPTER.dump_json(event).decode(),
                    ),
                )
                insertion_sequence = cursor.lastrowid
                assert insertion_sequence is not None
                stored.append(
                    StoredCanonicalEvent(
                        insertion_sequence=insertion_sequence,
                        world_id=world_id,
                        resulting_world_revision=resulting_world_revision,
                        event=event,
                    )
                )
        except sqlite3.IntegrityError as error:
            self._mark_failed()
            raise DuplicateEventIdentityError(
                "canonical event identity already exists"
            ) from error
        return tuple(stored)

    def list_for_world(self, world_id: UUID) -> tuple[StoredCanonicalEvent, ...]:
        self._require_active()
        rows = self._connection.execute(
            """
            SELECT insertion_sequence, world_id, resulting_world_revision,
                   event_id, outcome_id, event_type, occurred_at_seconds, event_json
            FROM canonical_events
            WHERE world_id = ?
            ORDER BY insertion_sequence
            """,
            (str(world_id),),
        ).fetchall()
        try:
            return tuple(_decode_event(row) for row in rows)
        except StoredRecordDecodingError:
            self._mark_failed()
            raise


class SQLiteTraceRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
        mark_failed: Callable[[], None],
        require_active: Callable[[], None],
    ) -> None:
        self._connection = connection
        self._mark_failed = mark_failed
        self._require_active = require_active

    def append(
        self,
        *,
        world_id: UUID,
        resulting_world_revision: int,
        trace: CompletedActorActionStepTrace,
    ) -> StoredActorActionStepTrace:
        self._require_active()
        current = self._connection.execute(
            "SELECT world_id, revision FROM current_world WHERE singleton = 1"
        ).fetchone()
        if current is None:
            self._mark_failed()
            raise MissingWorldError("the singleton world does not exist")
        if current["world_id"] != str(world_id):
            self._mark_failed()
            raise WorldIdentityMismatchError("trace world does not match current world")
        if current["revision"] != resulting_world_revision:
            self._mark_failed()
            raise WorldRevisionMismatchError(
                "trace must be associated with the current resulting world revision"
            )
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO simulation_step_traces (
                    world_id, resulting_world_revision, simulation_step_id,
                    outcome_id, outcome_status, trace_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(world_id),
                    resulting_world_revision,
                    str(trace.simulation_step_id),
                    str(trace.outcome.outcome_id),
                    trace.outcome.status,
                    trace.model_dump_json(),
                ),
            )
        except sqlite3.IntegrityError as error:
            self._mark_failed()
            raise DuplicateSimulationStepIdentityError(
                "simulation step identity already exists"
            ) from error
        insertion_sequence = cursor.lastrowid
        assert insertion_sequence is not None
        return StoredActorActionStepTrace(
            insertion_sequence=insertion_sequence,
            world_id=world_id,
            resulting_world_revision=resulting_world_revision,
            trace=trace,
        )

    def list_for_world(self, world_id: UUID) -> tuple[StoredActorActionStepTrace, ...]:
        self._require_active()
        rows = self._connection.execute(
            """
            SELECT insertion_sequence, world_id, resulting_world_revision,
                   simulation_step_id, outcome_id, outcome_status, trace_json
            FROM simulation_step_traces
            WHERE world_id = ?
            ORDER BY insertion_sequence
            """,
            (str(world_id),),
        ).fetchall()
        try:
            return tuple(_decode_trace(row) for row in rows)
        except StoredRecordDecodingError:
            self._mark_failed()
            raise


def _schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("PRAGMA user_version").fetchone()
    assert row is not None
    return int(row[0])


def _decode_world(row: sqlite3.Row) -> StoredWorld:
    payload_schema_version = row["payload_schema_version"]
    if payload_schema_version != WORLD_PAYLOAD_SCHEMA_VERSION:
        raise UnsupportedPayloadSchemaVersionError(payload_schema_version)
    try:
        return StoredWorld(
            payload_schema_version=payload_schema_version,
            world_id=UUID(row["world_id"]),
            revision=row["revision"],
            rule_package=PackageReference(
                package_id=row["rule_package_id"],
                package_version=row["rule_package_version"],
            ),
            scenario_package=PackageReference(
                package_id=row["scenario_package_id"],
                package_version=row["scenario_package_version"],
            ),
            state=WorldState.model_validate_json(row["state_json"]),
            scheduled_queue=ScheduledActivityQueue.model_validate_json(
                row["scheduled_queue_json"]
            ),
        )
    except (TypeError, ValueError, ValidationError) as error:
        raise StoredRecordDecodingError("invalid stored-world record") from error


def _decode_event(row: sqlite3.Row) -> StoredCanonicalEvent:
    try:
        event = _CANONICAL_EVENT_ADAPTER.validate_json(row["event_json"])
        if (
            str(event.event_id) != row["event_id"]
            or str(event.outcome_id) != row["outcome_id"]
            or event.event_type != row["event_type"]
            or event.occurred_at_seconds != row["occurred_at_seconds"]
        ):
            raise ValueError("explicit event metadata does not match event payload")
        return StoredCanonicalEvent(
            insertion_sequence=row["insertion_sequence"],
            world_id=UUID(row["world_id"]),
            resulting_world_revision=row["resulting_world_revision"],
            event=event,
        )
    except (TypeError, ValueError, ValidationError) as error:
        raise StoredRecordDecodingError("invalid stored canonical event") from error


def _decode_trace(row: sqlite3.Row) -> StoredActorActionStepTrace:
    try:
        trace = CompletedActorActionStepTrace.model_validate_json(row["trace_json"])
        if (
            str(trace.simulation_step_id) != row["simulation_step_id"]
            or str(trace.outcome.outcome_id) != row["outcome_id"]
            or trace.outcome.status != row["outcome_status"]
        ):
            raise ValueError("explicit trace metadata does not match trace payload")
        return StoredActorActionStepTrace(
            insertion_sequence=row["insertion_sequence"],
            world_id=UUID(row["world_id"]),
            resulting_world_revision=row["resulting_world_revision"],
            trace=trace,
        )
    except (TypeError, ValueError, ValidationError) as error:
        raise StoredRecordDecodingError("invalid stored actor-action trace") from error
