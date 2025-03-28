import os
import json
import requests
from typing import Dict, List, Optional, Union

class LlamaEdgeClient:
    """Client for interacting with LlamaEdge OpenAI-compatible API"""
    
    def __init__(self, base_url: str = "http://localhost:8080/v1", 
                 llm_model: str = "Qwen2.5-Coder-3B-Instruct", 
                 embed_model: str = "gte-Qwen2-1.5B-instruct"):
        self.base_url = base_url
        self.llm_model = llm_model
        self.embed_model = embed_model
        
    def generate_text(self, 
                     prompt: str, 
                     system_message: str = "You are a helpful assistant with expertise in Rust programming.", 
                     max_tokens: int = 4000,
                     temperature: float = 0.7) -> str:
        """Generate text using the LLM"""
        
        url = f"{self.base_url}/chat/completions"
        
        # Using chatml format for Qwen2.5 models
        formatted_prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
        
        payload = {
            "model": self.llm_model,
            "prompt": formatted_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": ["<|im_end|>"]
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["text"].strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM API: {e}")
            return ""
            
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts"""
        
        url = f"{self.base_url}/embeddings"
        
        payload = {
            "model": self.embed_model,
            "input": texts
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return [item["embedding"] for item in result["data"]]
        except requests.exceptions.RequestException as e:
            print(f"Error getting embeddings: {e}")
            return []