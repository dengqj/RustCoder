import os
import json
import sys
from typing import Dict, Any, Optional, List

from mcp.server import MCPServer, Response
from mcp.runner import MCPRunner
from mcp.types import MethodCall, Resource, Status

from app.compiler import RustCompiler
from app.response_parser import ResponseParser
from app.vector_store import QdrantStore
from app.llm_client import LlamaEdgeClient
from app.mcp_service import RustCompilerMCP


class RustMCPServer(MCPServer):
    def __init__(self):
        super().__init__("rust-compiler-mcp")
        
        # Initialize services
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY environment variable not set")
            
        # Initialize components
        self.llm_client = LlamaEdgeClient(api_key=api_key)
        self.vector_store = QdrantStore()
        self.vector_store.create_collection("project_examples")
        self.vector_store.create_collection("error_examples")
        
        # Set up the RustCompilerMCP
        self.mcp_service = RustCompilerMCP(vector_store=self.vector_store, llm_client=self.llm_client)
        
        # Register methods
        self.register_method("compile", self.compile_code)
        self.register_method("compileAndFix", self.compile_and_fix_code)
        self.register_method("vectorSearch", self.vector_search)

    def compile_code(self, call: MethodCall) -> Response:
        """Compile Rust code"""
        code = call.params.get("code", "")
        if not code:
            return Response(status=Status.ERROR, result={"error": "Missing code parameter"})
            
        try:
            result = self.mcp_service.compile_rust_code(code)
            return Response(
                status=Status.SUCCESS if result["success"] else Status.ERROR,
                result=result
            )
        except Exception as e:
            return Response(status=Status.ERROR, result={"error": str(e)})

    def compile_and_fix_code(self, call: MethodCall) -> Response:
        """Compile and fix Rust code"""
        code = call.params.get("code", "")
        description = call.params.get("description", "")
        max_attempts = int(call.params.get("max_attempts", 3))
        
        if not code or not description:
            return Response(status=Status.ERROR, result={"error": "Missing required parameters"})
            
        try:
            result = self.mcp_service.compile_and_fix_rust_code(code, description, max_attempts)
            return Response(
                status=Status.SUCCESS if result["success"] else Status.ERROR,
                result=result
            )
        except Exception as e:
            return Response(status=Status.ERROR, result={"error": str(e)})

    def vector_search(self, call: MethodCall) -> Response:
        """Search vector database for similar examples"""
        query = call.params.get("query", "")
        collection = call.params.get("collection", "project_examples")
        limit = int(call.params.get("limit", 5))
        
        if not query:
            return Response(status=Status.ERROR, result={"error": "Missing query parameter"})
            
        try:
            result = self.mcp_service.vector_search(query, collection, limit)
            return Response(
                status=Status.SUCCESS if result["success"] else Status.ERROR,
                result=result
            )
        except Exception as e:
            return Response(status=Status.ERROR, result={"error": str(e)})


if __name__ == "__main__":
    # Create and run the MCP server
    server = RustMCPServer()
    
    # Run the server with STDIO communication
    runner = MCPRunner(server)
    runner.run(sys.stdin, sys.stdout)