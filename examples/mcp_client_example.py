from mcp.client import MCPClient
import json

def main():
    # Connect to MCP proxy server
    client = MCPClient("http://localhost:3000")
    
    # Example 1: Simple compilation
    print("\n=== Testing MCP Compile ===")
    
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
    
    result = client.call("rust-compiler", "compile", {"code": rust_code})
    print("Compilation result:", json.dumps(result, indent=2))
    
    # Example 2: Code with error that needs fixing
    print("\n=== Testing MCP Compile and Fix ===")
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
    
    result = client.call("rust-compiler", "compileAndFix", {
        "code": rust_code_with_error,
        "description": "A simple Hello World program",
        "max_attempts": 3
    })
    print("Compilation and fix result:", json.dumps(result, indent=2))
    
    # Example 3: Vector search
    print("\n=== Testing MCP Vector Search ===")
    result = client.call("rust-compiler", "vectorSearch", {
        "query": "how to implement a web server in Rust",
        "collection": "project_examples",
        "limit": 3
    })
    print("Vector search result:", json.dumps(result, indent=2))

if __name__ == "__main__":
    main()