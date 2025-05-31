import os
import uuid
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client import models  # Add this import
from glob import glob
import json
from app.llm_client import LlamaEdgeClient  # Adjust the import based on your project structure

class QdrantStore:
    """Interface for Qdrant vector database"""
    
    def __init__(self, url: Optional[str] = None, 
                 api_key: Optional[str] = None,
                 local_path: Optional[str] = None,
                 embedding_size: int = 1536):
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.embedding_size = embedding_size
        
        if url and api_key:  # Cloud Qdrant
            self.client = QdrantClient(url=url, api_key=api_key)
        elif local_path:     # Local Qdrant
            self.client = QdrantClient(path=local_path)
        else:                # Default local Qdrant
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            
    def create_collection(self, name: str, vector_size: Optional[int] = None):
        """Create a new collection if it doesn't exist"""
        if vector_size is None:
            vector_size = self.embedding_size
            
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if name not in collection_names:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"Created collection: {name}")
            else:
                print(f"Collection {name} already exists")
        except Exception as e:
            # Check if error is about collection already existing
            if "already exists" in str(e):
                print(f"Collection {name} already exists (caught exception)")
            else:
                # Re-raise if it's a different error
                raise
            
    def insert_documents(self, collection_name: str, embeddings: List[List[float]], 
                        metadata: List[Dict[str, Any]]):
        """Insert documents with embeddings and metadata into collection"""
        points = []
        for embedding, meta in zip(embeddings, metadata):
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),  # Using UUID instead of index
                vector=embedding,
                payload=meta
            ))
            
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
    def search(self, collection_name: str, query_vector: List[float], 
              limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in collection"""
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return [hit.payload for hit in results]

    def upsert(self, collection_name: str, points: List[Dict[str, Any]]):
        """Upsert points to collection with id, vector, and payload"""
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def add_item(self, collection_name, vector, item):
        """
        Add an item to a collection with its vector embedding
        
        Args:
            collection_name: Name of the collection
            vector: Vector embedding
            item: Payload dictionary
        """
        try:
            # Add unique ID for this item
            item_id = str(uuid.uuid4())
            
            # Add to collection
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=item_id,
                        vector=vector,
                        payload=item
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Error adding item to collection {collection_name}: {e}")
            return False

    def count(self, collection_name: str) -> int:
        """Get the number of items in a collection"""
        try:
            collection_info = self.client.get_collection(collection_name=collection_name)
            return collection_info.vectors_count
        except Exception as e:
            print(f"Error getting count for collection {collection_name}: {e}")
            return 0

def load_project_examples():
    """Load project examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    # Ensure collections exist
    vector_store.create_collection("project_examples")
    
    example_files = glob("data/project_examples/*.json")
    
    embeddings = []
    metadata = []
    
    for file_path in example_files:
        with open(file_path, 'r') as f:
            example = json.load(f)
        
        # Get embedding for query
        embedding = llm_client.get_embeddings([example["query"]])[0]
        
        embeddings.append(embedding)
        metadata.append(example)
        
        print(f"Loaded project example: {example['query']}")
    
    # Insert all documents in a single batch
    if embeddings:
        vector_store.insert_documents("project_examples", embeddings, metadata)