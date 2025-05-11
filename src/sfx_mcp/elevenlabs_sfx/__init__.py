# SPDX-FileCopyrightText: 2025 Cline (AI Agent)
#
# SPDX-License-Identifier: MIT

"""
elevenlabs-sfx

A Python library for generating sound effects using the ElevenLabs API.
"""

__version__ = "0.1.0"

from .client import ElevenLabsSFXClient
from .exceptions import (
    ElevenLabsSFXError,
    ElevenLabsAPIError,
    ElevenLabsAPIKeyError,
    ElevenLabsRateLimitError,
    ElevenLabsPermissionError,
    ElevenLabsGenerationError,
    ElevenLabsParameterError
)

__all__ = [
    "ElevenLabsSFXClient",
    "ElevenLabsSFXError",
    "ElevenLabsAPIError",
    "ElevenLabsAPIKeyError",
    "ElevenLabsRateLimitError",
    "ElevenLabsPermissionError",
    "ElevenLabsGenerationError",
    "ElevenLabsParameterError",
    "__version__",
]
