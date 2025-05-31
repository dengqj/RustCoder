import json
import os
import uuid
from glob import glob
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore
import logging

PROJECT_COLLECTION = "project_examples"
ERROR_COLLECTION = "error_examples"
PROJECT_DATA_PATH = "data/project_examples/*.json"
ERROR_DATA_PATH = "data/error_examples/*.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_examples(vector_store, llm_client, collection_name, file_pattern, text_key):
    """Load examples into vector database"""
    # Ensure collections exist
    vector_store.create_collection(collection_name)
    
    example_files = glob(file_pattern)
    
    # Collect all embeddings and metadata first
    embeddings = []
    metadata = []
    
    for file_path in example_files:
        with open(file_path, 'r') as f:
            example = json.load(f)
        
        # Get embedding for query or error
        try:
            embedding = llm_client.get_embeddings([example[text_key]])[0]
            embeddings.append(embedding)
            metadata.append(example)
            logger.info(f"Loaded {collection_name[:-1]} example: {example[text_key][:50]}...")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    # Insert all documents in a single batch
    if embeddings:
        vector_store.insert_documents(collection_name, embeddings, metadata)

def load_project_examples():
    """Load project examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    load_examples(vector_store, llm_client, PROJECT_COLLECTION, PROJECT_DATA_PATH, "query")

def load_error_examples():
    """Load compiler error examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    load_examples(vector_store, llm_client, ERROR_COLLECTION, ERROR_DATA_PATH, "error")

if __name__ == "__main__":
    load_project_examples()
    load_error_examples()
