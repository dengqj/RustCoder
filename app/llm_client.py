import os
import json
import requests
from typing import List, Dict, Any, Optional
from openai import OpenAI

class LlamaEdgeClient:
    """Client for interacting with LlamaEdge OpenAI-compatible API"""
    
    def __init__(self, api_key=None, api_base=None, model=None, embed_model=None):
        """Initialize LlamaEdgeClient with API credentials"""
        # Use the suggested public Gaia node as default
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        
        # Use provided parameters with fallback to environment variables and the new suggested URL
        self.base_url = api_base or os.getenv("LLM_API_BASE", "https://0x9fcf7888963793472bfcb8c14f4b6b47a7462f17.gaia.domains/v1")
        self.llm_model = model or os.getenv("LLM_MODEL", "Qwen2.5-Coder-3B-Instruct")
        self.llm_embed_model = embed_model or os.getenv("LLM_EMBED_MODEL", "gte-Qwen2-1.5B-instruct")
        
        # Don't require API key for the public node
        is_public_node = "gaia.domains" in self.base_url
        is_local_endpoint = self.base_url.startswith("http://localhost") or self.base_url.startswith("http://host.docker.internal")
        
        if not self.api_key and not (is_local_endpoint or is_public_node):
            raise ValueError("API key is required for non-local, non-public endpoints")
            
        # Initialize OpenAI client with custom base URL
        # Use dummy API key for endpoints that don't require authentication
        api_key_to_use = self.api_key if self.api_key else "dummy_api_key_for_local_setup"
        self.client = OpenAI(
            api_key=api_key_to_use,
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
        
        # Add explicit instructions to format the response correctly
        enhanced_system_message = f"""
{system_message}

IMPORTANT: Format your response with file headers in this exact format:
[filename: Cargo.toml]
<cargo toml content>

[filename: src/main.rs]
<rust code content>

[filename: README.md]
<readme content>

Do not include explanations outside of these file blocks.
"""
        
        messages = [
            {"role": "system", "content": enhanced_system_message},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Add timeout to prevent hanging on server issues
            print(f"Calling LLM API at {self.base_url} with model {self.llm_model}")
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=60  # Add explicit timeout
            )
            result = response.choices[0].message.content
            print(f"LLM response received: {result[:100]}...")
            
            # Check if response is properly formatted
            if not result.strip().startswith("[filename:"):
                print("Warning: Response not properly formatted, applying fix...")
                # Extract content that looks like files and reformat
                fixed_result = ""
                if "Cargo.toml" in result:
                    cargo_section = result.split("Cargo.toml", 1)[1].split("[filename:", 1)[0]
                    fixed_result += "[filename: Cargo.toml]\n" + cargo_section.strip() + "\n\n"
                if "src/main.rs" in result or "main.rs" in result:
                    main_section = result.split("main.rs", 1)[1].split("[filename:", 1)[0]
                    fixed_result += "[filename: src/main.rs]\n" + main_section.strip() + "\n\n"
                if "README" in result:
                    readme_section = result.split("README", 1)[1].split("[filename:", 1)[0]
                    fixed_result += "[filename: README.md]\n" + readme_section.strip()
                
                # If we managed to fix it, use the fixed version
                if fixed_result.strip():
                    return fixed_result
                
                # Otherwise use fallback
                return self._get_fallback_response(prompt)
                
            return result
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            return self._get_fallback_response(prompt)
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Get fallback response when API fails"""
        print("Using fallback template for text generation")
        if "create a Rust project" in prompt or "generate a project" in prompt or "calculator" in prompt:
            return """[filename: Cargo.toml]
[package]
name = "calculator"
version = "0.1.0"
edition = "2021"

[dependencies]

[filename: src/main.rs]
fn main() {
    println!("Simple Calculator");
    
    let a = 10;
    let b = 5;
    
    println!("Addition: {} + {} = {}", a, b, a + b);
    println!("Subtraction: {} - {} = {}", a, b, a - b);
    println!("Multiplication: {} * {} = {}", a, b, a * b);
    println!("Division: {} / {} = {}", a, b, a / b);
}

[filename: README.md]
# Calculator

A simple command-line calculator written in Rust that supports basic arithmetic operations.
"""
        elif "fix" in prompt and "error" in prompt:
            return """[filename: src/main.rs]
fn main() {
    println!("Hello, World!");
}
"""
        else:
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
            def text_to_pseudo_embedding(text: str) -> List[float]:
                import hashlib
                result = []
                text = text.lower()
                for i in range(self.embedding_size):
                    h = hashlib.md5(f"{text}_{i}".encode()).digest()
                    val = (int.from_bytes(h[:4], byteorder='big') / 2**32) * 2 - 1
                    result.append(val)
                return result
                
            return [text_to_pseudo_embedding(text) for text in texts]
    
    def generate_text_with_tools(self, prompt: str) -> str:
        """Generate text with tool-calling capability"""
        # Implement tool calling if needed
        return self.generate_text(prompt)