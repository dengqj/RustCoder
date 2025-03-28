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
        
        # Pattern to match both [filename: path] and filename: path formats
        file_matches = re.findall(r'\[filename: (.+?)\]|\*\*(.+?):\*\*|```(.+?)\s', response, re.DOTALL)
        content_blocks = re.split(r'\[filename: .+?\]|\*\*(.+?):\*\*|```(.+?)\s', response)
        
        # Clean up content blocks
        cleaned_blocks = []
        for block in content_blocks:
            if block and block.strip():
                # Find code block content
                code_match = re.search(r'```(?:\w+)?\s*(.*?)```', block, re.DOTALL)
                if code_match:
                    cleaned_blocks.append(code_match.group(1).strip())
                else:
                    cleaned_blocks.append(block.strip())
        
        # Match filenames with content
        for i, match in enumerate(file_matches):
            if i < len(cleaned_blocks):
                # Find first non-empty group in the match
                filename = next((name for name in match if name), "").strip()
                if filename and not filename.startswith("```"):
                    files[filename] = cleaned_blocks[i]
        
        # If nothing was parsed but there are code blocks, try simpler parsing
        if not files:
            code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', response, re.DOTALL)
            file_headers = re.findall(r'(?:^|\n)#+\s*(.+\.rs|Cargo\.toml|README\.md)', response)
            
            if len(code_blocks) == len(file_headers):
                for i, header in enumerate(file_headers):
                    files[header.strip()] = code_blocks[i].strip()
        
        return files
    
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