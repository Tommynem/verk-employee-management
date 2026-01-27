"""Domain exceptions for Verk application with German error messages."""


class VerkException(Exception):
    """Base exception for Verk application."""

    pass


class NotFoundError(VerkException):
    """Raised when a requested resource is not found.

    Args:
        resource: Type of resource (e.g., "Rechnung", "Kasseneintrag")
        id: Identifier of the missing resource

    Example:
        raise NotFoundError("Rechnung", 123)
        # Message: "Rechnung mit ID 123 nicht gefunden"
    """

    def __init__(self, resource: str, id: int | str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} mit ID {id} nicht gefunden")


class ValidationError(VerkException):
    """Raised when validation fails.

    Example:
        raise ValidationError("Betrag muss positiv sein")
    """

    pass
