import os
import re
from typing import Dict, List, Tuple

class ResponseParser:
    """Parses LLM responses into separate files"""
    
    def __init__(self):
        self.file_pattern = r"\[filename:\s*(.*?)\](.*?)(?=\[filename:|$)"
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse the LLM response into separate files"""
        # Find all file patterns in the response
        matches = re.findall(self.file_pattern, response, re.DOTALL)
        
        files = {}
        for filename, content in matches:
            # Clean up filename and content
            filename = filename.strip()
            content = content.strip()
            files[filename] = content
            
        return files
    
    def write_files(self, files: Dict[str, str], output_dir: str) -> List[str]:
        """Write parsed files to disk"""
        written_files = []
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        for filename, content in files.items():
            # Create subdirectories if needed
            file_path = os.path.join(output_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the file
            with open(file_path, 'w') as f:
                f.write(content)
                
            written_files.append(file_path)
            
        return written_files