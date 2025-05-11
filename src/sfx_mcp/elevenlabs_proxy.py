from sfx_mcp.elevenlabs_sfx.client import ElevenLabsSFXClient
from sfx_mcp.elevenlabs_sfx import exceptions as sfx_exceptions
from .config import ELEVENLABS_API_KEY

# Store the client instance globally within this module to reuse it if possible,
# or instantiate it on demand. For simplicity, we'll instantiate on demand
# in the function, but in a high-traffic server, a shared instance might be better.

def get_elevenlabs_sfx_client() -> ElevenLabsSFXClient:
    """
    Initializes and returns an instance of the ElevenLabsSFXClient.

    Raises:
        sfx_exceptions.ElevenLabsAPIKeyError: If the API key is not configured.

    Returns:
        ElevenLabsSFXClient: An instance of the client.
    """
    if not ELEVENLABS_API_KEY:
        raise sfx_exceptions.ElevenLabsAPIKeyError(
            "ELEVENLABS_API_KEY is not configured. Please set it in the .env file."
        )
    return ElevenLabsSFXClient(api_key=ELEVENLABS_API_KEY)

async def generate_sfx(
    text: str,
    duration_seconds: float | None = None,
    prompt_influence: float | None = None,
    output_format: str | None = None,
) -> bytes:
    """
    Generates a sound effect using the ElevenLabsSFXClient.

    This function acts as a proxy to the elevenlabs-sfx library,
    handling client instantiation and parameter passing.

    Args:
        text: The text prompt for the sound effect.
        duration_seconds: Optional duration in seconds. Defaults to library default.
        prompt_influence: Optional prompt influence. Defaults to library default.
        output_format: Optional output format. Defaults to library default.

    Returns:
        bytes: The generated audio data.

    Raises:
        sfx_exceptions.ElevenLabsSFXError: Base class for errors from the sfx library.
        sfx_exceptions.ElevenLabsAPIKeyError: If API key is missing.
        sfx_exceptions.ElevenLabsParameterError: For invalid parameters.
        sfx_exceptions.ElevenLabsRateLimitError: If rate limit is exceeded.
        sfx_exceptions.ElevenLabsPermissionError: For permission issues.
        sfx_exceptions.ElevenLabsGenerationError: If generation fails.
        sfx_exceptions.ElevenLabsAPIError: For other API errors.
        Exception: For any other unexpected errors during the process.
    """
    client = get_elevenlabs_sfx_client()

    # Prepare arguments, only passing them if they are not None
    # The elevenlabs-sfx library has its own defaults if parameters are not provided.
    kwargs = {}
    if duration_seconds is not None:
        kwargs["duration_seconds"] = duration_seconds
    if prompt_influence is not None:
        kwargs["prompt_influence"] = prompt_influence
    if output_format is not None:
        kwargs["output_format"] = output_format
    
    try:
        # Use asyncio.to_thread to run the synchronous method in a separate thread
        import asyncio
        audio_bytes = await asyncio.to_thread(client.generate_sound_effect, text=text, **kwargs)
        return audio_bytes
    except sfx_exceptions.ElevenLabsSFXError as e:
        # Re-raise known SFX library errors to be handled by the FastAPI endpoint
        raise e
    except Exception as e:
        # Catch any other unexpected errors and wrap them or re-raise
        # For now, re-raising to be caught by a generic handler in FastAPI
        # Consider logging here
        print(f"Unexpected error in elevenlabs_proxy: {e}")
        raise sfx_exceptions.ElevenLabsSFXError(f"An unexpected error occurred: {e}")
