# parse_and_save_qna.py
import re
import os
import json
import uuid
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore

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
    vector_store = QdrantStore()  # Uses local Qdrant by default
    llm_client = LlamaEdgeClient()
    
    # Ensure collection exists
    vector_store.create_collection("project_examples")
    
    for i, qa_pair in enumerate(qa_pairs):
        # Get embedding for query
        embedding = llm_client.get_embeddings([qa_pair["query"]])[0]
        
        # Store in vector DB - using UUID
        vector_store.upsert("project_examples", 
                           [{"id": str(uuid.uuid4()),  # Generate a UUID
                             "vector": embedding, 
                             "payload": qa_pair}])
        
        print(f"Loaded project example {i}: {qa_pair['query'][:50]}...")

def main():
    qna_file = "c:/Users/arnav/OneDrive/Desktop/Lfx_wasmedge_try/Project3/data/project_examples/QnA_pair.txt"
    qa_pairs = parse_qna_file(qna_file)
    save_to_qdrant(qa_pairs)
    print(f"Successfully saved {len(qa_pairs)} Q&A pairs to Qdrant")

if __name__ == "__main__":
    main()