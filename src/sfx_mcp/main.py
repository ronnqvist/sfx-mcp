#!/usr/bin/env python
import asyncio
import os
import sys # Import sys for stderr
import uuid
from pathlib import Path
import io
import types # Import types for SimpleNamespace

# MCP SDK Imports
from mcp.types import (
    ListToolsRequest,
    CallToolRequest,
    CallToolResult,
    Tool,
    TextContent,
    METHOD_NOT_FOUND, 
    INVALID_PARAMS,
    INTERNAL_ERROR
)
from mcp.shared.exceptions import McpError
from mcp.server import Server, InitializationOptions, NotificationOptions
from mcp.server.stdio import stdio_server 

# Local project imports
from .config import ELEVENLABS_API_KEY, MCP_TEMP_FILES_DIR
from .elevenlabs_proxy import get_elevenlabs_sfx_client
from elevenlabs_sfx import exceptions as sfx_exceptions

server = Server(
    name="sfx-mcp",
    version="0.1.0",
    instructions="MCP Server for generating sound effects using the ElevenLabs API.",
)

generate_sfx_tool = Tool(
    name="generate_sfx",
    description="Generates a sound effect based on a text prompt using the ElevenLabs API and returns the path to the audio file.",
    inputSchema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text prompt for the sound effect.",
            },
            "duration_seconds": {
                "type": "number",
                "description": "Optional duration of the sound effect in seconds.",
            },
            "prompt_influence": {
                "type": "number",
                "description": "Optional influence of the prompt on the generation (0.0 to 1.0).",
            },
            "output_directory": {
                "type": "string",
                "description": "Optional: The directory path where the sound effect should be saved. Can be absolute or relative to the server's CWD. Defaults to a temporary directory if not provided.",
            },
            "output_filename": {
                "type": "string",
                "description": "Optional: The desired filename for the sound effect (including extension). Defaults to a unique system-generated name if not provided. Versioning (e.g., filename_v2.mp3) is applied if the file already exists.",
            },
        },
        "required": ["text"],
    }
)

@server.list_tools()
async def handle_list_tools_impl():
    return [generate_sfx_tool]

@server.call_tool()
async def handle_call_tool_impl(name: str, arguments: dict | None):
    """
    Handles the 'generate_sfx' tool call.

    Retrieves parameters from the arguments, calls the ElevenLabs SFX client
    to generate the sound effect, and saves it to the specified or default
    location with appropriate filename handling (including versioning).

    Args:
        name: The name of the tool being called (expected to be 'generate_sfx').
        arguments: A dictionary of arguments for the tool, including 'text',
                   and optional 'duration_seconds', 'prompt_influence',
                   'output_directory', and 'output_filename'.

    Returns:
        A list containing a TextContent object with the absolute path to the
        generated sound file.

    Raises:
        McpError: If the tool name is unknown, parameters are invalid,
                  or an error occurs during SFX generation or file handling.
    """
    if name != "generate_sfx":
        error_payload = types.SimpleNamespace(code=METHOD_NOT_FOUND, message=f"Unknown tool: {name}")
        raise McpError(error_payload)

    args = arguments or {}
    text_prompt = args.get("text")
    if not text_prompt or not isinstance(text_prompt, str):
        error_payload = types.SimpleNamespace(code=INVALID_PARAMS, message="Missing or invalid 'text' parameter.")
        raise McpError(error_payload)

    duration = args.get("duration_seconds")
    influence = args.get("prompt_influence")
    output_directory_str = args.get("output_directory")
    output_filename_str = args.get("output_filename")

    try:
        client = get_elevenlabs_sfx_client()

        sfx_kwargs = {}
        if duration is not None:
            sfx_kwargs["duration_seconds"] = float(duration)
        if influence is not None:
            sfx_kwargs["prompt_influence"] = float(influence)
        
        audio_bytes = await asyncio.to_thread(
            client.generate_sound_effect, text=text_prompt, **sfx_kwargs
        )

        # Determine target directory
        if output_directory_str:
            target_dir = Path(output_directory_str).resolve()
            os.makedirs(target_dir, exist_ok=True)
        else:
            target_dir = MCP_TEMP_FILES_DIR
            os.makedirs(target_dir, exist_ok=True) # Ensure default temp dir also exists

        # Determine filename and handle versioning
        if output_filename_str:
            base, ext = os.path.splitext(output_filename_str)
            if not ext: # Ensure there's an extension, default to .mp3
                ext = ".mp3"
                output_filename_str += ext
            
            current_filename = output_filename_str
            counter = 1
            file_path = target_dir / current_filename
            while file_path.exists():
                counter += 1
                current_filename = f"{base}_v{counter}{ext}"
                file_path = target_dir / current_filename
        else:
            current_filename = f"sfx_{uuid.uuid4()}.mp3"
            file_path = target_dir / current_filename
        
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        
        return [TextContent(type="text", text=str(file_path.resolve()))]

    except sfx_exceptions.ElevenLabsAPIKeyError as e:
        error_payload = types.SimpleNamespace(code=INTERNAL_ERROR, message=f"ElevenLabs API Key configuration error: {e}")
        raise McpError(error_payload)
    except sfx_exceptions.ElevenLabsParameterError as e:
        error_payload = types.SimpleNamespace(code=INVALID_PARAMS, message=f"ElevenLabs parameter error: {e}")
        raise McpError(error_payload)
    except (sfx_exceptions.ElevenLabsRateLimitError, 
            sfx_exceptions.ElevenLabsPermissionError, 
            sfx_exceptions.ElevenLabsGenerationError, 
            sfx_exceptions.ElevenLabsAPIError) as e:
        error_payload = types.SimpleNamespace(code=INTERNAL_ERROR, message=f"ElevenLabs API interaction error: {e}")
        raise McpError(error_payload)
    except Exception as e:
        print(f"Unexpected error during SFX generation: {e}", file=sys.stderr) # Print to stderr
        error_payload = types.SimpleNamespace(code=INTERNAL_ERROR, message=f"An unexpected error occurred: {e}")
        raise McpError(error_payload)

async def main_async_runner():
    if not ELEVENLABS_API_KEY:
        print("CRITICAL: ELEVENLABS_API_KEY is not configured. SFX MCP Server cannot start.", file=sys.stderr) # Print to stderr
        return

    print("SFX MCP Server (lowlevel Server) starting with stdio_server...", file=sys.stderr) # Print to stderr
    
    init_options = server.create_initialization_options(
        notification_options=NotificationOptions(tools_changed=True),
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            initialization_options=init_options 
        )

if __name__ == "__main__":
    asyncio.run(main_async_runner())
