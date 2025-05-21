import os
from app.mcp_server import RustMCPServer
from app.vector_store import QdrantStore
from app.llm_client import LlamaEdgeClient
from app.mcp_service import RustCompilerMCP
from dotenv import load_dotenv

def main():
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

    # Create collections
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
    
    # Initialize service and server
    mcp_service = RustCompilerMCP(vector_store=vector_store, llm_client=llm_client)
    server = RustMCPServer(mcp_service)
    
    # Start the server
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "3001"))
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()