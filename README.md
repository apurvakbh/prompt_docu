# Prompt Docu

A Model Context Protocol (MCP) server for sequential prompt documentation using the Sequential Thinking pattern.

## Overview

## What problem does it solve?
As software development has shifted from manual coding to writing prompts for code generation, **Prompt Docu** addresses the critical need to document and track the evolution of AI-assisted development sessions.

**Prompt Docu** follows the **Sequential Thinking MCP pattern**: instead of separate tools for different operations, it uses a single primary tool (`document_prompt`) that is called repeatedly—once per prompt/thought. Each call **saves the prompt first** (documentation before execution), then returns chain status. When the thought chain ends, the full documentation pipeline runs automatically.

## Features

This server exposes **one primary tool** and **four utility tools** following the Sequential Thinking pattern:

### Primary Sequential Tool

- **`document_prompt`**  
  The core sequential-thinking tool called repeatedly throughout a session—once per prompt/thought. Each call:
  
  **SAVES FIRST**: Persists the prompt to `temp_logs/` with full chain metadata (prompt number, total, revision info, branch info) before anything else happens.
  
  **Parameters** (mirrors Sequential Thinking MCP):
  - `message` – Your current prompt/thinking step
  - `file_names` – Files in context for this prompt
  - `promptNumber` – Current step in sequence (1-based)
  - `totalPrompts` – Estimated total (adjustable)
  - `nextPromptNeeded` – Whether more prompts follow (when `false`, triggers auto-pipeline)
  - `isRevision` – Revises a previous prompt
  - `revisesPrompt` – Which prompt number to revise
  - `branchFromPrompt` – Branching point
  - `branchId` – Branch identifier
  - `needsMorePrompts` – Dynamic extension flag
  
  **Auto-Pipeline**: When `nextPromptNeeded=false`, automatically runs:
  1. Aggregate all un-aggregated temp logs → `aggregate_logs/`
  2. Summarize aggregates → `final_logs/`
  3. Generate README.md in `prompt_logs/`
  
  **Returns**: JSON status similar to sequential thinking:
  ```json
  {
    "promptNumber": 3,
    "totalPrompts": 5,
    "nextPromptNeeded": true,
    "branches": [],
    "promptHistoryLength": 3,
    "savedTo": "prompt_20260317_123456.txt"
  }
  ```

### Utility Tools

- **`save_all_prompts`**  
  Bulk-save all session prompts and file history into a timestamped final log (`final_logs/`). Use this for manual archival of complete sessions.

- **`clear_temp_logs`**  
  Removes all `.txt` files from `temp_logs/` while preserving directory structure. Use after aggregation to clean up processed temporary files.

- **`clear_aggregate_logs`**  
  Removes all `.txt` files from `aggregate_logs/` while preserving the CSV tracker. Use to clean up old aggregate reports.

- **`create_readme`**  
  Manually triggers README.md generation in `prompt_logs/` using data from `final_logs/`. (Note: `document_prompt` auto-generates this when chain ends.)

## Workflow

The Sequential Thinking pattern creates a natural, iterative documentation flow:

### Sequential Prompt Documentation

1. **Call `document_prompt` repeatedly** — once per prompt/thought during your session:
   ```
   Prompt #1: "Analyze the problem..."
   Prompt #2: "Design the solution..."
   Prompt #3: "Revise approach..." (can revise Prompt #2)
   ...
   Prompt #N: "Final implementation" (nextPromptNeeded=false)
   ```

2. **Each call SAVES FIRST**: The prompt is persisted to `temp_logs/` with full metadata before any processing

3. **Chain Status**: Each call returns JSON showing progress through the thought chain

4. **Auto-Pipeline**: When `nextPromptNeeded=false`, the server automatically:
   - Aggregates temp logs → `aggregate_logs/`
   - Summarizes aggregates → `final_logs/`
   - Generates README.md

### Traditional Workflow (Using Utilities)

Alternatively, use the utility tools for manual control:

1. **Archive Phase**  
   - Use `save_all_prompts` to manually create permanent session archives in `final_logs/`

2. **Cleanup Phase**  
   - Use `clear_temp_logs` to remove processed temp files
   - Use `clear_aggregate_logs` to remove old aggregate reports
   - Use `create_readme` to manually regenerate documentation


## Directory Structure

The server organizes logs automatically based on your configuration:

```
prompt_logs/
├── temp_logs/          # Sequential prompt captures with chain metadata
│   └── prompt_YYYYMMDD_HHMMSS.txt  (includes promptNumber, revisions, branches)
├── final_logs/         # Complete session archives and summaries
│   ├── all_prompts_YYYYMMDD_HHMMSS.txt
│   └── aggregate_summary_YYYYMMDD_HHMMSS.txt
├── aggregate_logs/     # Compiled analysis reports
│   ├── aggregate_YYYYMMDD_HHMMSS.txt
│   └── aggregation_tracker.csv
└── README.md          # Auto-generated documentation
```

### Key Files

