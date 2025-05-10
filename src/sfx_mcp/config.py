import os
import io # Import io for StringIO
from dotenv import load_dotenv
from pathlib import Path

# Determine the project root directory (sfx-mcp)
# This assumes config.py is in sfx-mcp/src/sfx_mcp/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file located in the project root
dotenv_path = PROJECT_ROOT / ".env"

try:
    # Try to read as UTF-16, then pass as a stream of decoded strings
    with open(dotenv_path, 'r', encoding='utf-16') as f:
        env_content = f.read()
    load_dotenv(stream=io.StringIO(env_content))
except UnicodeDecodeError:
    # Fallback to utf-8-sig if utf-16 fails (e.g., if it's actually utf-8)
    load_dotenv(dotenv_path=dotenv_path, encoding="utf-8-sig")


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    # This is a fallback or a way to indicate the key is missing.
    # In a real application, you might raise an error or have a more robust
    # configuration management system. For this MCP server, we'll rely on
    # the .env file primarily. The proxy or main app should check for its presence.
    print(
        "Warning: ELEVENLABS_API_KEY not found in .env file. "
        "The server will not be able to authenticate with ElevenLabs."
    )

# Define the temporary files directory relative to the project root
MCP_TEMP_FILES_DIR = PROJECT_ROOT / "mcp_temp_files"
MCP_TEMP_FILES_DIR.mkdir(parents=True, exist_ok=True) # Ensure it exists
