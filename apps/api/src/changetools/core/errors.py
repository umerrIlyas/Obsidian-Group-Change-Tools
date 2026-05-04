"""Domain exception types — translated to HTTP responses by api/exception_handlers.py."""

from __future__ import annotations


class ChangeToolsError(Exception):
    """Base for all domain exceptions."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code


class NotFoundError(ChangeToolsError):
    status_code = 404
    code = "not_found"


class ValidationError(ChangeToolsError):
    status_code = 400
    code = "validation_error"


class ConfigurationError(ChangeToolsError):
    """Raised when required configuration is missing (e.g. an LLM API key)."""

    status_code = 500
    code = "configuration_error"


class ProviderError(ChangeToolsError):
    """Raised when an external provider (LLM, embeddings, storage) fails."""

    status_code = 502
    code = "provider_error"
