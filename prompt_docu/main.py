#!/usr/bin/env python3

"""
Basic MCP Server Example

This is a minimal implementation of a Model Context Protocol server
that demonstrates the core concepts and structure.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Import toml library (tomllib for Python 3.11+, tomli for earlier versions)
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
    CallToolResult,
    CallToolRequest,
    ListToolsRequest,
)

# Import from prompt_docu modules
from prompt_docu.tools import TOOLS
from prompt_docu.helper import (
    save_prompt_to_file, 
    get_daily_folder_path, 
    aggregate_prompts,
    clear_temp_logs_folder,
    clear_aggregate_logs_folder,
    summarize_aggregate_files,
    create_readme_from_final
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """Example MCP Server implementation"""
    
    def __init__(self):
        logger.info("=== Initializing Prompt_docu Server ===")        
        self.server = Server("prompt-docu-server")
        
        # Load configuration from config.toml
        config = self._load_config()
        
        # Get current directory and construct base logs location
        current_dir = Path(__file__).parent.resolve()
        base_logs_location = current_dir / config['paths']['base_folder']
        
        # Construct subdirectory paths
        temp_logs_loc = base_logs_location / config['paths']['temp_logs']
        final_logs_loc = base_logs_location / config['paths']['final_logs']
        aggregate_logs_loc = base_logs_location / config['paths']['aggregate_logs']
        
        # Create all directories
        base_logs_location.mkdir(parents=True, exist_ok=True)
        temp_logs_loc.mkdir(parents=True, exist_ok=True)
        final_logs_loc.mkdir(parents=True, exist_ok=True)
        aggregate_logs_loc.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Base logs location: {base_logs_location.absolute()}")
        logger.info(f"Temp logs location: {temp_logs_loc.absolute()}")
        logger.info(f"Final logs location: {final_logs_loc.absolute()}")
        logger.info(f"Aggregate logs location: {aggregate_logs_loc.absolute()}")
        
        # Store paths for later use
        self.prompt_logs_dir = base_logs_location
        self.temp_logs_dir = temp_logs_loc
        self.final_logs_dir = final_logs_loc
        self.aggregate_logs_dir = aggregate_logs_loc
        
        # Note: Session files are now saved to temp_logs with daily folders
        # No need to create a session file here - it's created on first save
        self._setup_handlers()
    
    def _load_config(self) -> dict:
        """Load configuration from config.toml"""
        config_path = Path(__file__).parent / "config.toml"
        with open(config_path, 'rb') as f:
            return tomllib.load(f)
    
    def _setup_handlers(self):
        """Set up request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return TOOLS
        
        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent]:
            """Handle tool execution"""
            
            if name == "save_all_prompts":
                return await self._handle_save_all(arguments)
            elif name == "save_current_prompt":
                return await self._handle_save_current(arguments)
            elif name == "aggregate_prompts":
                return await self._handle_aggregate(arguments)
            elif name == "clear_temp_logs":
                return await self._handle_clear_temp(arguments)
            elif name == "clear_aggregate_logs":
                return await self._handle_clear_aggregate(arguments)
            elif name == "summarize_aggregates":
                return await self._handle_summarize_aggregates(arguments)
            elif name == "create_readme":
                return await self._handle_create_readme(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
    async def _handle_save_all(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle save all text tool - saves to final_logs"""
        message = arguments.get("message", "")
        file_names = arguments.get("file_names", [])
        logger.info(f"Message: {message}")
        logger.info(f"File names: {file_names}")
        
        # Create file with UTC timestamp in final_logs
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        file_path = self.final_logs_dir / f"all_prompts_{timestamp}.txt"
        
        result_message = save_prompt_to_file(
            file_path,
            message,
            file_names
        )
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]
    
    async def _handle_save_current(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle save current text tool - saves to temp_logs"""
        message = arguments.get("message", "")
        file_names = arguments.get("file_names", [])
        logger.info(f"Message: {message}")
        logger.info(f"File names: {file_names}")
        
        # Create file with UTC timestamp directly in temp_logs
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        file_path = self.temp_logs_dir / f"prompt_{timestamp}.txt"
        
        result_message = save_prompt_to_file(
            file_path,
            message,
            file_names
        )
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]
    
    async def _handle_aggregate(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle aggregate prompts tool"""
        message = arguments.get("message", "")
        file_names = arguments.get("file_names", [])
        logger.info(f"Aggregate - Message: {message}")
        logger.info(f"Aggregate - File names: {file_names}")
        logger.info("Starting prompt aggregation...")
        
        # First save the current prompt to temp logs before aggregating
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        file_path = self.temp_logs_dir / f"prompt_{timestamp}.txt"
        save_prompt_to_file(file_path, message, file_names)
        
        # Now aggregate all un-aggregated files
        result_message = aggregate_prompts(
            self.temp_logs_dir,
            self.aggregate_logs_dir
        )
        
        logger.info(f"Aggregation complete: {result_message}")
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]
    
    async def _handle_clear_temp(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle clear temp logs tool"""
        logger.info("Clearing temp logs folder...")
        
        result_message = clear_temp_logs_folder(self.temp_logs_dir)
        
        logger.info(f"Clear temp complete: {result_message}")
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]
    
    async def _handle_clear_aggregate(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle clear aggregate logs tool"""
        logger.info("Clearing aggregate logs folder...")
        
        result_message = clear_aggregate_logs_folder(self.aggregate_logs_dir)
        
        logger.info(f"Clear aggregate complete: {result_message}")
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]
    
    async def _handle_summarize_aggregates(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle summarize aggregates tool"""
        logger.info("Summarizing aggregate files...")
        
        result_message = summarize_aggregate_files(
            self.aggregate_logs_dir,
            self.final_logs_dir
        )
        
        logger.info(f"Summarize complete: {result_message}")
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]
    
    async def _handle_create_readme(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle create README tool"""
        logger.info("Creating README from final logs...")
        
        result_message = create_readme_from_final(
            self.final_logs_dir,
            self.prompt_logs_dir
        )
        
        logger.info(f"Create README complete: {result_message}")
        
        return [
            TextContent(
                type="text",
                text=result_message
            )
        ]

    
    async def run(self):
        """Run the server"""        
        async with stdio_server() as (read_stream, write_stream):            
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()

def cli():
    """CLI entry point for console script"""
    asyncio.run(main())

if __name__ == "__main__":
    cli()