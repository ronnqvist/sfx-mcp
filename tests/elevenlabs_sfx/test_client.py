# SPDX-FileCopyrightText: 2025 Cline (AI Agent)
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the ElevenLabsSFXClient.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, ANY

from elevenlabs.core.api_error import ApiError as ElevenLabsSDKAPIError # Corrected import and casing

from sfx_mcp.elevenlabs_sfx.client import ElevenLabsSFXClient
from sfx_mcp.elevenlabs_sfx.exceptions import (
    ElevenLabsAPIKeyError,
    ElevenLabsParameterError,
    ElevenLabsRateLimitError,
    ElevenLabsPermissionError,
    ElevenLabsGenerationError,
    ElevenLabsAPIError,
    ElevenLabsSFXError,
)

# Constants for tests
MOCK_API_KEY = "test_api_key_123"
VALID_TEXT_PROMPT = "A cat meowing loudly."
DEFAULT_DURATION = ElevenLabsSFXClient.DEFAULT_DURATION_SECONDS
DEFAULT_INFLUENCE = ElevenLabsSFXClient.DEFAULT_PROMPT_INFLUENCE
DEFAULT_FORMAT = ElevenLabsSFXClient.DEFAULT_OUTPUT_FORMAT

@pytest.fixture
def mock_elevenlabs_sdk_client():
    """Mocks the ElevenLabs SDK client instance used by ElevenLabsSFXClient."""
    # Patch where ElevenLabs is looked up by the code under test (sfx_mcp.elevenlabs_sfx.client)
    with patch('sfx_mcp.elevenlabs_sfx.client.ElevenLabs', autospec=True) as mock_sdk_constructor:
        mock_sdk_instance = mock_sdk_constructor.return_value
        # Ensure the instance has the text_to_sound_effects attribute, which itself has a convert method
        mock_sdk_instance.text_to_sound_effects = MagicMock()
        # mock_sdk_instance.text_to_sound_effects.convert is already a MagicMock due to the above line
        yield mock_sdk_instance

@pytest.fixture
def sfx_client(mock_elevenlabs_sdk_client):
    """Provides an ElevenLabsSFXClient instance with a mocked SDK."""
    # The mock_elevenlabs_sdk_client fixture ensures that when ElevenLabsSFXClient
    # instantiates ElevenLabs(api_key=...), it gets our mock.
    # We pass mock_elevenlabs_sdk_client to ensure it's activated before sfx_client is created.
    return ElevenLabsSFXClient(api_key=MOCK_API_KEY)

@pytest.fixture(autouse=True)
def mock_time_sleep():
    """Mocks time.sleep to avoid actual delays in tests."""
    with patch('time.sleep', return_value=None) as mock_sleep:
        yield mock_sleep

# --- Initialization Tests ---

def test_client_initialization_success():
    """Test successful client initialization."""
    client = ElevenLabsSFXClient(api_key=MOCK_API_KEY)
    assert client.max_retries == ElevenLabsSFXClient.DEFAULT_MAX_RETRIES
    assert client.backoff_factor == ElevenLabsSFXClient.DEFAULT_BACKOFF_FACTOR
    # Check if the internal SDK client was attempted to be created with the key
    with patch('sfx_mcp.elevenlabs_sfx.client.ElevenLabs') as mock_constructor: # Patched where it's looked up
        ElevenLabsSFXClient(api_key=MOCK_API_KEY)
        mock_constructor.assert_called_once_with(api_key=MOCK_API_KEY)


def test_client_initialization_custom_retry_settings():
    """Test client initialization with custom retry settings."""
    client = ElevenLabsSFXClient(api_key=MOCK_API_KEY, max_retries=5, backoff_factor=0.5)
    assert client.max_retries == 5
    assert client.backoff_factor == 0.5

def test_client_initialization_empty_api_key():
    """Test client initialization with an empty API key."""
    with pytest.raises(ElevenLabsParameterError, match="API key cannot be empty."):
        ElevenLabsSFXClient(api_key="")

# --- Parameter Validation Tests for generate_sound_effect ---

