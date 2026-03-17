#!/usr/bin/env python3

"""
Prompt Documentation MCP Server — Sequential Thinking Pattern

A Model Context Protocol server whose primary tool, ``document_prompt``,
follows the Sequential Thinking pattern:

  1.  ONE tool is called repeatedly — once per prompt / thought.
  2.  Each call **saves the prompt first** (documentation before execution).
  3.  The server maintains an in-memory thought-chain across calls.
  4.  When ``nextPromptNeeded`` becomes ``false``, the full documentation
      pipeline runs automatically (aggregate → summarise → README).

Utility tools (``save_all_prompts``, ``clear_temp_logs``,
``clear_aggregate_logs``, ``create_readme``) are available alongside.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# toml compat
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("Please install tomli: pip install tomli")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

from prompt_docu.tools import TOOLS
from prompt_docu.helper import (
    save_prompt_sequential,
    save_prompt_to_file,
    aggregate_prompts,
    clear_temp_logs_folder,
    clear_aggregate_logs_folder,
    summarize_aggregate_files,
    create_readme_from_final,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  MCPServer — Sequential Thinking Architecture
# ═════════════════════════════════════════════════════════════════════════════

class MCPServer:
    """Prompt-documentation MCP server using the Sequential Thinking pattern."""

    # ── Initialisation ───────────────────────────────────────────────────

    def __init__(self):
        logger.info("=== Initialising Prompt_docu Server (Sequential Thinking) ===")
        self.server = Server("prompt-docu-server")

        config = self._load_config()

        current_dir = Path(__file__).parent.resolve()
        base = current_dir / config["paths"]["base_folder"]

        self.prompt_logs_dir   = base
        self.temp_logs_dir     = base / config["paths"]["temp_logs"]
        self.final_logs_dir    = base / config["paths"]["final_logs"]
        self.aggregate_logs_dir = base / config["paths"]["aggregate_logs"]

        for d in (self.prompt_logs_dir, self.temp_logs_dir,
                  self.final_logs_dir, self.aggregate_logs_dir):
            d.mkdir(parents=True, exist_ok=True)

        logger.info(f"Temp logs   : {self.temp_logs_dir}")
        logger.info(f"Final logs  : {self.final_logs_dir}")
        logger.info(f"Aggregate   : {self.aggregate_logs_dir}")

        # ── Sequential-thinking state ────────────────────────────────────
        self.prompt_history: List[Dict[str, Any]] = []
        self.branches: Dict[str, List[int]] = {}   # branchId → [promptNumbers]

        self._setup_handlers()

    # ── Config ───────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent / "config.toml"
        with open(config_path, "rb") as f:
            return tomllib.load(f)

    # ── Handler wiring ───────────────────────────────────────────────────

    def _setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return TOOLS

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            if name == "document_prompt":
                return await self._handle_document_prompt(arguments)
            elif name == "save_all_prompts":
                return await self._handle_save_all(arguments)
            elif name == "clear_temp_logs":
                return await self._handle_clear_temp(arguments)
            elif name == "clear_aggregate_logs":
                return await self._handle_clear_aggregate(arguments)
            elif name == "create_readme":
                return await self._handle_create_readme(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

    # ─────────────────────────────────────────────────────────────────────
    #  PRIMARY HANDLER — Sequential Thinking document_prompt
    # ─────────────────────────────────────────────────────────────────────

    async def _handle_document_prompt(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """
        Core sequential-thinking handler.

        Lifecycle per call:
          1. **SAVE FIRST** — persist the prompt to ``temp_logs/`` with full
             chain metadata.
          2. Update in-memory thought history (revisions & branches).
          3. If ``nextPromptNeeded`` is ``false`` → run the automatic pipeline
             (aggregate → summarise → README).
          4. Return a JSON status payload identical in shape to the
             ``sequentialthinking`` MCP response.
        """
        # ── Extract parameters ───────────────────────────────────────────
        message             = arguments.get("message", "")
        file_names          = arguments.get("file_names", [])
        prompt_number       = arguments.get("promptNumber", 1)
        total_prompts       = arguments.get("totalPrompts", 1)
        next_prompt_needed  = arguments.get("nextPromptNeeded", True)
        is_revision         = arguments.get("isRevision", False)
        revises_prompt      = arguments.get("revisesPrompt")
        branch_from_prompt  = arguments.get("branchFromPrompt")
        branch_id           = arguments.get("branchId")
        needs_more_prompts  = arguments.get("needsMorePrompts", False)

        logger.info(
            f"document_prompt #{prompt_number}/{total_prompts}  "
            f"next={next_prompt_needed}  revision={is_revision}"
        )

        # ── STEP 1: SAVE FIRST ──────────────────────────────────────────
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = self.temp_logs_dir / f"prompt_{timestamp}.txt"

        save_result = save_prompt_sequential(
            file_path=file_path,
            message=message,
            file_names=file_names,
            prompt_number=prompt_number,
            total_prompts=total_prompts,
            next_prompt_needed=next_prompt_needed,
            is_revision=is_revision,
            revises_prompt=revises_prompt,
            branch_from_prompt=branch_from_prompt,
            branch_id=branch_id,
            needs_more_prompts=needs_more_prompts,
        )
        logger.info(f"  Saved: {save_result}")

        # ── STEP 2: Update in-memory history ─────────────────────────────
        entry: Dict[str, Any] = {
            "promptNumber": prompt_number,
            "totalPrompts": total_prompts,
            "message": message[:200],  # keep memory lean
            "file_names": file_names,
            "isRevision": is_revision,
            "revisesPrompt": revises_prompt,
            "branchFromPrompt": branch_from_prompt,
            "branchId": branch_id,
            "timestamp": timestamp,
            "savedTo": file_path.name,
        }

        # Mark the original prompt as revised
        if is_revision and revises_prompt is not None:
            for h in self.prompt_history:
                if h["promptNumber"] == revises_prompt:
                    if h.get("branchId") == branch_id:
                        h["revisedBy"] = prompt_number

        # Track branches
        if branch_id:
            self.branches.setdefault(branch_id, []).append(prompt_number)

        self.prompt_history.append(entry)

        # ── STEP 3: Auto-pipeline when chain ends ────────────────────────
        pipeline_report = ""
        if not next_prompt_needed:
            logger.info("  Chain complete — running automatic pipeline …")
            pipeline_report = self._run_pipeline()

        # ── STEP 4: Build response (mirrors sequentialthinking shape) ────
        response_payload = {
            "promptNumber": prompt_number,
            "totalPrompts": total_prompts,
            "nextPromptNeeded": next_prompt_needed,
            "branches": list(self.branches.keys()),
            "promptHistoryLength": len(self.prompt_history),
            "savedTo": file_path.name,
        }

        response_text = json.dumps(response_payload)
        if pipeline_report:
            response_text += f"\n\n--- Pipeline Report ---\n{pipeline_report}"

        return [TextContent(type="text", text=response_text)]

    # ── Automatic pipeline (runs when chain ends) ────────────────────────

    def _run_pipeline(self) -> str:
        """
        Sequential documentation pipeline triggered when
        ``nextPromptNeeded`` is ``false``.

        Steps (each completes before the next starts):
          1. Aggregate un-aggregated temp logs
          2. Summarise aggregates into final_logs
          3. Generate README.md
        """
        steps: List[str] = []

        # Step 1 — Aggregate
        logger.info("  Pipeline Step 1: Aggregating …")
        r1 = aggregate_prompts(self.temp_logs_dir, self.aggregate_logs_dir)
        steps.append(f"[Step 1 — Aggregate] {r1}")
        logger.info(f"    {r1}")

        # Step 2 — Summarise
        logger.info("  Pipeline Step 2: Summarising …")
        r2 = summarize_aggregate_files(self.aggregate_logs_dir, self.final_logs_dir)
        steps.append(f"[Step 2 — Summarise] {r2}")
        logger.info(f"    {r2}")

        # Step 3 — README
        logger.info("  Pipeline Step 3: README …")
        r3 = create_readme_from_final(self.final_logs_dir, self.prompt_logs_dir)
        steps.append(f"[Step 3 — README] {r3}")
        logger.info(f"    {r3}")

        return "\n".join(steps)

    # ─────────────────────────────────────────────────────────────────────
    #  UTILITY HANDLERS
    # ─────────────────────────────────────────────────────────────────────

    async def _handle_save_all(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Bulk-save all session prompts to final_logs."""
        message = arguments.get("message", "")
        file_names = arguments.get("file_names", [])

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = self.final_logs_dir / f"all_prompts_{timestamp}.txt"

        result = save_prompt_to_file(file_path, message, file_names)
        return [TextContent(type="text", text=result)]

    async def _handle_clear_temp(self, arguments: dict[str, Any]) -> list[TextContent]:
        result = clear_temp_logs_folder(self.temp_logs_dir)
        return [TextContent(type="text", text=result)]

    async def _handle_clear_aggregate(self, arguments: dict[str, Any]) -> list[TextContent]:
        result = clear_aggregate_logs_folder(self.aggregate_logs_dir)
        return [TextContent(type="text", text=result)]

    async def _handle_create_readme(self, arguments: dict[str, Any]) -> list[TextContent]:
        result = create_readme_from_final(self.final_logs_dir, self.prompt_logs_dir)
        return [TextContent(type="text", text=result)]

    # ── Run ──────────────────────────────────────────────────────────────

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


# ═════════════════════════════════════════════════════════════════════════════
#  Entry-points
# ═════════════════════════════════════════════════════════════════════════════

async def main():
    server = MCPServer()
    await server.run()


def cli():
    asyncio.run(main())


if __name__ == "__main__":
    cli()