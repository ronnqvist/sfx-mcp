# SFX MCP Server - Specification

## 1. Overview

The SFX MCP Server is a Python application designed to provide sound effect generation capabilities as a Model Context Protocol (MCP) tool. It uses the `mcp-sdk` for Python to implement the MCP server logic and communicates with clients (like Cline) via stdio. The server acts as a bridge to the `elevenlabs-sfx` Python library, which handles the core interaction with the ElevenLabs API for sound generation.

**Key Objectives:**

-   Expose a single MCP tool: `generate_sfx`.
-   Handle requests for sound generation, including parameters like text prompt, duration, and prompt influence.
-   Utilize the `elevenlabs-sfx` library for the sound generation.
-   Manage API key configuration securely via an `.env` file.
-   Save generated audio files to a temporary local directory (`mcp_temp_files/`).
-   Return the absolute path to the generated audio file as the tool's output.
-   Implement robust error handling, translating library-specific exceptions into MCP errors.

## 2. Architecture

-   **MCP SDK**: `mcp-sdk` for Python (specifically `mcp[cli]` package).
-   **Server Class**: `mcp.server.Server` (via `FastMCP` initially, then refactored to base `Server`).
-   **Transport**: Stdio, managed by `mcp.server.stdio.stdio_server` context manager.
-   **Core Dependency**: `sfx_mcp.elevenlabs_sfx` (internal module, formerly the `elevenlabs-sfx` library).
-   **Configuration**: `python-dotenv` for loading `ELEVENLABS_API_KEY` from `.env`.
-   **Project Management**: Hatch.
-   **Directory Structure**:
    ```
    sfx-mcp/
    ├── .env                     (user-created, for API key)
    ├── .clinerules/
    │   └── documentation_maintenance.md
    ├── .gitignore
    ├── LICENSE
    ├── MCP_SERVER_SPECIFICATION.md (this file)
    ├── README.md
    ├── pyproject.toml           (Hatch configuration)
    ├── mcp_temp_files/          (for storing generated audio files)
    │   └── .gitkeep
    ├── src/
    │   └── sfx_mcp/
    │       ├── __init__.py
    │       ├── config.py          (loads .env, defines constants)
    │       ├── elevenlabs_proxy.py (interfaces with the internal elevenlabs_sfx module)
    │       ├── elevenlabs_sfx/    (internal module for ElevenLabs interaction)
    │       │   ├── __init__.py
    │       │   ├── client.py
    │       │   └── exceptions.py
    │       └── main.py            (MCP server logic, tool definitions)
    └── tests/
        ├── __init__.py
        └── elevenlabs_sfx/      (tests for the internal elevenlabs_sfx module)
            ├── __init__.py
            └── test_client.py
    ```

## 3. Server Details

-   **Name**: `sfx-mcp`
-   **Version**: `0.1.0`
-   **Description/Instructions**: "MCP Server for generating sound effects using the ElevenLabs API." (This is provided during `Server` initialization).

## 4. Authentication

-   Requires the `ELEVENLABS_API_KEY` environment variable.
-   This key **must** be set in an `.env` file located at the root of the `sfx-mcp` project (`sfx-mcp/.env`).
-   Format: `ELEVENLABS_API_KEY="your_key_here"`
-   The server checks for this key on startup; if not found, it prints a critical message to stderr and may not function correctly for tool calls.

## 5. Dependencies

Key dependencies managed by `pyproject.toml` (Hatch):
-   `mcp[cli]`: The Model Context Protocol SDK for Python.
-   `python-dotenv`: For loading the `.env` file.
-   `elevenlabs>=1.2.0,<2.0.0`: The official ElevenLabs Python SDK, now a direct dependency for the internal `sfx_mcp.elevenlabs_sfx` module.

## 6. Tool: `generate_sfx`

The server exposes a single tool for generating sound effects.

-   **Name**: `generate_sfx`
-   **Description**: "Generates a sound effect based on a text prompt using the ElevenLabs API and returns the path to the audio file."

### 6.1. Input Schema (`inputSchema`)

The tool expects a JSON object with the following properties:

```json
{
  "type": "object",
  "properties": {
    "text": {
      "type": "string",
      "description": "The text prompt for the sound effect."
    },
    "duration_seconds": {
      "type": "number",
      "description": "Optional duration of the sound effect in seconds."
    },
    "prompt_influence": {
      "type": "number",
      "description": "Optional influence of the prompt on the generation (0.0 to 1.0)."
    },
    "output_directory": {
      "type": "string",
      "description": "Optional: The directory path where the sound effect should be saved. Can be absolute or relative to the server's CWD. Defaults to a temporary directory ('mcp_temp_files/') if not provided."
    },
    "output_filename": {
      "type": "string",
      "description": "Optional: The desired filename for the sound effect (including extension, e.g., 'custom.mp3'). Defaults to a unique system-generated name (e.g., 'sfx_<uuid>.mp3') if not provided. If the specified filename already exists in the target directory, versioning is applied (e.g., 'custom_v2.mp3')."
    }
  },
  "required": ["text"]
}
```

