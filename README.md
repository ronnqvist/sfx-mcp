# SFX MCP Server

The SFX MCP Server provides a Model Context Protocol (MCP) tool for generating sound effects using the ElevenLabs API. It uses an internal module (`sfx_mcp.elevenlabs_sfx`) as its core engine for sound generation and is designed to be managed by an MCP client like Cline.

## Prerequisites

-   Python 3.8+
-   Hatch (Python project manager)
-   An ElevenLabs API Key

## Setup and Installation

This server is intended to be run as an MCP server, typically managed by an MCP client application (e.g., Cline).

1.  **Configure API Key:**
    Create a `.env` file in the root of the `sfx-mcp` project directory (i.e., `sfx-mcp/.env`):
    ```env
    ELEVENLABS_API_KEY="your_actual_elevenlabs_api_key"
    ```
    Replace `"your_actual_elevenlabs_api_key"` with your valid ElevenLabs API key. The server will not function without it.

2.  **Hatch Environment Setup (Automatic via MCP Client):**
    When an MCP client like Cline starts this server using the configuration below, Hatch will automatically create a virtual environment, install dependencies (including `mcp[cli]` and the internal `elevenlabs_sfx` module components), and run the server script.
    You do not typically need to run `hatch env create` or `hatch run` manually for Cline integration, but doing so can be useful for direct testing:
    ```bash
    # To manually test the server startup (from sfx-mcp directory):
    # hatch env remove default  # To ensure a clean build
    # hatch run serve_mcp
    ```
    The `serve_mcp` script is defined in `pyproject.toml`.

## Cline Integration (MCP Settings)

To use this server with Cline, add the following configuration object to Cline's MCP settings file. For your system, this file is typically located at `C:/Users/simon/AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`.

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

**Important Notes for `cline_mcp_settings.json`:**
-   **`command`**: This **must be the absolute path** to the `python.exe` (or `python` on Linux/macOS) executable *within the specific Hatch virtual environment created for the `sfx-mcp` project*.
    -   To find this path:
        1.  Navigate to your local `sfx-mcp` project directory in a terminal (e.g., `cd c:\Users\simon\projects\sfx\sfx-mcp`).
        2.  Run the command `hatch env find default`. If you are using PowerShell, the command to change directory and then find the environment is `cd sfx-mcp; hatch env find default`. This will output the base path of the virtual environment. For your system, this was `C:\Users\simon\AppData\Local\hatch\env\virtual\sfx-mcp\GrVLiaOy\sfx-mcp`.
        3.  The Python executable is typically at `Scripts\python.exe` (Windows) or `bin/python` (Linux/macOS) inside this base path.
        4.  Example for your Windows system, given the `hatch env find default` output:
            The command path would be `C:\\Users\\simon\\AppData\\Local\\hatch\\env\\virtual\\sfx-mcp\\GrVLiaOy\\sfx-mcp\\Scripts\\python.exe`. (Note double backslashes for JSON).
-   **`args`**: Should be `["-u", "-m", "sfx_mcp.main"]` to run the server script as an unbuffered module.
-   **`cwd`**: This **must be the absolute path** to the root directory of your local `sfx-mcp` project. For your system, this is `"c:\\Users\\simon\\projects\\sfx\\sfx-mcp"` (use double backslashes in JSON) or `"c:/Users/simon/projects/sfx/sfx-mcp"`.

## Tool Overview

The server provides one tool:

### `generate_sfx`
-   **Description**: Generates a sound effect based on a text prompt using the ElevenLabs API and returns the absolute path to the generated MP3 audio file.
-   **Parameters**:
    -   `text` (string, required): The descriptive prompt for the sound effect (e.g., "a cat meowing").
    -   `duration_seconds` (float, optional): Desired duration of the sound effect in seconds.
    -   `prompt_influence` (float, optional, 0.0-1.0): Controls how much the prompt influences the generation.
    -   `output_directory` (string, optional): The directory path (absolute or relative to the server's CWD) where the sound effect should be saved. If not provided, defaults to `sfx-mcp/mcp_temp_files/`. The directory will be created if it doesn't exist.
    -   `output_filename` (string, optional): The desired filename for the sound effect (e.g., `my_sound.mp3`). If not provided, a unique name like `sfx_<uuid>.mp3` is generated. If the filename lacks an extension, `.mp3` is appended. If the file already exists in the target directory, versioning is applied (e.g., `my_sound_v2.mp3`).
-   **Output**: A string containing the absolute path to the generated and saved MP3 file. The path reflects the chosen directory and filename (including any versioning).

## Development

This project uses `Hatch` for project management and `ruff` for linting/formatting.

-   **Linting & Formatting**:
    ```bash
    hatch fmt
    ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
