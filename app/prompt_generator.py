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
            
    def generate_prompt(self, project_description: str, additional_requirements: Optional[str] = "") -> str:
        """Generate a prompt for the LLM"""
        return self.template.substitute(
            project_description=project_description,
            additional_requirements=additional_requirements or ""
        )