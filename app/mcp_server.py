import os
import json
import sys
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use FastMCP instead of direct Server inheritance
from mcp.server.fastmcp import FastMCP

from app.compiler import RustCompiler
from app.response_parser import ResponseParser
from app.vector_store import QdrantStore
from app.llm_client import LlamaEdgeClient
from app.mcp_service import RustCompilerMCP

# Create a RustMCPServer class for the run_mcp_server.py script
class RustMCPServer:
    def __init__(self, mcp_service):
        self.mcp = FastMCP("Rust Compiler")
        self.mcp_service = mcp_service
        
        # Register tools
        @self.mcp.tool()
        def compile(code: str) -> Dict[str, Any]:
            """Compile Rust code"""
            result = self.mcp_service.compile_rust_code(code)
            if result["success"]:
                return "success"
            else:
                return {"status": "error", "message": f"Compilation failed: {result.get('build_output', '')}"}
            
        @self.mcp.tool()
        def compileAndFix(code: str, description: str, max_attempts: int = 3) -> Dict[str, Any]:
            """Compile and fix Rust code"""
            result = self.mcp_service.compile_and_fix_rust_code(code, description, max_attempts)
            
            if result["success"]:
                # Format fixed files as raw text with filename markers
                output_text = ""
                for filename, content in result["final_files"].items():
                    output_text += f"[filename: {filename}]\n{content}\n\n"
                
                return output_text.strip()
            else:
                return {"status": "error", "message": f"Failed to fix code: {result.get('build_output', '')}"}
                
        @self.mcp.tool()
        def vectorSearch(query: str, collection: str, limit: int = 3) -> Dict[str, Any]:
            """Search vector database for similar examples"""
            embedding = self.mcp_service.llm_client.get_embeddings([query])[0]
            results = self.mcp_service.vector_store.search(collection, embedding, limit=limit)
            return {"results": results}
    
    def run(self, host="0.0.0.0", port=3001):
        """Run the MCP server"""
        # Set the server host and port using environment variables
        os.environ["MCP_HOST"] = host
        os.environ["MCP_PORT"] = str(port)
        
        print(f"Starting MCP server on {host}:{port}")
        # Use sse transport instead of http
        self.mcp.run(transport="sse")

# For direct invocation
mcp = FastMCP("Rust Compiler")
mcp_service = None  # Will be initialized in main

@mcp.tool()
def compile_and_fix(code: str, description: str, max_attempts: int = 3) -> Dict[str, Any]:
    """
    Compile and fix Rust code
    
    Args:
        code: Multi-file Rust code with [filename:] markers
        description: Project description for context
        max_attempts: Maximum number of attempts to fix errors
        
    Returns:
        Fixed code or error details
    """
    global mcp_service
    
    if not code or not description:
        return {"status": "error", "message": "Missing required parameters"}
        
    try:
        result = mcp_service.compile_and_fix_rust_code(code, description, max_attempts)
        
        if result["success"]:
            # Format fixed files as raw text with filename markers
            output_text = ""
            for filename, content in result["final_files"].items():
                output_text += f"[filename: {filename}]\n{content}\n\n"
            
            return output_text.strip()
        else:
            # For errors, return error message
            return {"status": "error", "message": f"Failed to fix code: {result.get('build_output', '')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# For the standalone mcp tool definitions

@mcp.tool()
def compile(code: str) -> Dict[str, Any]:
    """Compile Rust code"""
    global mcp_service
    
    if not code:
        return {"status": "error", "message": "Missing required parameters"}
        
    try:
        result = mcp_service.compile_rust_code(code)
        if result["success"]:
            return "success"
        else:
            return {"status": "error", "message": f"Compilation failed: {result.get('build_output', '')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def compileAndFix(code: str, description: str, max_attempts: int = 3) -> Dict[str, Any]:
    """Compile and fix Rust code"""
    global mcp_service
    
    if not code or not description:
        return {"status": "error", "message": "Missing required parameters"}
        
    try:
        result = mcp_service.compile_and_fix_rust_code(code, description, max_attempts)
        
        if result["success"]:
            # Format fixed files as raw text with filename markers
            output_text = ""
            for filename, content in result["final_files"].items():
                output_text += f"[filename: {filename}]\n{content}\n\n"
            
            return output_text.strip()
        else:
            return {"status": "error", "message": f"Failed to fix code: {result.get('build_output', '')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Only run server setup if script is executed directly
    # Initialize required components
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable not set")
    
    # Get embedding size from environment variable
    llm_embed_size = int(os.getenv("LLM_EMBED_SIZE", "1536"))
    
    # Initialize components
    llm_client = LlamaEdgeClient(api_key=api_key)
    vector_store = QdrantStore(embedding_size=llm_embed_size)

    # Create collections with error handling
    try:
        vector_store.create_collection("project_examples")
        print("Created collection: project_examples")
    except Exception as e:
        if "already exists" in str(e):
            print("Collection project_examples already exists")
        else:
            raise

    try:
        vector_store.create_collection("error_examples")
        print("Created collection: error_examples")
    except Exception as e:
        if "already exists" in str(e):
            print("Collection error_examples already exists")
        else:
            raise
    
    # Initialize MCP service
    mcp_service = RustCompilerMCP(vector_store=vector_store, llm_client=llm_client)
    
    # Determine transport mode from arguments or environment
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    
    # Run server with appropriate transport
    if transport == "stdio":
        # Run in STDIO mode
        mcp.run(transport="stdio")
    else:
        # Run in HTTP/SSE mode
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "3001"))
        print(f"Starting MCP server on {host}:{port}")
        os.environ["MCP_HOST"] = host
        os.environ["MCP_PORT"] = str(port)
        mcp.run(transport="sse")  # Using SSE transport