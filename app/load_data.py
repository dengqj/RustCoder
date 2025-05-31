# app/load_data.py
import json
import os
import uuid
from glob import glob
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore

def load_project_examples():
    """Load project examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    # Ensure collections exist
    vector_store.create_collection("project_examples")
    
    example_files = glob("data/project_examples/*.json")
    
    for file_path in example_files:
        with open(file_path, 'r') as f:
            example = json.load(f)
        
        # Get embedding for query
        embedding = llm_client.get_embeddings([example["query"]])[0]
        
        # Store in vector DB with proper UUID
        point_id = str(uuid.uuid4())  # Generate proper UUID
        
        vector_store.upsert("project_examples", 
                          [{"id": point_id,  # Use UUID instead of filename
                            "vector": embedding, 
                            "payload": example}])
        
        print(f"Loaded project example: {example['query']}")

def load_error_examples():
    """Load compiler error examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    # Ensure collections exist
    vector_store.create_collection("error_examples")
    
    error_files = glob("data/error_examples/*.json")
    
    for file_path in error_files:
        with open(file_path, 'r') as f:
            example = json.load(f)
        
        # Get embedding for error
        embedding = llm_client.get_embeddings([example["error"]])[0]

        # Store in vector DB with proper UUID
        point_id = str(uuid.uuid4())
        
        # Store in vector DB
        vector_store.upsert("error_examples", 
                           [{"id": point_id, 
                             "vector": embedding, 
                             "payload": example}])
        
        print(f"Loaded error example: {example['error'][:50]}...")

if __name__ == "__main__":
    load_project_examples()
    load_error_examples()
