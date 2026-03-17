"""
MCP Tools Definitions — Sequential Thinking Pattern

This module defines the tools for the prompt_docu MCP server.

The primary tool is `document_prompt`, which follows the Sequential Thinking
MCP pattern: a single tool called repeatedly, once per prompt/thought, where
each call FIRST saves the prompt to disk, THEN returns chain status.

When nextPromptNeeded becomes false the server automatically runs the full
documentation pipeline (aggregate → summarise → README).
"""

from mcp.types import Tool

# ─────────────────────────────────────────────────────────────────────────────
# Primary sequential-thinking tool
# ─────────────────────────────────────────────────────────────────────────────

_DOCUMENT_PROMPT_TOOL = Tool(
    name="document_prompt",
    description=(
        "A detailed tool for sequential prompt documentation through thinking steps.\n"
        "This tool documents prompts through a flexible process that can adapt and evolve.\n"
        "Each prompt builds on, questions, or revises previous entries as understanding deepens.\n\n"
        "When to use this tool:\n"
        "- Documenting any prompt or thought during a coding session\n"
        "- Breaking down complex tasks into documented steps\n"
        "- Planning and design with room for revision\n"
        "- Analysis that might need course correction\n"
        "- Tasks that need to maintain context over multiple steps\n\n"
        "Key features:\n"
        "- You can adjust totalPrompts up or down as you progress\n"
        "- You can question or revise previous prompts\n"
        "- You can add more prompts even after reaching what seemed like the end\n"
        "- You can branch into alternative exploration paths\n"
        "- Each call SAVES the prompt FIRST, then returns chain status\n"
        "- When nextPromptNeeded=false, the full pipeline runs automatically "
        "(aggregate → summarise → README)\n\n"
        "Parameters explained:\n"
        "- message: Your current prompt/thinking step\n"
        "- file_names: Files in context for this prompt\n"
        "- nextPromptNeeded: True if you need more documentation steps\n"
        "- promptNumber: Current number in sequence (can go beyond initial total)\n"
        "- totalPrompts: Current estimate of prompts needed (adjustable up/down)\n"
        "- isRevision: Boolean indicating if this revises previous thinking\n"
        "- revisesPrompt: If isRevision is true, which prompt number is being reconsidered\n"
        "- branchFromPrompt: If branching, which prompt number is the branching point\n"
        "- branchId: Identifier for the current branch (if any)\n"
        "- needsMorePrompts: If reaching end but realising more prompts are needed"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Your current prompt/thinking step. Can include regular analytical steps, revisions, "
                               "questions about previous decisions, realisations, changes in approach, etc.",
            },
            "file_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The complete list of file names or file paths in context for this prompt. "
                               "Send an empty array [] if no files are in context.",
            },
            "promptNumber": {
                "type": "integer",
                "description": "Current prompt number in the sequence (1-based). Can go beyond initial totalPrompts if needed.",
                "minimum": 1,
            },
            "totalPrompts": {
                "type": "integer",
                "description": "Current estimate of total prompts needed. Can be adjusted up or down as the session progresses.",
                "minimum": 1,
            },
            "nextPromptNeeded": {
                "type": "boolean",
                "description": "Whether another prompt step is needed. Set to false only when truly done — "
                               "this triggers the automatic aggregation/summarisation pipeline.",
            },
            "isRevision": {
                "type": "boolean",
                "description": "Whether this prompt revises previous thinking.",
                "default": False,
            },
            "revisesPrompt": {
                "type": "integer",
                "description": "If isRevision is true, the prompt number being reconsidered.",
                "minimum": 1,
            },
            "branchFromPrompt": {
                "type": "integer",
                "description": "If branching, the prompt number that is the branching point.",
                "minimum": 1,
            },
            "branchId": {
                "type": "string",
                "description": "Identifier for the current branch (if any).",
            },
            "needsMorePrompts": {
                "type": "boolean",
                "description": "Set to true if reaching the end but realising more prompts are needed.",
                "default": False,
            },
        },
        "required": ["message", "file_names", "promptNumber", "totalPrompts", "nextPromptNeeded"],
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Utility tools
# ─────────────────────────────────────────────────────────────────────────────

_SAVE_ALL_PROMPTS_TOOL = Tool(
    name="save_all_prompts",
    description=(
        "Save all the user text/prompts entered so far in the session AND the complete "
        "list of all files used in this context/session to final_logs. "
        "BOTH parameters MUST ALWAYS be provided. If no files are in context, send an empty array []."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "All the prompts/text in the order they were entered.",
            },
            "file_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The list of all file names or file paths used in this context.",
            },
        },
        "required": ["message", "file_names"],
    },
)

_CLEAR_TEMP_LOGS_TOOL = Tool(
    name="clear_temp_logs",
    description=(
        "Clear all .txt files from the temp_logs folder. Removes all temporary prompt "
        "files while preserving the directory structure. Use to clean up after aggregation "
        "or to start fresh."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

_CLEAR_AGGREGATE_LOGS_TOOL = Tool(
    name="clear_aggregate_logs",
    description=(
        "Clear all .txt aggregate files from the aggregate_logs folder while preserving "
        "the CSV tracker. Removes aggregate reports but keeps tracking information."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

_CREATE_README_TOOL = Tool(
    name="create_readme",
    description=(
        "Generate a comprehensive README.md file using all data from the final_logs folder. "
        "Creates a structured README with project overview, file descriptions, workflow "
        "documentation, and statistics about all logged prompts and summaries."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Public list consumed by the MCP server
# ─────────────────────────────────────────────────────────────────────────────

TOOLS = [
    _DOCUMENT_PROMPT_TOOL,
    _SAVE_ALL_PROMPTS_TOOL,
    _CLEAR_TEMP_LOGS_TOOL,
    _CLEAR_AGGREGATE_LOGS_TOOL,
    _CREATE_README_TOOL,
]

