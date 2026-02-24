#!/usr/bin/env python3
"""
Entry point for running prompt_docu as a module
"""

from prompt_docu.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