- **`prompt_*.txt`** in `temp_logs/`: Individual sequential prompt captures with:
  - Full chain metadata (prompt #, total, next needed)
  - Revision tracking (which prompt this revises)
  - Branch information (branch ID, branch point)
  - Machine-readable JSON metadata block for aggregation
- **`all_prompts_*.txt`** in `final_logs/`: Complete session archives (bulk-save format)
- **`aggregate_*.txt`** in `aggregate_logs/`: Structured reports with per-file change tracking
- **`aggregate_summary_*.txt`** in `final_logs/`: High-level summaries of all aggregates
- **`aggregation_tracker.csv`**: CSV database tracking processed temp files
- **`README.md`**: Auto-generated when `document_prompt` chain ends or via `create_readme` tool

## Configuration

Paths and settings are managed in `config.toml`. You can customize the base folder and subdirectory names to fit your project structure.

```toml
[paths]
# Base folder name for logs (relative to project directory)
base_folder = "prompt_logs"

# Subdirectory names within base_logs_location
temp_logs = "temp_logs"
final_logs = "final_logs"
aggregate_logs = "aggregate_logs"
```

All directories are created automatically on server startup if they don't exist.

## Installation

**Requirements:**
- Python 3.8 or higher (Python 3.12+ recommended)

### Via pip (Recommended)

Install the package directly from PyPI:

```bash
pip install prompt-docu
```

### Verification

Once installed, you can verify the installation by starting the server:

```bash
prompt-docu
```

(Note: This will initialize the server and create the `prompt_logs/` directory in your current workspace).

### From Source

Alternatively, clone the repository and install locally:

```bash
git clone https://github.com/apurva-bhatt/prompt_docu.git
cd prompt_docu
pip install -e .
```

## Running the Server

After installation, you can start the MCP server directly:

```bash
prompt-docu
```

## MCP Client Configuration

### Claude Desktop

Add this configuration to your Claude Desktop config file:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "prompt-docu": {
      "command": "prompt-docu"
    }
  }
}
```

### Other MCP Clients

For other MCP clients (VS Code extensions, custom implementations), configure them to execute the `prompt-docu` command as the server entry point.

## Usage Example

Typical workflow using the Sequential Thinking pattern:

### Sequential Documentation (Recommended)

The AI automatically calls `document_prompt` repeatedly as it works through your request:

```
Call 1: document_prompt(
  message="Analyzing the problem...",
  file_names=["main.py"],
  promptNumber=1,
  totalPrompts=5,
  nextPromptNeeded=true
)
→ Saves to temp_logs/prompt_20260317_120001.txt
→ Returns: {"promptNumber": 1, "totalPrompts": 5, "nextPromptNeeded": true, ...}

Call 2: document_prompt(
  message="Designing the solution...",
  file_names=["main.py", "helper.py"],
  promptNumber=2,
  totalPrompts=5,
  nextPromptNeeded=true
)
→ Saves to temp_logs/prompt_20260317_120002.txt
→ Returns: {"promptNumber": 2, "totalPrompts": 5, "nextPromptNeeded": true, ...}

...

Call N: document_prompt(
  message="Implementation complete",
  file_names=["main.py", "helper.py", "tests.py"],
  promptNumber=5,
  totalPrompts=5,
  nextPromptNeeded=false  ← Chain ends
)
→ Saves to temp_logs/prompt_20260317_120005.txt
→ Auto-runs pipeline: aggregate → summarize → README
→ Returns: {"promptNumber": 5, ..., "nextPromptNeeded": false} + pipeline report
```

### Manual Workflow (Using Utilities)

For manual control or batch operations:

1. Archive the entire session: `save_all_prompts(message=..., file_names=...)`
2. Clean up processed files: `clear_temp_logs()`
3. Regenerate documentation: `create_readme()`

## Tips

- Use larger models with Prompt Docu like Claude Sonnet 4.5 and others for best results with the Sequential Thinking pattern
- The `document_prompt` tool mirrors how sequential thinking works—each call builds on previous prompts
- Let the AI manage the sequential flow naturally; the documentation happens automatically
- Use `isRevision=true` to mark when you're reconsidering earlier prompts
- Branch exploration is supported via `branchId` for alternative solution paths

## Understanding Sequential Thinking Pattern

The Sequential Thinking MCP pattern (inspired by the `sequentialthinking` MCP tool) works differently from traditional multi-tool MCPs:

**Traditional approach**: Separate tools for different operations (save, aggregate, summarize, etc.)

**Sequential Thinking approach**: ONE tool called repeatedly in a chain
- Each call represents one step in the thought/prompt sequence
- Each call SAVES FIRST (documentation before execution)
- State accumulates across calls (prompt history, branches, revisions)
- When the chain ends, the full pipeline runs automatically

**Benefits**:
- Natural documentation flow that mirrors how AI thinks through problems
- No need to remember which tool to call when—just continue the chain
- Automatic aggregation and summarization when the session completes
- Support for revisions and branching (explore alternative approaches)
- Complete audit trail with sequence numbers and relationships

## What's New in v0.2.0

**Major architectural refactor** to Sequential Thinking MCP pattern:

- **New primary tool**: `document_prompt` — called repeatedly (once per prompt), saves first, returns chain status
- **Removed tools**: `save_current_prompt`, `aggregate_prompts`, `summarize_aggregates`, `document_session` (functionality absorbed into sequential flow)
- **Kept utilities**: `save_all_prompts`, `clear_temp_logs`, `clear_aggregate_logs`, `create_readme`
- **Auto-pipeline**: When prompt chain ends (`nextPromptNeeded=false`), automatically runs aggregate → summarize → README
- **Sequential metadata**: Each saved prompt includes full chain context (number, total, revisions, branches)
- **Code cleanup**: Removed unused `src/` folder, dead imports, and `get_daily_folder_path` function

## Contributing

The project is still in development. We request users to please create PRs if you see any limitations or have suggestions for improvement. 