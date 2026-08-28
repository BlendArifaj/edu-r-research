class DomainError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    def __init__(self, entity: str, identifier: str | int) -> None:
        super().__init__(f"{entity} not found: {identifier}")
        self.entity = entity
        self.identifier = identifier


class ConflictError(DomainError):
    pass


class AuthorizationError(DomainError):
    pass
