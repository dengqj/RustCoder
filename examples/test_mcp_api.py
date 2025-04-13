import requests
import json

def test_mcp_api():
    """Test the MCP API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test simple compilation
    print("\n=== Testing MCP API: Simple Compilation ===")
    rust_code = """
    [filename: Cargo.toml]
    [package]
    name = "hello_world"
    version = "0.1.0"
    edition = "2021"
    
    [dependencies]
    
    [filename: src/main.rs]
    fn main() {
        println!("Hello from MCP API!");
    }
    """
    
    response = requests.post(
        f"{base_url}/mcp/compile",
        json={"code": rust_code}
    )
    
    print(f"Status code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # Test compilation with error fixing
    print("\n=== Testing MCP API: Compilation with Error Fixing ===")
    rust_code_with_error = """
    [filename: Cargo.toml]
    [package]
    name = "hello_world"
    version = "0.1.0"
    edition = "2021"
    
    [dependencies]
    
    [filename: src/main.rs]
    fn main() {
        println!("Hello from MCP API!" // Missing closing parenthesis
    }
    """
    
    response = requests.post(
        f"{base_url}/mcp/compile-and-fix",
        json={
            "code": rust_code_with_error,
            "description": "A simple hello world program",
            "max_attempts": 3
        }
    )
    
    print(f"Status code: {response.status_code}")
    # Handle the response safely
    try:
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error response: {response.text}")
    except requests.exceptions.JSONDecodeError:
        print(f"Failed to decode JSON response: {response.text}")

if __name__ == "__main__":
    test_mcp_api()