@pytest.mark.parametrize("duration", [-1.0, 0.0, 0.4, 22.1, 25.0])
def test_generate_invalid_duration(sfx_client, duration):
    """Test generate_sound_effect with invalid duration_seconds."""
    with pytest.raises(ElevenLabsParameterError, match="Duration must be between"):
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT, duration_seconds=duration)

@pytest.mark.parametrize("influence", [-0.1, 1.1, 2.0])
def test_generate_invalid_prompt_influence(sfx_client, influence):
    """Test generate_sound_effect with invalid prompt_influence."""
    with pytest.raises(ElevenLabsParameterError, match="Prompt influence must be between"):
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT, prompt_influence=influence)

@pytest.mark.parametrize("text", ["", "   ", None])
def test_generate_invalid_text_prompt(sfx_client, text):
    """Test generate_sound_effect with invalid text prompt."""
    with pytest.raises(ElevenLabsParameterError, match="Text prompt cannot be empty"):
        sfx_client.generate_sound_effect(text=text)

# --- Successful Generation Test ---

def test_generate_sound_effect_success_default_params(sfx_client, mock_elevenlabs_sdk_client):
    """Test successful sound effect generation with default parameters."""
    expected_audio_bytes = b"mock_audio_data"
    # Return an iterable (list of bytes) because client uses b"".join()
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.return_value = [expected_audio_bytes]

    audio_data = sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert audio_data == expected_audio_bytes
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.assert_called_once_with(
        text=VALID_TEXT_PROMPT,
        duration_seconds=DEFAULT_DURATION,
        prompt_influence=DEFAULT_INFLUENCE,
        output_format=DEFAULT_FORMAT
    )

def test_generate_sound_effect_success_custom_params(sfx_client, mock_elevenlabs_sdk_client):
    """Test successful sound effect generation with custom parameters."""
    expected_audio_bytes = b"mock_custom_audio_data"
    custom_duration = 2.5
    custom_influence = 0.7
    custom_format = "mp3_44100_192"
    # Return an iterable (list of bytes)
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.return_value = [expected_audio_bytes]

    audio_data = sfx_client.generate_sound_effect(
        text=VALID_TEXT_PROMPT,
        duration_seconds=custom_duration,
        prompt_influence=custom_influence,
        output_format=custom_format
    )

    assert audio_data == expected_audio_bytes
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.assert_called_once_with(
        text=VALID_TEXT_PROMPT,
        duration_seconds=custom_duration,
        prompt_influence=custom_influence,
        output_format=custom_format
    )

# --- API Error Handling Tests (more to be added) ---

def test_api_key_error_401(sfx_client, mock_elevenlabs_sdk_client):
    """Test handling of APIError with status 401 (API Key Error)."""
    sdk_error = ElevenLabsSDKAPIError(
        status_code=401,
        body={"detail": {"message": "Invalid API Key."}} # Example body
    )
    # Set side_effect to *be* the exception instance to raise it
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsAPIKeyError) as exc_info:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in str(exc_info.value) or "Invalid API Key." in str(exc_info.value)
    assert exc_info.value.original_error is sdk_error

def test_permission_error_403(sfx_client, mock_elevenlabs_sdk_client):
    """Test handling of APIError with status 403 (Permission Error)."""
    sdk_error = ElevenLabsSDKAPIError(
        status_code=403,
        body={"detail": {"message": "You do not have permissions to perform this action."}}
    )
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsPermissionError) as exc_info:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert exc_info.value.status_code == 403
    assert "Permission denied" in str(exc_info.value)
    assert "You do not have permissions" in str(exc_info.value)
    assert exc_info.value.original_error is sdk_error

def test_bad_request_error_400(sfx_client, mock_elevenlabs_sdk_client):
    """Test handling of APIError with status 400 (Bad Request)."""
    sdk_error = ElevenLabsSDKAPIError(
        status_code=400,
        body={"detail": {"message": "The input text was too long."}}
    )
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsGenerationError) as exc_info: # Mapped to GenerationError
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert exc_info.value.status_code == 400
    assert "Bad request to API" in str(exc_info.value)
    assert "The input text was too long." in str(exc_info.value)
    assert exc_info.value.original_error is sdk_error


# --- Retry Mechanism Tests (more to be added) ---

