"""
MCP Tools Definitions

This module contains all the tool definitions for the MCP server.
"""

from mcp.types import Tool

# Define your tools
TOOLS = [
    Tool(
        name="save_current_prompt",
        description="If the user requests to save the current prompt, then save the current user text/prompt AND the complete list of files used in this context. BOTH parameters MUST ALWAYS be provided - message and file_names. If no files are in context, send an empty array [] for file_names.",
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
        description="If the user requests to save all prompts, then save all the user text/prompt entered so far in the session AND the complete list of all files used in this context/session. BOTH parameters MUST ALWAYS be provided - message and file_names. If no files are in context, send an empty array [] for file_names.",
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
        description="If the user requests to aggregate all prompts, then aggregate all prompts from the temp logs folder. This tool reads all prompt text files in the temp folder, creates a detailed aggregated report, saves it to the aggregate folder, and maintains a CSV tracker of aggregated files. No parameters required.",
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
        name="clear_temp_logs",
        description="Clear all .txt files from the temp_logs folder. This removes all temporary prompt files while preserving the directory structure. Use this to clean up after aggregation or to start fresh.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="clear_aggregate_logs",
        description="Clear all .txt aggregate files from the aggregate_logs folder while preserving the CSV tracker. This removes all aggregate reports but keeps the tracking information. Use this to clean up old aggregates.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="summarize_aggregates",
        description="Create a comprehensive summary of all aggregate files and save it to the final_logs folder. This tool analyzes all aggregate reports, extracts file references, and creates a detailed summary document with statistics and file listings.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="create_readme",
        description="Generate a comprehensive README.md file using all data from the final_logs folder. This creates a structured README with project overview, file descriptions, workflow documentation, and statistics about all logged prompts and summaries.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]

