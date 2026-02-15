# Prompt Docu

> A minimal Model Context Protocol (MCP) server for logging, tracking, and documenting development prompts.

## Overview

**Prompt Docu** is a lightweight tool designed to capture the context of your development sessions. It runs as an MCP server and provides utilities to save prompts, track file contexts, and aggregate logs into structured reports.

## Features

This server exposes three core tools to help manage your workflow:

- **`save_current_prompt`**  
  Captures the current prompt and list of active file contexts, saving them to a temporary log.

- **`save_all_prompts`**  
  Archives the entire session's prompts and file history into a timestamped final log.

- **`aggregate_prompts`**  
  Processes scattered temporary logs and compiles them into a single, comprehensive report.

## Directory Structure

The server organizes logs automatically based on your configuration:

```
prompt_logs/
├── temp_logs/       # Individual prompt captures
├── final_logs/      # Complete session archives
└── aggregate_logs/  # Compiled reports
```

## Configuration

Paths and settings are managed in `config.toml`. You can customize the base folder and subdirectory names to fit your project structure.

```toml
[paths]
base_folder = "prompt_logs"
temp_logs = "temp_logs"
final_logs = "final_logs"
aggregate_logs = "aggregate_logs"
```

## Usage

1.  **Install Dependencies**  
    Ensure you have the required packages installed:
    ```bash
    pip install mcp
    # For Python < 3.11: pip install tomli
    ```

2.  **Run the Server**  
    Start the MCP server:
    ```bash
    python main.py
    ```

3.  **Connect**  
    Configure your MCP client (e.g., Claude Desktop, VS Code) to use this server.

---
*Generated for the Prompt Docu project.*
