import json
from typing import Dict, List, Optional
from app.vector_store import QdrantStore

class VectorStoreQueryTool:
    """Tool to allow the LLM to query the vector store directly"""
    
    def __init__(self):
        self.vector_store = QdrantStore()
        
    def query_examples(self, query: str, collection: str = "project_examples", limit: int = 3) -> str:
        """Allow the LLM to query the vector database for examples
        
        Args:
            query: The text to search for similar examples
            collection: Which collection to search ("project_examples" or "error_examples")
            limit: Maximum number of results
            
        Returns:
            JSON string with results
        """
        from app.llm_client import LlamaEdgeClient
        llm = LlamaEdgeClient()
        
        # Generate embedding for the query
        embedding = llm.get_embeddings([query])[0]
        
        # Search vector store
        results = self.vector_store.search(collection, embedding, limit=limit)
        
        # Format results as clean JSON
        formatted_results = []
        for result in results:
            if collection == "project_examples":
                formatted_results.append({
                    "query": result.get("query", ""),
                    "example": result.get("example", "")
                })
            else:  # error_examples
                formatted_results.append({
                    "error": result.get("error", ""),
                    "solution": result.get("solution", "")
                })
                
        return json.dumps(formatted_results, indent=2)