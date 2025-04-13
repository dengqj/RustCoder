import os
import json
from typing import Dict, List, Optional, Union
from openai import OpenAI

class LlamaEdgeClient:
    """Client for interacting with LlamaEdge OpenAI-compatible API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")
            
        # Use environment variables with defaults
        self.base_url = os.getenv("LLAMAEDGE_URL", "http://localhost:8080/v1")
        self.llm_model = os.getenv("LLAMAEDGE_MODEL", "Qwen2.5-Coder-3B-Instruct")
        
        # Initialize OpenAI client with custom base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
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
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",  # Default model, may need to adjust based on LlamaEdge capabilities
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            return [[] for _ in texts]  # Return empty embeddings on error
    
    def generate_text_with_tools(self, prompt: str) -> str:
        """Generate text with tool-calling capability"""
        # Implement tool calling if needed
        return self.generate_text(prompt)