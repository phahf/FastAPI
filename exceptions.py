
class DomainError(Exception):
    """Basisklasse für alle fachlichen Fehler."""
    pass


class UserNotFound(DomainError):
    pass


class UserAlreadyExists(DomainError):
    pass


class InvalidPassword(DomainError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class InvalidCurrentPassword(DomainError):
    pass


