import httpx
import sys
import json
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Get API host from environment variable or use default
# Use localhost as default for non-Docker environments
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

mcp = FastMCP("Rust compiler tools")

@mcp.tool()
async def generate(description: str, requirements: str) -> str:
    """Generate a new Rust cargo project from the description and requirements"""

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/generate-sync", json={'description': description, 'requirements': requirements})
        return response.text

@mcp.tool()
async def compile_and_fix(code: str, description: str = "A Rust project", max_attempts: int = 3) -> str:
    """Compile a Rust cargo project and fix any compiler errors"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/compile-and-fix", 
                json={'code': code, 'description': description, 'max_attempts': max_attempts}
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Error calling compile-and-fix API: {str(e)}"

@mcp.tool()
async def compile(code: str) -> str:
    """Compile a Rust cargo project"""

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/compile", json={'code': code})
        return response.text

if __name__ == "__main__":
    # Use transport from environment variable or default to stdio
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    print(f"Starting MCP server with {transport} transport")
    print(f"API URL: {API_BASE_URL}")
    mcp.run(transport=transport)
