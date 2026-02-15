"""
MCP Tools Definitions

This module contains all the tool definitions for the MCP server.
"""

from mcp.types import Tool

# Define your tools
TOOLS = [
    Tool(
        name="save_current_prompt",
        description="REQUIRED: Save current user text/prompt AND the complete list of files used in this context. BOTH parameters MUST ALWAYS be provided - message and file_names. If no files are in context, send an empty array [] for file_names.",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "First, Save the full and whole current prompt/text entered now, no matter what is in it.",
                },
                "file_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Second, Save the full and whole list of all the file names or all the file paths that are being used in the context for this prompt.",
                }
            },
            "required": ["message", "file_names"],
        },
    ),
    Tool(
        name="save_all_prompts",
        description="REQUIRED: Save ALL the user text/prompt entered so far in the session AND the complete list of all files used in this context/session. BOTH parameters MUST ALWAYS be provided - message and file_names. If no files are in context, send an empty array [] for file_names.",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "First, send all the prompts/text here in the order they were entered, no matter what is in it.",
                },
                "file_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Second, Save the list of all the file names or all the file paths that are being used in the context for this prompt.",
                }
            },
            "required": ["message", "file_names"],
        },
    ),
    Tool(
        name="aggregate_prompts",
        description="Aggregate all prompts from the temp logs folder. This tool reads all prompt text files in the temp folder, creates a detailed aggregated report, saves it to the aggregate folder, and maintains a CSV tracker of aggregated files. No parameters required.",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "First, send all the prompts/text here in the order they were entered, no matter what is in it.",
                },
                "file_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Second, Save the list of all the file names or all the file paths that are being used in the context for this prompt.",
                }
            },
            "required": ["message", "file_names"],
        },
    )
]
