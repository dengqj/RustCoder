from app.mcp_server import RustMCPServer
from app.mcp_service import RustCompilerMCP
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore
from app.compiler import RustCompiler
from app.response_parser import ResponseParser
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    # Initialize components
    api_key = os.getenv("LLM_API_KEY")
    llm_embed_size = int(os.getenv("LLM_EMBED_SIZE", "1536"))
    
    # Get LLM API base URL
    llm_api_base = os.getenv("LLM_API_BASE", "https://coder.gaia.domains/v1")
    llm_model = os.getenv("LLM_MODEL", "Qwen2.5-Coder-32B-Instruct-Q5_K_M")
    
    llm_client = LlamaEdgeClient(api_key=api_key, api_base=llm_api_base, model=llm_model)
    
    # Get Qdrant host and port from environment variables (for Docker)
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    vector_store = QdrantStore(embedding_size=llm_embed_size, host=qdrant_host, port=qdrant_port)
    vector_store.create_collection("project_examples")
    vector_store.create_collection("error_examples")
    
    # Initialize MCP service
    mcp_service = RustCompilerMCP(vector_store=vector_store, llm_client=llm_client)
    
    # Create and run MCP server
    server = RustMCPServer(mcp_service)
    
    print("Starting MCP server on 0.0.0.0:3001")
    server.run(host="0.0.0.0", port=3001)

if __name__ == "__main__":
    main()