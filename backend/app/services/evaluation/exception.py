class EvaluationError(Exception):
    """Base exception for the evaluation flow."""


class EmptyDatasetError(EvaluationError):
    """Raised when an evaluation run is submitted with no dataset items."""


class InvalidDatasetError(EvaluationError):
    """Raised when a dataset file cannot be parsed into evaluation items."""


class EvaluationRunNotFoundError(EvaluationError):
    """Raised when an evaluation run does not exist in the workspace."""
