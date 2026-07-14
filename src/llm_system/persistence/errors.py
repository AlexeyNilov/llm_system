class PersistenceError(Exception):
    pass


class UnsupportedSchemaVersionError(PersistenceError):
    def __init__(self, version: int) -> None:
        super().__init__(f"unsupported SQLite schema version: {version}")
        self.version = version


class UnsupportedPayloadSchemaVersionError(PersistenceError):
    def __init__(self, version: int) -> None:
        super().__init__(f"unsupported stored-world payload schema version: {version}")
        self.version = version


class StoredRecordDecodingError(PersistenceError):
    pass


class ExistingWorldError(PersistenceError):
    pass


class MissingWorldError(PersistenceError):
    pass


class WorldIdentityMismatchError(PersistenceError):
    pass


class StaleWorldRevisionError(PersistenceError):
    pass


class WorldRevisionMismatchError(PersistenceError):
    pass


class DuplicateEventIdentityError(PersistenceError):
    pass


class DuplicateSimulationStepIdentityError(PersistenceError):
    pass


class DuplicatePlayerInputIdentityError(PersistenceError):
    pass


class UnitOfWorkFailedError(PersistenceError):
    pass
