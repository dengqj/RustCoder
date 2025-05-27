import httpx
import sys
import json
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Rust compiler tools")

@mcp.tool()
async def generate(description: str, requirements: str) -> str:
    """Generate a new Rust cargo project from the description and requirements"""

    async with httpx.AsyncClient() as client:
        response = await client.post("http://host.docker.internal:8000/generate-sync", json={'description': description, 'requirements': requirements})
        return response.text

@mcp.tool()
async def compile_and_fix(code: str) -> str:
    """Compile a Rust cargo project and fix any compiler errors"""

    async with httpx.AsyncClient() as client:
        response = await client.post("http://host.docker.internal:8000/compile-and-fix", json={'code': code, 'description': 'A Rust project', 'max_attempts': 3})
        return response.text

if __name__ == "__main__":
    mcp.run(transport="stdio")
