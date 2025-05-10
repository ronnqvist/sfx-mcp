# Cline Rule: Documentation Maintenance and Context Adherence for `sfx-mcp`

## 1. Contextual Understanding
Before starting any new development task or modification for this MCP server project, review the following project documentation to gain full context:
- `MCP_SERVER_SPECIFICATION.md`: For a comprehensive understanding of the server's purpose, tool definitions (name, description, input/output schemas), dependencies, authentication requirements, and overall structure. This is the primary source of truth for the server's intended design and behavior.
- `README.md`: For user-facing documentation including setup instructions, API key management (`.env` file), and how to integrate the server with an MCP client like Cline (specifically, the structure of the entry in `cline_mcp_settings.json`).

## 2. Documentation Updates
After successfully implementing any changes to the server's:
- Tool definitions (e.g., adding/removing tools, changing tool names, parameters, input/output schemas)
- Core functionalities or features
- Authentication mechanisms or environment variable requirements
- Dependencies or supported Python versions
- Technical structure or internal logic that impacts external understanding or usage (e.g., how it's run via Hatch)

Ensure the following documents are updated to accurately reflect the new state of the server:
- **`MCP_SERVER_SPECIFICATION.md`**: This document must be updated to reflect any changes to the server's technical specifications, especially tool definitions.
- **`README.md`**: Update with any changes relevant to the end-user, such as new tools, changes to existing tools, setup instructions, or how to configure it in `cline_mcp_settings.json`.
- **Docstrings**: Ensure all public modules, classes, functions, and methods within the Python source code have comprehensive and up-to-date PEP 257 compliant docstrings, particularly for the MCP server logic in `main.py`.

## 3. Adherence
All development work must align with the specifications outlined in `MCP_SERVER_SPECIFICATION.md` and `README.md` unless explicitly instructed otherwise by the user for a specific task. If a requested change conflicts with existing documentation, bring this to the user's attention and clarify how the documentation (especially `MCP_SERVER_SPECIFICATION.md`) should be updated *prior* to implementing the change.
