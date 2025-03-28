import os
import subprocess
from typing import Tuple, Optional, Dict

class RustCompiler:
    """Handles compilation of Rust Cargo projects"""
    
    def __init__(self):
        # Use environment variables with defaults
        self.cargo_path = os.getenv("CARGO_PATH", "cargo")
        self.rustc_path = os.getenv("RUST_COMPILER_PATH", "rustc")
        
    def build_project(self, project_path: str) -> Tuple[bool, Optional[str]]:
        """Build a Rust project with cargo"""
        try:
            # Run cargo build
            result = subprocess.run(
                [self.cargo_path, "build"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if build was successful
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
            
    def extract_error_context(self, error_output: str) -> Dict[str, str]:
        """Extract relevant context from compilation error"""
        # This is a simple implementation
        # Could be enhanced to better parse Rust error messages
        lines = error_output.split('\n')
        
        error_context = {
            "full_error": error_output,
            "error_message": "",
            "error_location": ""
        }
        
        for i, line in enumerate(lines):
            if "error[" in line:
                error_context["error_message"] = line
                # Try to get location from next line
                if i + 1 < len(lines) and "-->" in lines[i + 1]:
                    error_context["error_location"] = lines[i + 1]
                break
                
        return error_context
    
    def run_project(self, project_path: str) -> Tuple[bool, str]:
        """Run a Rust project with cargo run"""
        try:
            result = subprocess.run(
                [self.cargo_path, "run"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)