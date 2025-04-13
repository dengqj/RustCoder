import requests
import json
from pprint import pprint

# Base URL of your MCP service
BASE_URL = "http://localhost:8000"

def test_simple_compilation():
    """Test simple Rust code compilation"""
    print("\n=== Testing Simple Compilation ===")
    
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
    
    # Send compilation request
    response = requests.post(
        f"{BASE_URL}/mcp/compile",
        json={"code": rust_code}
    )
    
    # Print response
    pprint(response.json())
    
def test_code_with_error():
    """Test code with compilation error that needs fixing"""
    print("\n=== Testing Code with Error ===")
    
    # Example Rust code with error
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
    
    # Send compile-and-fix request
    response = requests.post(
        f"{BASE_URL}/mcp/compile-and-fix",
        json={
            "code": rust_code_with_error,
            "description": "A simple Hello World program",
            "max_attempts": 3
        }
    )
    
    # Print response
    pprint(response.json())

if __name__ == "__main__":
    test_simple_compilation()
    test_code_with_error()