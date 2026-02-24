# Prompt Docu

A minimal Model Context Protocol (MCP) server for logging, tracking, and documenting development prompts.

## Overview

## What problem does it solve?
As software development has shifted from manual coding to writing prompts for code generation, **Prompt Docu** addresses the critical need to document and track the evolution of AI-assisted development sessions.

**Prompt Docu** is a lightweight tool designed to capture the context of your development sessions. It runs as an MCP server and provides utilities to save prompts, track file contexts, and aggregate logs into structured reports.

## Features

This server exposes **seven powerful tools** to help manage your development documentation workflow:

### Core Logging Tools

- **`save_current_prompt`**  
  Captures the current prompt and list of active file contexts, saving them to temporary logs (`temp_logs/`). Use this to document incremental changes or manual code modifications during development.

- **`save_all_prompts`**  
  Archives the entire session's prompts and file history into a timestamped final log (`final_logs/`). This creates a permanent record of all prompts used in a session.

### Analysis & Aggregation Tools

- **`aggregate_prompts`**  
  Processes all un-aggregated temporary logs and compiles them into a comprehensive, structured report in `aggregate_logs/`. This tool:
  - Saves the current prompt first
  - Reads all `.txt` files from `temp_logs/` that haven't been processed yet
  - Parses prompts to extract timestamps, actions, and file references
  - Groups changes by file with chronological tracking
  - Maintains a CSV tracker (`aggregation_tracker.csv`) to prevent duplicate processing
  - Creates detailed reports with three sections: source files, per-file aggregate points, and raw content

- **`summarize_aggregates`**  
  Creates a comprehensive summary of all aggregate files and saves it to `final_logs/`. This tool analyzes all aggregate reports to extract:
  - Overview of all aggregate files processed
  - All files modified/referenced across sessions
  - Unique file lists and statistics
  - Total prompt entries across all aggregates

- **`create_readme`**  
  Generates a comprehensive README.md in the `prompt_logs/` directory using data from `final_logs/`. The generated README includes:
  - Project overview and directory structure
  - Complete file listings with sizes and timestamps
  - Workflow documentation
  - Available tools reference
  - Statistics and metadata

### Maintenance Tools

- **`clear_temp_logs`**  
  Removes all `.txt` files from `temp_logs/` folder while preserving directory structure. Use this after aggregation to clean up processed temporary files.

- **`clear_aggregate_logs`**  
  Removes all `.txt` files from `aggregate_logs/` folder while preserving the CSV tracker. Use this to clean up old aggregate reports while maintaining processing history.

## Workflow

The tools are designed to work in a three-tier workflow:

1. **Capture Phase** (`temp_logs/`)  
   - Use `save_current_prompt` to capture individual prompts during active development
   - Each prompt is saved with UTC timestamp, full text, and file context

2. **Analysis Phase** (`aggregate_logs/`)  
   - Use `aggregate_prompts` to process temp logs into structured reports
   - CSV tracker ensures each temp file is only aggregated once
   - Reports organize changes chronologically per file

3. **Archive Phase** (`final_logs/`)  
   - Use `save_all_prompts` to create permanent session archives
   - Use `summarize_aggregates` to create high-level summaries
   - Use `create_readme` to generate documentation from final logs

4. **Cleanup Phase**  
   - Use `clear_temp_logs` after successful aggregation
   - Use `clear_aggregate_logs` to remove old aggregate reports


## Directory Structure

The server organizes logs automatically based on your configuration:

```
prompt_logs/
├── temp_logs/          # Individual prompt captures (working directory)
│   └── prompt_YYYYMMDD_HHMMSS.txt
├── final_logs/         # Complete session archives and summaries
│   ├── all_prompts_YYYYMMDD_HHMMSS.txt
│   └── aggregate_summary_YYYYMMDD_HHMMSS.txt
├── aggregate_logs/     # Compiled analysis reports
│   ├── aggregate_YYYYMMDD_HHMMSS.txt
│   └── aggregation_tracker.csv
└── README.md          # Auto-generated documentation (optional)
```

### Key Files

- **`prompt_*.txt`** in `temp_logs/`: Individual prompt captures with timestamps and file contexts
- **`all_prompts_*.txt`** in `final_logs/`: Complete session logs with all prompts
- **`aggregate_*.txt`** in `aggregate_logs/`: Structured reports with per-file change tracking
- **`aggregate_summary_*.txt`** in `final_logs/`: High-level summaries of all aggregates
- **`aggregation_tracker.csv`**: CSV database tracking which temp files have been aggregated to prevent duplicate processing

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

Typical workflow for documenting a development session:

1. During development, prompts are automatically captured when you use `save_current_prompt`
2. When ready to analyze, call `aggregate_prompts` to create structured reports
3. Use `summarize_aggregates` to create a high-level overview
4. Archive the entire session with `save_all_prompts`
5. Optionally generate documentation with `create_readme`
6. Clean up with `clear_temp_logs` after aggregation

## Tips
Use larger models with prompt docu like claude sonnet 4.5 and others. 

The project is still in development stage, we request users to please create PRs if you see any limitations. 