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
    """
      Generate a new Rust cargo project from the description and requirements. The input arguments are

        * description: a text string description of the generated Rust project.
        * requiremenets: functional requirements on what the generated Rust project.

      The return value is a text string that contains all files in the project. Each file is seperated by a [filename: path_to_file] line. For example, a project that contains a Cargo.toml file and a src/main.rs file will be returned as the following.

[filename: Cargo.toml]
[package]
name = "a_command_line_calcu"
version = "0.1.0"
edition = "2021"

[dependencies]


[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}

    """

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE_URL}/generate-sync", json={'description': description, 'requirements': requirements})
            response.raise_for_status()

            resp_json = json.loads(response.text)
            if "combined_text" in resp_json:
                return resp_json["combined_text"]
            else:
                return "Rust project creation error."
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Error trying to generate a Rust project: {str(e)}"

@mcp.tool()
async def compile_and_fix(code: str, description: str = "A Rust project", max_attempts: int = 3) -> str:
    """
        Compile a Rust cargo project and fix any compiler errors.

        The argument `code` is a text string that contains all files in the project. Each file is seperated by a [filename: path_to_file] line. For example, a project that contains a Cargo.toml file and a src/main.rs file will be returned as the following.

[filename: Cargo.toml]
[package]
name = "a_command_line_calcu"
version = "0.1.0"
edition = "2021"

[dependencies]


[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}

        The return value is also a text string that contains all files in the project. It is in the same format as the input `code` argument.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/compile-and-fix", 
                json={'code': code, 'description': description, 'max_attempts': max_attempts}
            )
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            if "combined_text" in resp_json:
                return resp_json["combined_text"]
            else:
                return "Cannot fix the Rust compiler error."
            # return response.text
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Error trying to fixing the Rust compiler error: {str(e)}"

@mcp.tool()
async def compile(code: str) -> str:
    """
        Compile a Rust cargo project and return the compiler output.

        The argument `code` is a text string that contains all files in the project. Each file is seperated by a [filename: path_to_file] line. For example, a project that contains a Cargo.toml file and a src/main.rs file will be returned as the following.

[filename: Cargo.toml]
[package]
name = "a_command_line_calcu"
version = "0.1.0"
edition = "2021"

[dependencies]


[filename: src/main.rs]
fn main() {
    println!("Hello, world!");
}

        The return value is a text string that contains the Rust compiler output.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE_URL}/compile", json={'code': code})
            response.raise_for_status()
            
            resp_json = json.loads(response.text)
            if "build_output" in resp_json:
                return resp_json["build_output"]
            else:
                return "Rust compiler error."
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return f"Rust compiler error: {str(e)}"

if __name__ == "__main__":
    # Use transport from environment variable or default to stdio
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    print(f"Starting MCP server with {transport} transport")
    print(f"API URL: {API_BASE_URL}")
    mcp.run(transport=transport)
