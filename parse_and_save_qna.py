# parse_and_save_qna.py
import re
import os
import json
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore
from sentence_transformers import SentenceTransformer
from qdrant_client.http import models

def parse_qna_file(file_path):
    """Parse the QnA_pair.txt file into question-answer pairs"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract questions and answers
    qa_pairs = []
    pattern = r'Q\d+:\s*(.*?)\nA\d+:\s*```rust(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for i, (question, answer) in enumerate(matches):
        qa_pairs.append({
            "query": question.strip(),
            "example": answer.strip()
        })
    
    return qa_pairs

def save_to_qdrant(qa_pairs):
    """Save the parsed QA pairs to Qdrant"""
    # Use local file path instead of server connection
    vector_store = QdrantStore(local_path="./qdrant_local_storage")
    
    # Use sentence-transformers for embeddings instead of LlamaEdge
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast model
    
    # Ensure collection exists
    vector_store.create_collection("project_examples", vector_size=384)  # MiniLM has 384 dimensions
    
    for i, qa_pair in enumerate(qa_pairs):
        # Get embedding with sentence-transformers
        embedding = model.encode(qa_pair["query"]).tolist()
        
        # Create proper PointStruct objects
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=qa_pair
        )
        
        # Store in vector DB using proper PointStruct
        vector_store.client.upsert(
            collection_name="project_examples",
            points=[point]
        )
        
        print(f"Loaded project example {i}: {qa_pair['query'][:50]}...")

def main():
    qna_file = "c:/Users/arnav/OneDrive/Desktop/Lfx_wasmedge_try/Project3/data/project_examples/QnA_pair.txt"
    qa_pairs = parse_qna_file(qna_file)
    save_to_qdrant(qa_pairs)
    print(f"Successfully saved {len(qa_pairs)} Q&A pairs to Qdrant")

if __name__ == "__main__":
    main()