# SPDX-FileCopyrightText: 2025 Cline (AI Agent)
#
# SPDX-License-Identifier: MIT

"""
Client for interacting with the ElevenLabs API to generate sound effects.
"""

import time
import random
import logging
from typing import ClassVar

from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError as ElevenLabsSDKAPIError # Corrected import and casing

from .exceptions import (
    ElevenLabsSFXError,
    ElevenLabsAPIKeyError,
    ElevenLabsRateLimitError,
    ElevenLabsPermissionError,
    ElevenLabsGenerationError,
    ElevenLabsParameterError,
    ElevenLabsAPIError # General API error from our exceptions
)

# Configure a logger for internal library use
# Consumers of the library can configure this logger if they wish to see logs.
# By default, it will not produce output unless a handler is added.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler()) # Add NullHandler to prevent "No handler found" warnings

class ElevenLabsSFXClient:
    """
    A client for generating sound effects using the ElevenLabs API.

    This client handles API key management, parameter validation, API calls,
    error handling, and automatic retries for transient issues.
    """

    DEFAULT_MAX_RETRIES: ClassVar[int] = 3
    DEFAULT_BACKOFF_FACTOR: ClassVar[float] = 1.0  # seconds
    DEFAULT_DURATION_SECONDS: ClassVar[float] = 5.0
    DEFAULT_PROMPT_INFLUENCE: ClassVar[float] = 0.3
    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "mp3_44100_128"

    MIN_DURATION: ClassVar[float] = 0.5
    MAX_DURATION: ClassVar[float] = 22.0
    MIN_INFLUENCE: ClassVar[float] = 0.0
    MAX_INFLUENCE: ClassVar[float] = 1.0

    def __init__(
        self,
        api_key: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    ):
        """
        Initializes the ElevenLabsSFXClient.

        Args:
            api_key: Your ElevenLabs API key.
            max_retries: Maximum number of retries for transient API errors.
            backoff_factor: Base factor for calculating exponential backoff delay.

        Raises:
            ElevenLabsParameterError: If the API key is empty.
        """
        if not api_key:
            raise ElevenLabsParameterError("API key cannot be empty.")
        
        self.client = ElevenLabs(api_key=api_key)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        logger.info("ElevenLabsSFXClient initialized.")

    def generate_sound_effect(
        self,
        text: str,
        duration_seconds: float = DEFAULT_DURATION_SECONDS,
        prompt_influence: float = DEFAULT_PROMPT_INFLUENCE,
        output_format: str = DEFAULT_OUTPUT_FORMAT
    ) -> bytes:
        """
        Generates a sound effect based on the provided text prompt.

        Args:
            text: The text prompt describing the sound effect.
            duration_seconds: The desired duration of the sound effect in seconds.
                              Must be between 0.5 and 22.0. Defaults to 5.0.
            prompt_influence: Controls how much the prompt influences generation (0.0 to 1.0).
                              Defaults to 0.3.
            output_format: The desired audio output format.
                           Defaults to "mp3_44100_128".

        Returns:
            The raw audio data as bytes.

        Raises:
            ElevenLabsParameterError: If input parameters are invalid.
            ElevenLabsAPIKeyError: If the API key is invalid or authentication fails.
            ElevenLabsRateLimitError: If API rate limits are exceeded.
            ElevenLabsPermissionError: If the API key lacks necessary permissions.
            ElevenLabsGenerationError: For other errors during sound generation.
            ElevenLabsSFXError: For unexpected errors within the library.
        """
        logger.debug(
            "generate_sound_effect called with text: '%s...', duration: %s, influence: %s, format: %s",
            text[:50] if text else "", duration_seconds, prompt_influence, output_format
        )

        # 1. Parameter Validation
        if not (self.MIN_DURATION <= duration_seconds <= self.MAX_DURATION):
            msg = f"Duration must be between {self.MIN_DURATION} and {self.MAX_DURATION} seconds, got {duration_seconds}."
            logger.error(msg)
            raise ElevenLabsParameterError(msg)
        if not (self.MIN_INFLUENCE <= prompt_influence <= self.MAX_INFLUENCE):
            msg = f"Prompt influence must be between {self.MIN_INFLUENCE} and {self.MAX_INFLUENCE}, got {prompt_influence}."
            logger.error(msg)
            raise ElevenLabsParameterError(msg)
        if not text or not text.strip():
            msg = "Text prompt cannot be empty or whitespace only."
            logger.error(msg)
            raise ElevenLabsParameterError(msg)

        # 2. Retry Loop & API Call
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    "Attempting to generate sound effect (attempt %d/%d) for text: '%s...'",
                    attempt + 1, self.max_retries + 1, text[:50]
                )
                audio_bytes = self.client.text_to_sound_effects.convert(
                    text=text,
                    duration_seconds=duration_seconds,
                    prompt_influence=prompt_influence,
                    output_format=output_format
                )
                # The convert method returns a generator, consume it to get bytes
                # and to ensure any exceptions during generation are raised here.
                consumed_audio_bytes = b"".join(audio_bytes)
                logger.info("Sound effect generated successfully after %d attempt(s).", attempt + 1)
                return consumed_audio_bytes
            
            except ElevenLabsSDKAPIError as e:
                # The SDK's APIError has status_code and body (which might contain more details)
                status_code = e.status_code
                error_message = str(e)
                if e.body and isinstance(e.body, dict) and "detail" in e.body:
                    if isinstance(e.body["detail"], dict) and "message" in e.body["detail"]:
                         error_message = e.body["detail"]["message"]
                    elif isinstance(e.body["detail"], str):
                         error_message = e.body["detail"]
                
                logger.warning(
                    "ElevenLabs SDK APIError encountered (status: %s, attempt %d/%d): %s",
                    status_code, attempt + 1, self.max_retries + 1, error_message,
                    exc_info=True # Log traceback for SDK errors
                )

                if status_code == 401:
                    raise ElevenLabsAPIKeyError(message=f"Invalid API key or authentication failed: {error_message}", status_code=status_code, original_error=e) from e
                
                if status_code == 403:
                    raise ElevenLabsPermissionError(message=f"Permission denied. API key may lack permissions: {error_message}", status_code=status_code, original_error=e) from e

                if status_code == 429: # Rate limit
                    if attempt < self.max_retries:
                        sleep_duration = (self.backoff_factor * (2 ** attempt)) + random.uniform(0, 0.1 * (self.backoff_factor * (2 ** attempt)))
                        logger.warning("Rate limit hit. Retrying in %.2f seconds...", sleep_duration)
                        time.sleep(sleep_duration)
                        continue
                    raise ElevenLabsRateLimitError(message=f"Rate limit exceeded after {self.max_retries + 1} attempts: {error_message}", status_code=status_code, original_error=e) from e
                
                if status_code == 400: # Bad request (e.g., invalid prompt, unsupported parameters by API)
                    # This might also be caught by parameter validation, but API can have stricter rules
                    raise ElevenLabsGenerationError(message=f"Bad request to API (e.g., invalid prompt or parameters): {error_message}", status_code=status_code, original_error=e) from e

                if status_code and status_code >= 500: # Server-side errors
                    if attempt < self.max_retries:
                        sleep_duration = (self.backoff_factor * (2 ** attempt)) + random.uniform(0, 0.1 * (self.backoff_factor * (2 ** attempt)))
                        logger.warning("Server error (%s). Retrying in %.2f seconds...", status_code, sleep_duration)
                        time.sleep(sleep_duration)
                        continue
                    raise ElevenLabsGenerationError(message=f"Server error ({status_code}) after {self.max_retries + 1} attempts: {error_message}", status_code=status_code, original_error=e) from e
                
                # Fallback for other client-side API errors from the SDK not explicitly handled above
                raise ElevenLabsAPIError(message=f"Unhandled API error from ElevenLabs SDK (status: {status_code}): {error_message}", status_code=status_code, original_error=e) from e

            except Exception as e: # Catch-all for unexpected errors (e.g., network issues not caught by SDK, etc.)
                logger.error("An unexpected error occurred during sound effect generation: %s", str(e), exc_info=True)
                # Wrap in a generic library error if it's not already one of ours
                if not isinstance(e, ElevenLabsSFXError):
                    raise ElevenLabsSFXError(f"An unexpected error occurred: {str(e)}") from e
                raise # Re-raise if it's already one of our specific errors

        # This line should ideally not be reached if retry logic is correct and exceptions are raised.
        # Adding it for robustness in case of an unexpected loop exit.
        msg = f"Failed to generate sound effect after {self.max_retries + 1} attempts due to persistent errors."
        logger.error(msg)
        raise ElevenLabsGenerationError(msg, status_code=None) # No specific status code if loop exhausted