**Fields:**
-   `text` (string, **required**): The textual description of the sound effect.
-   `duration_seconds` (float, optional): Desired duration. If not provided, the `elevenlabs-sfx` library's default is used.
-   `prompt_influence` (float, optional): Controls prompt influence (0.0-1.0). If not provided, the `elevenlabs-sfx` library's default is used.
-   `output_directory` (string, optional): Specifies the directory where the generated sound effect file should be saved. This can be an absolute path or a path relative to the server's current working directory. If not provided, the file is saved to the default temporary directory (`mcp_temp_files/` within the server's project structure). The directory will be created if it doesn't exist.
-   `output_filename` (string, optional): Specifies the desired filename for the sound effect, including its extension (e.g., `explosion.mp3`). If not provided, a unique system-generated filename (e.g., `sfx_<uuid>.mp3`) is used. If an extension is not included, `.mp3` will be appended. If the specified `output_filename` already exists in the target directory (either the `output_directory` or the default temporary directory), a versioning scheme is applied by appending `_v<number>` (e.g., `explosion_v2.mp3`, `explosion_v3.mp3`) to ensure uniqueness.

### 6.2. Output

-   **On Success**: The tool returns a string which is the **absolute path** to the generated and saved MP3 audio file.
    -   If `output_directory` and/or `output_filename` are provided, the path will reflect the specified location and name (with versioning if applied).
    -   Otherwise, files are saved in the `sfx-mcp/mcp_temp_files/` directory with a unique name (e.g., `sfx_<uuid>.mp3`).
    -   The MCP `CallToolResult` will have `isError: false` and its `content` will be a list containing a single `TextContent` item, where the `text` field holds this absolute file path.
-   **On Failure**: Raises an `McpError` with an appropriate error code (from `mcp.types` like `INVALID_PARAMS`, `INTERNAL_ERROR`) and a descriptive message. This includes errors related to file system operations (e.g., inability to create a directory or write a file).

### 6.3. Error Handling for the Tool

The tool call handler in `main.py` catches exceptions from the `elevenlabs-sfx` library and internal errors, translating them into `McpError` exceptions with standard MCP error codes:
-   `sfx_exceptions.ElevenLabsAPIKeyError` -> `INTERNAL_ERROR` (as it's a server config issue)
-   `sfx_exceptions.ElevenLabsParameterError` -> `INVALID_PARAMS`
-   Other `sfx_exceptions` (RateLimit, Permission, Generation, API) -> `INTERNAL_ERROR`
-   Unexpected Python exceptions -> `INTERNAL_ERROR`

## 7. Cline Integration

To integrate this server with Cline, the `cline_mcp_settings.json` file must be configured. The recommended and currently working method is to directly invoke the Python interpreter from the Hatch-created virtual environment for the `sfx-mcp` project.

**Example `sfx-mcp` entry in `cline_mcp_settings.json` (updated for Simon's system):**
```json
{
  "mcpServers": {
    // ... other server configurations ...
    "sfx-mcp": {
      "command": "C:\\Users\\simon\\AppData\\Local\\hatch\\env\\virtual\\sfx-mcp\\GrVLiaOy\\sfx-mcp\\Scripts\\python.exe",
      "args": [
        "-u",
        "-m",
        "sfx_mcp.main"
      ],
      "cwd": "c:\\Users\\simon\\projects\\sfx\\sfx-mcp",
      "env": {},
      "disabled": false,
      "autoApprove": ["generate_sfx"],
      "transportType": "stdio",
      "timeout": 60
    }
    // ... other server configurations ...
  }
}
```
**Key fields to customize for a new setup (example for Simon's system):**
-   **`command`**: The absolute path to `python.exe` (Windows) or `python` (Linux/macOS) within the specific Hatch virtual environment for the `sfx-mcp` project.
    -   This path can be found by navigating to the `sfx-mcp` project directory (e.g., `cd c:\Users\simon\projects\sfx\sfx-mcp`) and running `hatch env find default`. For PowerShell, the combined command is `cd sfx-mcp; hatch env find default`.
    -   On Simon's system, `hatch env find default` returned `C:\Users\simon\AppData\Local\hatch\env\virtual\sfx-mcp\GrVLiaOy\sfx-mcp`.
    -   The resulting `command` path is `C:\\Users\\simon\\AppData\\Local\\hatch\\env\\virtual\\sfx-mcp\\GrVLiaOy\\sfx-mcp\\Scripts\\python.exe`.
-   **`cwd`**: The absolute path to the root of the `sfx-mcp` project directory. For Simon's system, this is `c:\Users\simon\projects\sfx\sfx-mcp`.

The `args` should generally remain `["-u", "-m", "sfx_mcp.main"]`.

## 8. Future Considerations
-   Making the `command` and `cwd` paths in `cline_mcp_settings.json` more portable if Cline supports environment variables or relative path resolution for MCP server configurations.
-   Automatic cleanup of files in `mcp_temp_files/`.
