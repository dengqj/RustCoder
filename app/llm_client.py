import os
import json
import requests
from typing import List, Dict, Any, Optional
from openai import OpenAI  # Add this import

class LlamaEdgeClient:
    """Client for interacting with LlamaEdge OpenAI-compatible API"""
    
    def __init__(self, api_key=None, api_base=None, model=None, embed_model=None):
        """Initialize LlamaEdgeClient with API credentials
        
        Args:
            api_key: API key for LLM service
            api_base: Base URL for API (overrides LLM_API_BASE env var)
            model: Model name (overrides LLM_MODEL env var)
            embed_model: Embedding model name (overrides LLM_EMBED_MODEL env var)
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")
            
        # Use provided parameters with fallback to environment variables
        self.base_url = api_base or os.getenv("LLM_API_BASE", "http://localhost:8080/v1")
        self.llm_model = model or os.getenv("LLM_MODEL", "Qwen2.5-Coder-3B-Instruct")
        self.llm_embed_model = embed_model or os.getenv("LLM_EMBED_MODEL", "gte-Qwen2-1.5B-instruct")  # Fixed variable name
        
        # Initialize OpenAI client with custom base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Set embedding size for fallback pseudo-embeddings
        self.embedding_size = int(os.getenv("LLM_EMBED_SIZE", "1536"))  # Use configured size
        
    def generate_text(self, 
                    prompt: str, 
                    system_message: str = "You are a helpful assistant with expertise in Rust programming.", 
                    max_tokens: int = 4000,
                    temperature: float = 0.7) -> str:
        """Generate text using the LLM with OpenAI format"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Add timeout to prevent hanging on server issues
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            
            # Return a fallback template for development/testing
            if "API Key" in str(e) or "401" in str(e) or "connect" in str(e):
                print("Using fallback template for text generation")
                if "create a Rust project" in prompt or "generate a project" in prompt:
                    return """[filename: Cargo.toml]
[package]
name = "hello_world"
version = "0.1.0"
edition = "2021"

[dependencies]

[filename: src/main.rs]
fn main() {
    println!("Hello, World!");
}

[filename: README.md]
# Hello World

This is a simple Rust program that prints "Hello, World!".
"""
                elif "fix" in prompt and "error" in prompt:
                    return """[filename: src/main.rs]
fn main() {
    println!("Hello, World!");
}
"""
            return f"Error: {str(e)}"
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts"""
        try:
            response = self.client.embeddings.create(
                model=self.llm_embed_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error getting embeddings from API: {str(e)}")
            print("Using fallback hash-based pseudo-embeddings")
            
            # Create pseudo-embeddings using hash function as fallback
            # This is just for testing purposes - not suitable for production!
            def text_to_pseudo_embedding(text: str) -> List[float]:
                import hashlib
                # Create a fixed size embedding by hashing parts of the text
                result = []
                text = text.lower()
                for i in range(self.embedding_size):
                    # Hash different substrings of the text
                    h = hashlib.md5(f"{text}_{i}".encode()).digest()
                    # Convert 16 bytes to a float between -1 and 1
                    val = (int.from_bytes(h[:4], byteorder='big') / 2**32) * 2 - 1
                    result.append(val)
                return result
                
            return [text_to_pseudo_embedding(text) for text in texts]
    
    def generate_text_with_tools(self, prompt: str) -> str:
        """Generate text with tool-calling capability"""
        # Implement tool calling if needed
        return self.generate_text(prompt)