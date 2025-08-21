class EventProcessingError(Exception):
    """Base exception for event processing errors"""


class DependencyGraphError(EventProcessingError):
    """Raised when dependency graph validation fails"""


class CycleDetectedError(DependencyGraphError):
    """Raised when circular dependencies are detected"""


class DependencyRegistrationError(DependencyGraphError):
    """Raised when handler dependencies are invalid"""


__all__ = [
    "EventProcessingError",
    "DependencyGraphError",
    "CycleDetectedError",
    "DependencyRegistrationError",
]
