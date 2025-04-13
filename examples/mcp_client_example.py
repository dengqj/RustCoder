import requests
import json
from typing import Dict, Optional


class MCPClient:
    """Client for the Rust Compiler MCP service"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def compile_rust_code(self, code_content: str) -> Dict:
        """
        Call the MCP service to compile Rust code
        
        Args:
            code_content: String containing Rust code with file markers
            
        Returns:
            Dict with compilation status, output, and error messages
        """
        response = requests.post(
            f"{self.base_url}/mcp/compile",
            json={"code": code_content}
        )
        return response.json()
    
    def compile_and_fix_rust_code(
        self, 
        code_content: str, 
        description: str,
        max_attempts: int = 3
    ) -> Dict:
        """
        Call the MCP service to compile and fix Rust code
        
        Args:
            code_content: String containing Rust code with file markers
            description: Project description for context
            max_attempts: Maximum attempts to fix compilation errors
            
        Returns:
            Dict with compilation status, output, fixes applied, and final code
        """
        response = requests.post(
            f"{self.base_url}/mcp/compile-and-fix",
            json={
                "code": code_content,
                "description": description,
                "max_attempts": max_attempts
            }
        )
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize MCP client
    mcp_client = MCPClient()
    
    # Example Rust code with multiple files
    rust_code = """
    [filename: Cargo.toml]
    [package]
    name = "hello_world"
    version = "0.1.0"
    edition = "2021"
    
    [dependencies]
    
    [filename: src/main.rs]
    fn main() {
        println!("Hello, World!");
    }
    """
    
    # Example 1: Simple compilation
    result = mcp_client.compile_rust_code(rust_code)
    print("Compilation result:", json.dumps(result, indent=2))
    
    # Example 2: Code with error that needs fixing
    rust_code_with_error = """
    [filename: Cargo.toml]
    [package]
    name = "hello_world"
    version = "0.1.0"
    edition = "2021"
    
    [dependencies]
    
    [filename: src/main.rs]
    fn main() {
        println!("Hello, World!" // Missing closing parenthesis
    }
    """
    
    result = mcp_client.compile_and_fix_rust_code(
        rust_code_with_error,
        "A simple Hello World program"
    )
    print("Compilation and fix result:", json.dumps(result, indent=2))