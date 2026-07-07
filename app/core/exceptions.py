"""
Custom exceptions for the application.

Purpose: Define application-specific exception hierarchy.
Responsibility: Provide meaningful error context and HTTP mapping.
"""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        """Initialize application error.

        Args:
            message: Error message
            error_code: Application-specific error code
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class LLMError(ApplicationError):
    """Raised when LLM API call fails."""

    def __init__(self, message: str):
        """Initialize LLM error."""
        super().__init__(message, error_code="LLM_ERROR")


class PlanningError(ApplicationError):
    """Raised when planning agent fails."""

    def __init__(self, message: str):
        """Initialize planning error."""
        super().__init__(message, error_code="PLANNING_ERROR")


class ExecutionError(ApplicationError):
    """Raised when execution agent fails."""

    def __init__(self, message: str):
        """Initialize execution error."""
        super().__init__(message, error_code="EXECUTION_ERROR")


class ValidationError(ApplicationError):
    """Raised when validation fails."""

    def __init__(self, message: str):
        """Initialize validation error."""
        super().__init__(message, error_code="VALIDATION_ERROR")


class DocumentGenerationError(ApplicationError):
    """Raised when document generation fails."""

    def __init__(self, message: str):
        """Initialize document generation error."""
        super().__init__(message, error_code="DOCUMENT_ERROR")


class ReflectionError(ApplicationError):
    """Raised when reflection agent fails."""

    def __init__(self, message: str):
        """Initialize reflection error."""
        super().__init__(message, error_code="REFLECTION_ERROR")


class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str):
        """Initialize configuration error."""
        super().__init__(message, error_code="CONFIG_ERROR")


class TemplateError(ApplicationError):
    """Raised when template loading/processing fails."""

    def __init__(self, message: str):
        """Initialize template error."""
        super().__init__(message, error_code="TEMPLATE_ERROR")
