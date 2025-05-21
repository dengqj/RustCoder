import os
import json
import sys
from typing import Dict, Any, Optional, List

# Update this import
from mcp.server import Server, Response, Status, MethodCall
from mcp.runner import MCPRunner

from app.compiler import RustCompiler
from app.response_parser import ResponseParser
from app.vector_store import QdrantStore
from app.llm_client import LlamaEdgeClient
from app.mcp_service import RustCompilerMCP


class RustMCPServer(Server):
    def __init__(self, mcp_service):
        self.mcp_service = mcp_service
        super().__init__()
        
    def compile_and_fix(self, call: MethodCall) -> Response:
        """Compile and fix Rust code according to MCP standard"""
        code = call.params.get("code", "")
        description = call.params.get("description", "")
        max_attempts = int(call.params.get("max_attempts", 3))
        
        if not code or not description:
            return Response(status=Status.ERROR, result="Missing required parameters")
            
        try:
            result = self.mcp_service.compile_and_fix_rust_code(code, description, max_attempts)
            
            if result["success"]:
                # Format fixed files as raw text with filename markers
                output_text = ""
                for filename, content in result["final_files"].items():
                    output_text += f"[filename: {filename}]\n{content}\n\n"
                
                # Return raw text instead of JSON
                return Response(status=Status.SUCCESS, result=output_text.strip())
            else:
                # For errors, return error message
                return Response(status=Status.ERROR, result=f"Failed to fix code: {result.get('build_output', '')}")
        except Exception as e:
            return Response(status=Status.ERROR, result=str(e))


if __name__ == "__main__":
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
    parser = ResponseParser()
    compiler = RustCompiler()
    
    # Initialize vector store
    vector_store = QdrantStore(embedding_size=llm_embed_size)
    vector_store.create_collection("project_examples")
    vector_store.create_collection("error_examples")
    
    # Initialize MCP service
    mcp_service = RustCompilerMCP(vector_store=vector_store, llm_client=llm_client)
    
    # Create and run the MCP server
    server = RustMCPServer(mcp_service)
    
    # Run the server with STDIO communication
    runner = MCPRunner(server)
    runner.run(sys.stdin, sys.stdout)