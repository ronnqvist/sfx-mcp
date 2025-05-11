# SPDX-FileCopyrightText: 2025 Cline (AI Agent)
#
# SPDX-License-Identifier: MIT

"""
Custom exceptions for the elevenlabs-sfx library.
"""

class ElevenLabsSFXError(Exception):
    """Base exception for all elevenlabs-sfx specific errors."""
    pass

class ElevenLabsParameterError(ValueError, ElevenLabsSFXError):
    """
    Raised when invalid parameters are provided to a library function.
    Inherits from ValueError for broad compatibility with parameter validation checks.
    """
    pass

class ElevenLabsAPIError(ElevenLabsSFXError):
    """
    Base exception for errors originating from the ElevenLabs API.
    This can be used to catch all API-related issues from this library.
    """
    def __init__(self, message: str, status_code: int | None = None, original_error: Exception | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.original_error = original_error

    def __str__(self):
        if self.status_code:
            return f"(Status {self.status_code}) {super().__str__()}"
        return super().__str__()

class ElevenLabsAPIKeyError(ElevenLabsAPIError):
    """
    Raised specifically for API authentication errors (e.g., HTTP 401 Unauthorized).
    Indicates an issue with the provided API key.
    """
    def __init__(self, message: str = "Invalid API key or authentication failed.", status_code: int = 401, original_error: Exception | None = None):
        super().__init__(message, status_code, original_error)

class ElevenLabsRateLimitError(ElevenLabsAPIError):
    """
    Raised when the ElevenLabs API rate limits are exceeded (e.g., HTTP 429 Too Many Requests).
    """
    def __init__(self, message: str = "API rate limit exceeded.", status_code: int = 429, original_error: Exception | None = None):
        super().__init__(message, status_code, original_error)

class ElevenLabsPermissionError(ElevenLabsAPIError):
    """
    Raised for permission-related errors (e.g., HTTP 403 Forbidden).
    Indicates the API key may not have the required permissions for the operation.
    """
    def __init__(self, message: str = "Permission denied. The API key may lack necessary permissions.", status_code: int = 403, original_error: Exception | None = None):
        super().__init__(message, status_code, original_error)

class ElevenLabsGenerationError(ElevenLabsAPIError):
    """
    Raised for general errors during the sound generation process not covered by
    more specific API exceptions like key, rate limit, or permission errors.
    This can include bad requests (e.g., HTTP 400) or server-side errors (e.g., HTTP 5xx).
    """
    pass
