import os
from string import Template
from typing import Dict, Optional

class PromptGenerator:
    """Generates prompts for LLM to create Rust Cargo projects"""
    
    def __init__(self, template_path: str = "../templates/project_prompt.txt"):
        self.template_path = template_path
        self._load_template()
        
    def _load_template(self):
        """Load the prompt template from file"""
        try:
            with open(self.template_path, 'r') as f:
                self.template = Template(f.read())
        except FileNotFoundError:
            # Default template if file not found
            self.template = Template("""
<|im_start|>system
You are an expert Rust developer. You are tasked with creating a complete, 
working Cargo project based on the requirements. Provide well-structured code 
with comprehensive error handling. Your output should consist of complete file 
contents for all necessary files, clearly marked with filename headers like:

[filename: src/main.rs]
// file contents here

[filename: Cargo.toml]
// file contents here

Make sure the project follows Rust best practices, has appropriate dependencies,
and can be built successfully with 'cargo build'.
<|im_end|>
<|im_start|>user
Create a Rust Cargo project for: $project_description
$additional_requirements
<|im_end|>
<|im_start|>assistant
            """)
            
    def generate_prompt(self, description: str, requirements: Optional[str] = None) -> str:
        """Generate a prompt for the LLM that includes tool usage instructions"""
        
        tool_instructions = """
You have access to a vector database with Rust project examples and error solutions.
When you need a reference or example, use the query_examples function as follows:

To find project examples:

query_examples(query="chess game", collection="project_examples", limit=2)


To find error solutions:
query_examples(query="error message", collection="error_examples", limit=2)

First, analyze what kind of Rust project is needed. Then query relevant examples before writing code.
"""
        
        base_prompt = f"""
Create a Rust project based on this description:
{description}

{requirements or ""}

Generate all required files for a complete, compilable Rust project.
Use proper Rust best practices and error handling.
Format each file in code blocks with the filename as the header.
"""
        return tool_instructions + base_prompt