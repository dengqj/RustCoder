import requests
import json
from pprint import pprint

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_vector_search():
    """Test the vector search endpoint"""
    print("\n=== Testing Vector Search API ===")
    
    # Example 1: Search for project examples
    search_data = {
        "query": "how to build a Rust web server",
        "collection": "project_examples",
        "limit": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/vector-search",
            json=search_data
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            pprint(response.json())
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
        
    # Example 2: Search for error examples
    search_data = {
        "query": "cannot borrow as mutable",
        "collection": "error_examples",
        "limit": 2
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/vector-search",
            json=search_data
        )
        
        print(f"\nStatus code: {response.status_code}")
        if response.status_code == 200:
            pprint(response.json())
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_vector_search()