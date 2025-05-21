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
    
    llm_client = LlamaEdgeClient(api_key=api_key)
    vector_store = QdrantStore(embedding_size=llm_embed_size)
    
    # Initialize MCP service
    mcp_service = RustCompilerMCP(vector_store=vector_store, llm_client=llm_client)
    
    # Create and run MCP server
    server = RustMCPServer(mcp_service)
    server.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    main()