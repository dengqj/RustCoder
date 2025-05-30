"""
This file contains the core business logic for the Rust Compiler MCP service.
Note that the API integration and HTTP endpoints are now handled by app/mcp_tools.py.
"""

import os
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple

from app.compiler import RustCompiler
from app.response_parser import ResponseParser
from app.vector_store import QdrantStore
from app.llm_client import LlamaEdgeClient

class RustCompilerMCP:
    def __init__(self, vector_store=None, llm_client=None):
        """
        Initialize the Rust Compiler MCP service
        
        Args:
            vector_store: Vector store for searching similar examples
            llm_client: LLM client for generating fixes
        """
        self.compiler = RustCompiler()
        self.parser = ResponseParser()
        
        # Use provided vector store or create a new one
        self.vector_store = vector_store
        if self.vector_store is None:
            self.vector_store = QdrantStore()
            self.vector_store.create_collection("project_examples")
            self.vector_store.create_collection("error_examples")
            
        # Use provided LLM client or create a new one
        self.llm_client = llm_client
        if self.llm_client is None:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("LLM_API_KEY")
            if api_key:
                self.llm_client = LlamaEdgeClient(api_key=api_key)
            else:
                raise ValueError("LLM_API_KEY environment variable not set")
        
    def compile_rust_code(self, code_content: str) -> Dict:
        """
        MCP function to compile Rust code
        
        Args:
            code_content: String containing Rust code with file markers
            
        Returns:
            Dict with compilation status, output, and error messages
        """
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Parse the multi-file content
            files = self.parser.parse_response(code_content)
            
            # Ensure project structure
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            
            # Write files
            file_paths = self.parser.write_files(files, temp_dir)
            
            # Compile the project
            success, output = self.compiler.build_project(temp_dir)
            
            if success:
                # Try running if compilation succeeded
                run_success, run_output = self.compiler.run_project(temp_dir)
                
                # Store successful project in vector store for future reference
                self._store_successful_project(files, code_content)
                
                return {
                    "success": True,
                    "files": file_paths,
                    "build_output": output or "Build successful",
                    "run_output": run_output if run_success else "Failed to run project"
                }
            else:
                # Return error details
                error_context = self.compiler.extract_error_context(output)
                return {
                    "success": False,
                    "files": file_paths,
                    "build_output": output,
                    "error_details": error_context
                }
                
    def compile_and_fix_rust_code(self, 
                                  code_content: str, 
                                  description: str,
                                  max_attempts: int = 3) -> Dict:
        """
        MCP function to compile Rust code and fix errors using LLM
        
        Args:
            code_content: String containing Rust code with file markers
            description: Project description for context
            max_attempts: Maximum number of fix attempts
            
        Returns:
            Dict with compilation status, output, fixes applied, and final code
        """
        # Create temp directory for this compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Parse the multi-file content
            files = self.parser.parse_response(code_content)
            
            # Ensure project structure
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            
            # Write files
            file_paths = self.parser.write_files(files, temp_dir)
            
            # Check if we have similar projects in our dataset for reference
            project_reference = self._find_similar_project(description)
            
            attempts = []
            current_files = files.copy()
            
            # Try compiling and fixing up to max_attempts
            for attempt in range(max_attempts):
                # Compile the project
                success, output = self.compiler.build_project(temp_dir)
                
                # Store this attempt
                attempts.append({
                    "attempt": attempt + 1,
                    "success": success,
                    "output": output
                })
                
                if success:
                    # Try running if compilation succeeded
                    run_success, run_output = self.compiler.run_project(temp_dir)
                    
                    # Store this successful fix in our vector database
                    if attempt > 0:  # Only store if we actually fixed something
                        self._store_successful_fix(code_content, current_files, output)
                    
                    return {
                        "success": True,
                        "attempts": attempts,
                        "final_files": current_files,
                        "build_output": output or "Build successful",
                        "run_output": run_output if run_success else "Failed to run project",
                        "similar_project_used": project_reference is not None
                    }
                
                # If we've reached max attempts without success, stop
                if attempt == max_attempts - 1:
                    break
                    
                # Extract error context for LLM
                error_context = self.compiler.extract_error_context(output)
                
                # Find similar errors in vector DB
                similar_errors = self._find_similar_errors(error_context["full_error"])
                
                # Generate fix prompt
                fix_prompt = self._generate_fix_prompt(
                    description, 
                    error_context,
                    similar_errors,
                    project_reference
                )
                
                # Get fix from LLM
                fix_response = self.llm_client.generate_text(fix_prompt)
                
                # Parse and apply fixes
                fixed_files = self.parser.parse_response(fix_response)
                for filename, content in fixed_files.items():
                    file_path = os.path.join(temp_dir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)
                    current_files[filename] = content
            
            # If we've exhausted all attempts
            return {
                "success": False,
                "attempts": attempts,
                "final_files": current_files,
                "build_output": attempts[-1]["output"],
                "error_details": self.compiler.extract_error_context(attempts[-1]["output"]),
                "similar_project_used": project_reference is not None,
                "similar_errors_found": len(similar_errors) if 'similar_errors' in locals() else 0
            }
    
    def _find_similar_project(self, description: str) -> Optional[Dict]:
        """Find similar project from vector store"""
        if not self.vector_store:
            return None
            
        try:
            embeddings = self.llm_client.get_embeddings([description])[0]
            similar_projects = self.vector_store.search("project_examples", embeddings, limit=1)
            
            if similar_projects:
                return similar_projects[0]
        except Exception as e:
            print(f"Error finding similar project: {e}")
        
        return None
        
    def _find_similar_errors(self, error_text: str) -> List[Dict]:
        """Find similar error examples from vector store"""
        if not self.vector_store:
            return []
            
        try:
            embeddings = self.llm_client.get_embeddings([error_text])[0]
            similar_errors = self.vector_store.search("error_examples", embeddings, limit=3)
            return similar_errors
        except Exception as e:
            print(f"Error finding similar errors: {e}")
            return []
    
    def _generate_fix_prompt(self, 
                            description: str, 
                            error_context: Dict, 
                            similar_errors: List[Dict],
                            project_reference: Optional[Dict]) -> str:
        """Generate prompt for fixing compilation errors"""
        fix_examples = ""
        if similar_errors:
            fix_examples = "Here are some examples of similar errors and their fixes:\n\n"
            for i, err in enumerate(similar_errors):
                fix_examples += f"Example {i+1}:\n{err['error']}\nFix: {err['solution']}\n\n"
        
        reference_text = ""
        if project_reference:
            reference_text = f"\nHere's a similar project for reference:\n{project_reference['example']}\n"
        
        return f"""
Here is a Rust project that failed to compile. Help me fix the compilation errors.

Project description: {description}
{reference_text}

Compilation error:
{error_context["full_error"]}

{fix_examples}

Please provide the fixed code for all affected files.
"""
    
    def _store_successful_project(self, files: Dict[str, str], code_content: str):
        """Store successful project compilation in vector store"""
        if not self.vector_store:
            return
            
        try:
            # Create a project description
            if "README.md" in files:
                description = files["README.md"][:500]  # Use first 500 chars of README
            else:
                # Default to cargo.toml content
                description = files.get("Cargo.toml", "Rust project")
            
            # Try to get embedding or use dummy embedding if failed
            try:
                embeddings = self.llm_client.get_embeddings([description])[0]
            except Exception as e:
                print(f"Error getting embeddings: {e}")
                # Use a dummy embedding of correct size
                embeddings = [0.0] * self.vector_store.embedding_size  # Use configurable size
            
            # Store in vector store
            self.vector_store.add_item(
                collection_name="project_examples",
                vector=embeddings,
                item={
                    "example": code_content[:10000],  # Limit size
                    "description": description
                }
            )
        except Exception as e:
            print(f"Failed to store project in vector DB: {e}")
    
    def _store_successful_fix(self, original_code: str, fixed_files: Dict[str, str], error_output: str):
        """Store successful error fix in vector store"""
        if not self.vector_store:
            return
            
        try:
            # Create a combined fixed code representation
            fixed_code = "\n\n".join([
                f"[filename: {filename}]\n{content}"
                for filename, content in fixed_files.items()
            ])
            
            # Get embedding of the error
            error_context = self.compiler.extract_error_context(error_output)
            embeddings = self.llm_client.get_embeddings([error_context["full_error"]])[0]
            
            # Store in vector store
            self.vector_store.add_item(
                collection_name="error_examples",
                vector=embeddings,
                item={
                    "error": error_context["full_error"],
                    "solution": fixed_code[:5000],  # Limit size
                    "original_code": original_code[:5000]  # Limit size
                }
            )
        except Exception as e:
            print(f"Failed to store error fix in vector DB: {e}")
    
    def _fix_errors_with_llm(self, error_output, current_files, description, project_reference=None):
        """Use LLM to fix compilation errors"""
        if not self.llm_client:
            print("Warning: No LLM client available, returning original files")
            return current_files
        
        try:
            # Create prompt for error fixing
            prompt = self.prompt_generator.generate_error_fix_prompt(
                error_output=error_output,
                current_files=current_files,
                description=description,
                project_reference=project_reference
            )
            
            # Get LLM response
            response = self.llm_client.generate_text(
                prompt=prompt,
                system_message="You are an expert Rust developer fixing compilation errors.",
                max_tokens=4000,
                temperature=0.2  # Lower temperature for more precise fixes
            )
            
            # Parse response into fixed files
            fixed_files = self.parser.parse_response(response)
            
            # Return the fixed files
            return fixed_files
        except Exception as e:
            print(f"Error fixing with LLM: {str(e)}")
            # Return original files if LLM fails
            return current_files