def test_retry_on_rate_limit_429_then_success(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test retry on 429 error, then success."""
    rate_limit_error = ElevenLabsSDKAPIError(status_code=429, body={"detail": "Rate limit exceeded"})
    success_response_iterable = [b"audio_after_retry"] # Must be iterable

    # Simulate: 1st call -> raises rate_limit_error, 2nd call -> returns success_response_iterable
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = [
        rate_limit_error,
        success_response_iterable
    ]

    client_with_retries = ElevenLabsSFXClient(api_key=MOCK_API_KEY, max_retries=1, backoff_factor=0.01)
    audio_data = client_with_retries.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert audio_data == b"audio_after_retry" # b"".join will produce this
    assert mock_elevenlabs_sdk_client.text_to_sound_effects.convert.call_count == 2
    mock_time_sleep.assert_called_once() # Check that sleep was called due to retry

def test_exhaust_retries_on_rate_limit_429(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test exhausting retries on persistent 429 errors."""
    rate_limit_error = ElevenLabsSDKAPIError(status_code=429, body={"detail": "Rate limit exceeded"})
    
    # Simulate persistent 429 errors
    # Client default max_retries is 3, so 1 initial + 3 retries = 4 calls
    # Each call in side_effect list will be used once.
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = [
        rate_limit_error, rate_limit_error, rate_limit_error, rate_limit_error # This will make it raise 4 times
    ]
    
    client_default_retries = ElevenLabsSFXClient(api_key=MOCK_API_KEY, backoff_factor=0.01) # Uses DEFAULT_MAX_RETRIES (3)

    with pytest.raises(ElevenLabsRateLimitError) as exc_info:
        client_default_retries.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert "Rate limit exceeded after 4 attempts" in str(exc_info.value) # 1 initial + 3 retries
    assert mock_elevenlabs_sdk_client.text_to_sound_effects.convert.call_count == (ElevenLabsSFXClient.DEFAULT_MAX_RETRIES + 1)
    assert mock_time_sleep.call_count == ElevenLabsSFXClient.DEFAULT_MAX_RETRIES
    assert exc_info.value.original_error is rate_limit_error


def test_retry_on_server_error_500_then_success(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test retry on 500 server error, then success."""
    server_error = ElevenLabsSDKAPIError(status_code=500, body={"detail": "Internal server error"})
    success_response_iterable = [b"audio_after_500_retry"]

    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = [
        server_error,
        success_response_iterable
    ]
    
    client_with_retries = ElevenLabsSFXClient(api_key=MOCK_API_KEY, max_retries=1, backoff_factor=0.01)
    audio_data = client_with_retries.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert audio_data == b"audio_after_500_retry"
    assert mock_elevenlabs_sdk_client.text_to_sound_effects.convert.call_count == 2
    mock_time_sleep.assert_called_once()

def test_exhaust_retries_on_server_error_503(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test exhausting retries on persistent 503 server errors."""
    server_error = ElevenLabsSDKAPIError(status_code=503, body={"detail": "Service temporarily unavailable"})
    
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = [
        server_error, server_error, server_error, server_error # 1 initial + 3 retries
    ]

    client_default_retries = ElevenLabsSFXClient(api_key=MOCK_API_KEY, backoff_factor=0.01)

    with pytest.raises(ElevenLabsGenerationError) as exc_info: # 5xx errors map to GenerationError after retries
        client_default_retries.generate_sound_effect(text=VALID_TEXT_PROMPT)

    assert f"Server error ({server_error.status_code}) after {ElevenLabsSFXClient.DEFAULT_MAX_RETRIES + 1} attempts" in str(exc_info.value)
    assert mock_elevenlabs_sdk_client.text_to_sound_effects.convert.call_count == (ElevenLabsSFXClient.DEFAULT_MAX_RETRIES + 1)
    assert mock_time_sleep.call_count == ElevenLabsSFXClient.DEFAULT_MAX_RETRIES
    assert exc_info.value.original_error is server_error

# --- Test Unhandled SDK APIError and General Exception ---

def test_unhandled_sdk_api_error(sfx_client, mock_elevenlabs_sdk_client):
    """Test that an unclassified SDK APIError is wrapped into ElevenLabsAPIError."""
    sdk_error = ElevenLabsSDKAPIError(
        status_code=418, # I'm a teapot
        body={"detail": {"message": "The server is a teapot."}}
    )
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsAPIError) as exc_info:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    
    assert exc_info.value.status_code == 418
    assert "Unhandled API error" in str(exc_info.value)
    assert "The server is a teapot." in str(exc_info.value)
    assert exc_info.value.original_error is sdk_error
    # Ensure it's not one of the more specific custom API errors
    assert not isinstance(exc_info.value, (ElevenLabsAPIKeyError, ElevenLabsRateLimitError, ElevenLabsPermissionError, ElevenLabsGenerationError))


def test_unexpected_non_api_error_during_convert(sfx_client, mock_elevenlabs_sdk_client):
    """Test handling of an unexpected non-APIError during the convert call."""
    unexpected_error = ValueError("Something broke unexpectedly inside convert mock")
    # Make the mocked convert method raise this error
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = unexpected_error

    with pytest.raises(ElevenLabsSFXError) as exc_info:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    
    assert "An unexpected error occurred: Something broke unexpectedly inside convert mock" in str(exc_info.value)
    assert exc_info.value.__cause__ is unexpected_error


def test_sdk_error_body_parsing_for_message(sfx_client, mock_elevenlabs_sdk_client):
    """Test that error message is correctly parsed from SDK error body."""
    # Case 1: body.detail.message
    sdk_error_1 = ElevenLabsSDKAPIError(status_code=400, body={"detail": {"message": "Specific message from detail.message"}})
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error_1
    with pytest.raises(ElevenLabsGenerationError) as exc_info_1:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    assert "Specific message from detail.message" in str(exc_info_1.value)

    # Case 2: body.detail (string)
    sdk_error_2 = ElevenLabsSDKAPIError(status_code=400, body={"detail": "Specific message from detail string"})
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error_2
    with pytest.raises(ElevenLabsGenerationError) as exc_info_2:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    assert "Specific message from detail string" in str(exc_info_2.value)

    # Case 3: body is not a dict or detail not present (fallback to main error message from str(e) of SDK error)
    sdk_error_3 = ElevenLabsSDKAPIError(status_code=400, body="Not a dict")
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error_3
    with pytest.raises(ElevenLabsGenerationError) as exc_info_3:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    # Check that the essential parts of the SDK error's string representation are in our exception message
    assert "status_code: 400" in str(exc_info_3.value) # Added colon
    assert "body: Not a dict" in str(exc_info_3.value) 
    assert "Bad request to API" in str(exc_info_3.value)


    sdk_error_4 = ElevenLabsSDKAPIError(status_code=400, body={"other_key": "value"}) # For dicts, repr usually keeps quotes
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error_4
    with pytest.raises(ElevenLabsGenerationError) as exc_info_4:
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    assert "status_code: 400" in str(exc_info_4.value) # Added colon
    assert "body: {'other_key': 'value'}" in str(exc_info_4.value) # Added colon and space
    assert "Bad request to API" in str(exc_info_4.value)

def test_no_retry_on_401_api_key_error(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test that 401 API Key error does not trigger retries."""
    sdk_error = ElevenLabsSDKAPIError(status_code=401, body={"detail": "Invalid key"})
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsAPIKeyError):
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.assert_called_once() # Should only be called once
    mock_time_sleep.assert_not_called() # No sleep, so no retry

def test_no_retry_on_400_bad_request(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test that 400 Bad Request error does not trigger retries."""
    sdk_error = ElevenLabsSDKAPIError(status_code=400, body={"detail": "Text too short"})
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsGenerationError):
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.assert_called_once()
    mock_time_sleep.assert_not_called()

def test_no_retry_on_403_permission_error(sfx_client, mock_elevenlabs_sdk_client, mock_time_sleep):
    """Test that 403 Permission error does not trigger retries."""
    sdk_error = ElevenLabsSDKAPIError(status_code=403, body={"detail": "No permission"})
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.side_effect = sdk_error

    with pytest.raises(ElevenLabsPermissionError):
        sfx_client.generate_sound_effect(text=VALID_TEXT_PROMPT)
    
    mock_elevenlabs_sdk_client.text_to_sound_effects.convert.assert_called_once()
    mock_time_sleep.assert_not_called()
