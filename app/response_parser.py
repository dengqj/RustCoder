import os
import re
from typing import Dict, List, Tuple

class ResponseParser:
    """Parses LLM responses into separate files"""
    
    def __init__(self):
        self.file_pattern = r"\[filename:\s*(.*?)\](.*?)(?=\[filename:|$)"
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse response into a dictionary of files"""
        files = {}
        
        # First, try to extract using explicit filename markers
        file_blocks = re.findall(r'\[filename:\s*(.*?)\](.*?)(?=\[filename:|$)', response, re.DOTALL)
        if file_blocks:
            for filename, content in file_blocks:
                # Clean the filename and content
                clean_filename = filename.strip()
                # Remove leading/trailing backticks and language identifiers from content
                clean_content = self._clean_code_block(content)
                
                if clean_filename and clean_content:
                    files[clean_filename] = clean_content
        
        # If no files found with explicit markers, try to identify standard Rust project files
        if not files:
            # Look for code blocks and try to identify their file type by content
            code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', response, re.DOTALL)
            
            cargo_toml = None
            main_rs = None
            readme_md = None
            
            for block in code_blocks:
                clean_block = block.strip()
                if "[package]" in clean_block and "name =" in clean_block and "version =" in clean_block:
                    cargo_toml = clean_block
                elif "fn main()" in clean_block:
                    main_rs = clean_block
                elif clean_block.startswith("# ") or "# " in clean_block[:20]:
                    readme_md = clean_block
            
            if cargo_toml:
                files["Cargo.toml"] = cargo_toml
            if main_rs:
                files["src/main.rs"] = main_rs
            if readme_md:
                files["README.md"] = readme_md
        
        # If still no files found, use a more aggressive approach to extract content
        if not files:
            # Last resort: extract based on common patterns in the response
            if "Cargo.toml" in response:
                cargo_section = self._extract_section(response, "Cargo.toml")
                if cargo_section:
                    files["Cargo.toml"] = cargo_section
            
            if "main.rs" in response:
                main_section = self._extract_section(response, "main.rs")
                if main_section:
                    files["src/main.rs"] = main_section
            
            if "README" in response:
                readme_section = self._extract_section(response, "README")
                if readme_section:
                    files["README.md"] = readme_section
        
        # Ensure we don't have language identifiers as filenames
        common_lang_identifiers = ["toml", "rust", "markdown", "bash"]
        for lang in common_lang_identifiers:
            if lang in files and len(files[lang]) < 100:  # Only remove if it's short (likely a lang identifier)
                del files[lang]
        
        # Ensure we have the essential files with proper content
        if not files.get("Cargo.toml") or not files.get("src/main.rs"):
            # Create fallback files if missing
            if not files.get("Cargo.toml"):
                files["Cargo.toml"] = """[package]
name = "rust_project"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
            
            if not files.get("src/main.rs"):
                files["src/main.rs"] = """fn main() {
    println!("Hello, world!");
}
"""
        
        return files
    
    def _clean_code_block(self, text: str) -> str:
        """Clean code blocks by removing backticks and language identifiers"""
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove triple backticks and language identifier at start
        text = re.sub(r'^```\w*\s*', '', text)
        
        # Remove trailing triple backticks
        text = re.sub(r'\s*```$', '', text)
        
        return text
    
    def _extract_section(self, response: str, identifier: str) -> str:
        """Extract a section from the response based on an identifier"""
        parts = response.split(identifier)
        if len(parts) < 2:
            return ""
        
        # Get the part after the identifier
        section = parts[1]
        
        # Find the next code block or section
        next_section = re.search(r'(\[filename:|```\w*)', section)
        if next_section:
            section = section[:next_section.start()]
        
        # Clean up the section
        section = re.sub(r'^[^\w]*', '', section, flags=re.DOTALL)  # Remove non-word chars at start
        section = section.strip()
        
        return section
    
    def write_files(self, files: Dict[str, str], project_dir: str) -> List[str]:
        """Write files to the project directory"""
        file_paths = []
        
        for filename, content in files.items():
            # Normalize path to use OS-specific separators
            normalized_path = os.path.normpath(os.path.join(project_dir, filename))
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(normalized_path), exist_ok=True)
            
            with open(normalized_path, 'w') as f:
                f.write(content)
            
            file_paths.append(filename)
        
        return file_paths