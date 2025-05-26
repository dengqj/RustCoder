import os
import uuid
import shutil
import json  # Move from within functions to top level
from typing import Dict, List, Optional
from dotenv import load_dotenv
import tempfile  # Import tempfile for temporary directory handling

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse  # Move from within function to top level
from pydantic import BaseModel

from app.prompt_generator import PromptGenerator
from app.response_parser import ResponseParser
from app.compiler import RustCompiler
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore
from app.mcp_service import RustCompilerMCP

app = FastAPI(title="Rust Project Generator API")

# Get API key from environment variable
api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise ValueError("LLM_API_KEY environment variable not set")

# Get embedding size from environment variable
llm_embed_size = int(os.getenv("LLM_EMBED_SIZE", "1536"))  # Default to 1536 for compatibility

# Initialize components
llm_client = LlamaEdgeClient(api_key=api_key)
prompt_gen = PromptGenerator()
parser = ResponseParser()
compiler = RustCompiler()

# Initialize vector store
vector_store = QdrantStore(embedding_size=llm_embed_size)
vector_store.create_collection("project_examples")
vector_store.create_collection("error_examples")

# After initializing vector store
from app.load_data import load_project_examples, load_error_examples

# Check if collections are empty and load data if needed
if vector_store.count("project_examples") == 0:
    load_project_examples()
if vector_store.count("error_examples") == 0:
    load_error_examples()

# Initialize MCP service with vector store and LLM client
rust_mcp = RustCompilerMCP(vector_store=vector_store, llm_client=llm_client)

# Project generation request
class ProjectRequest(BaseModel):
    description: str
    requirements: Optional[str] = None

# Project generation response
class ProjectResponse(BaseModel):
    project_id: str
    status: str
    message: str
    files: Optional[List[str]] = None
    build_output: Optional[str] = None
    run_output: Optional[str] = None

@app.post("/generate", response_model=ProjectResponse)
async def generate_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """Generate a Rust project based on description"""
    
    # Create unique project ID
    project_id = str(uuid.uuid4())
    project_dir = f"output/{project_id}"
    
    # Generate project in background
    background_tasks.add_task(
        handle_project_generation, 
        project_id, 
        project_dir, 
        request.description, 
        request.requirements
    )
    
    return ProjectResponse(
        project_id=project_id,
        status="processing",
        message="Project generation started"
    )

@app.get("/project/{project_id}", response_model=ProjectResponse)
async def get_project_status(project_id: str):
    """Get status of a project generation"""
    status_file = f"output/{project_id}/status.json"
    if not os.path.exists(status_file):
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Read status file
    with open(status_file, 'r') as f:
        status = json.load(f)
        
    return ProjectResponse(**status)

@app.post("/compile")  # Changed from /mcp/compile
async def compile_rust(request: dict):
    """MCP endpoint to compile Rust code"""
    if "code" not in request:
        raise HTTPException(status_code=400, detail="Missing 'code' field")
    
    return rust_mcp.compile_rust_code(request["code"])

@app.post("/compile-and-fix")  # Changed from /mcp/compile-and-fix
async def compile_and_fix_rust(request: dict):
    """Endpoint to compile and fix Rust code"""
    if "code" not in request or "description" not in request:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    max_attempts = request.get("max_attempts", 10)
    
    # Pre-process code to fix common syntax errors
    code = request["code"]
    # Fix missing parenthesis in println! macro
    if "println!(" in code and ");" not in code:
        code = code.replace("println!(\"", "println!(\"") 
        code = code.replace("\" //", "\"); //")
    
    result = rust_mcp.compile_and_fix_rust_code(
        code,
        request["description"],
        max_attempts=max_attempts
    )
    
    # Format as text with filename markers
    output_text = ""
    for filename, content in result["final_files"].items():
        output_text += f"[filename: {filename}]\n{content}\n\n"
    
    # For successful fixes, return a text response with the combined code
    if result["success"]:
        return PlainTextResponse(content=output_text.strip())
    else:
        # For errors, return the JSON with detailed error information
        return JSONResponse(content={
            "status": "error",
            "message": f"Failed to fix code: {result.get('build_output', '')}",
            "attempts": result.get("attempts", []),
            "combined_text": output_text.strip()
        })

async def handle_project_generation(
    project_id: str, 
    project_dir: str, 
    description: str, 
    requirements: Optional[str]
):
    """Handle the project generation process"""
    # Create project directory structure
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
    
    status = {
        "project_id": project_id,
        "status": "generating",
        "message": "Generating project code"
    }
    save_status(project_dir, status)
    
    try:
        # Skip vector search if environment variable is set
        skip_vector_search = os.getenv("SKIP_VECTOR_SEARCH", "").lower() == "true"
        
        example_text = ""
        if not skip_vector_search:
            try:
                # Step 1: Check if similar project exists in vector DB
                query_embedding = llm_client.get_embeddings([description])[0]
                similar_projects = vector_store.search("project_examples", query_embedding, limit=1)
                
                # If we found a similar project, use it as reference
                if similar_projects:
                    example_text = f"\nHere's a similar project you can use as reference:\n{similar_projects[0]['example']}"
            except Exception as e:
                print(f"Vector search error (non-critical): {e}")
                # Continue without vector search results
        
        if example_text and requirements:
            requirements += example_text
        elif example_text:
            requirements = example_text
        
        # Step 2: Generate prompt and get response from LLM
        prompt = prompt_gen.generate_prompt(description, requirements)
        
        # Use regular generate_text method instead of generate_text_with_tools
        system_message = """You are an expert Rust developer. Create a complete, working Rust project.
        Always include at minimum these files: Cargo.toml, src/main.rs, and README.md.
        For Cargo.toml, include proper dependencies and metadata.
        Format your response with clear file headers like:
        
        [filename: Cargo.toml]
        <file content>
        
        [filename: src/main.rs]
        <file content>
        """
        
        response = llm_client.generate_text(prompt, system_message=system_message)
        
        # Step 3: Parse response into files
        files = parser.parse_response(response)
        
        # Ensure essential files exist
        if "Cargo.toml" not in files:
            # Create a basic Cargo.toml if it's missing
            project_name = description.lower().replace(" ", "_").replace("-", "_")[:20]
            files["Cargo.toml"] = f"""[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
        
        if "src/main.rs" not in files and "src\\main.rs" not in files:
            # Create a basic main.rs if it's missing
            files["src/main.rs"] = """fn main() {
    println!("Hello, world!");
}
"""
        
        file_paths = parser.write_files(files, project_dir)
        
        status.update({
            "status": "compiling",
            "message": "Compiling project",
            "files": file_paths
        })
        save_status(project_dir, status)
        
        # Step 4: Compile the project
        success, output = compiler.build_project(project_dir)
        
        if not success:
            # Project failed to compile, try to fix errors
            status.update({
                "status": "error",
                "message": "Compilation failed, attempting to fix",
                "build_output": output
            })
            save_status(project_dir, status)
            
            # Extract error context
            error_context = compiler.extract_error_context(output)
            
            # Skip vector search if environment variable is set
            skip_vector_search = os.getenv("SKIP_VECTOR_SEARCH", "").lower() == "true"
            similar_errors = []
            
            if not skip_vector_search:
                try:
                    # Find similar errors in vector DB
                    error_embedding = llm_client.get_embeddings([error_context["full_error"]])[0]
                    similar_errors = vector_store.search("error_examples", error_embedding, limit=3)
                except Exception as e:
                    print(f"Vector search error (non-critical): {e}")
                    # Continue without vector search results
        
            # Generate fix prompt
            fix_examples = ""
            if similar_errors:
                fix_examples = "Here are some examples of similar errors and their fixes:\n\n"
                for i, err in enumerate(similar_errors):
                    fix_examples += f"Example {i+1}:\n{err['error']}\nFix: {err['solution']}\n\n"
            
            fix_prompt = f"""
Here is a Rust project that failed to compile. Help me fix the compilation errors.

Project description: {description}

Compilation error:
{error_context["full_error"]}

{fix_examples}

Please provide the fixed code for all affected files.
"""
            
            # Get fix from LLM
            fix_response = llm_client.generate_text(fix_prompt)
            
            # Parse and apply fixes
            fixed_files = parser.parse_response(fix_response)
            for filename, content in fixed_files.items():
                file_path = os.path.join(project_dir, filename)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Try compiling again
            success, output = compiler.build_project(project_dir)
        
        if success:
            # Project compiled successfully, try running it
            run_success, run_output = compiler.run_project(project_dir)
            
            status.update({
                "status": "completed",
                "message": "Project generated successfully",
                "build_output": output,
                "run_output": run_output if run_success else "Failed to run project"
            })
        else:
            status.update({
                "status": "failed",
                "message": "Failed to generate working project",
                "build_output": output
            })
        
        save_status(project_dir, status)
    except Exception as e:
        # Update status to reflect the error
        status.update({
            "status": "failed",
            "message": f"Project generation failed: {str(e)}",
        })
        save_status(project_dir, status)

def save_status(project_dir: str, status: Dict):
    """Save project status to file"""
    with open(f"{project_dir}/status.json", 'w') as f:
        json.dump(status, f)

@app.get("/project/{project_id}/files/{file_path:path}")
async def get_project_file(project_id: str, file_path: str):
    """Get the contents of a specific file from a generated project"""
    full_path = os.path.join("output", project_id, file_path)
    
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return PlainTextResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.get("/project/{project_id}/download")
async def download_project(project_id: str):
    """Create a zip archive of the project and return it for download"""
    from fastapi.responses import FileResponse
    import zipfile
    
    project_dir = f"output/{project_id}"
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create a zip file
    zip_path = f"{project_dir}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(project_dir))
                zipf.write(file_path, arcname)
    
    return FileResponse(
        path=zip_path,
        filename=f"project-{project_id}.zip",
        media_type="application/zip"
    )

@app.post("/generate-sync")
async def generate_project_sync(request: ProjectRequest):
    """
    Generate a Rust project synchronously and return all files in text format.
    This endpoint will wait for the full generation process to complete.
    """
    try:
        # Create temporary directory for generation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up status tracking
            status = {
                "status": "generating",
                "message": "Generating project code"
            }
            
            # Skip vector search if environment variable is set
            skip_vector_search = os.getenv("SKIP_VECTOR_SEARCH", "").lower() == "true"
            
            example_text = ""
            if not skip_vector_search:
                try:
                    # Check for similar projects in vector DB
                    query_embedding = llm_client.get_embeddings([request.description])[0]
                    similar_projects = vector_store.search("project_examples", query_embedding, limit=1)
                    
                    if similar_projects:
                        example_text = f"\nHere's a similar project you can use as reference:\n{similar_projects[0]['example']}"
                except Exception as e:
                    print(f"Vector search error (non-critical): {e}")
            
            requirements = request.requirements or ""
            if example_text:
                requirements = f"{requirements}\n{example_text}" if requirements else example_text
            
            # Generate prompt and get response from LLM
            prompt = prompt_gen.generate_prompt(request.description, requirements)
            
            system_message = """You are an expert Rust developer. Create a complete, working Rust project.
            Always include at minimum these files: Cargo.toml, src/main.rs, and README.md.
            For Cargo.toml, include proper dependencies and metadata.
            Format your response with clear file headers like:
            
            [filename: Cargo.toml]
            <file content>
            
            [filename: src/main.rs]
            <file content>
            """
            
            response = llm_client.generate_text(prompt, system_message=system_message)
            
            # Parse response into files
            files = parser.parse_response(response)
            
            # Ensure essential files exist
            if "Cargo.toml" not in files:
                # Create a basic Cargo.toml if it's missing
                project_name = request.description.lower().replace(" ", "_").replace("-", "_")[:20]
                files["Cargo.toml"] = f"""[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
            
            if "src/main.rs" not in files and "src\\main.rs" not in files:
                # Create a basic main.rs if it's missing
                files["src/main.rs"] = """fn main() {
    println!("Hello, world!");
}
"""
            
            file_paths = parser.write_files(files, temp_dir)
            
            status.update({
                "status": "compiling",
                "message": "Compiling project",
                "files": file_paths
            })
            save_status(temp_dir, status)
            
            # Compile the project
            success, output = compiler.build_project(temp_dir)
            
            if not success:
                # Project failed to compile, try to fix errors
                status.update({
                    "status": "error",
                    "message": "Compilation failed, attempting to fix",
                    "build_output": output
                })
                save_status(temp_dir, status)
                
                # Extract error context
                error_context = compiler.extract_error_context(output)
                
                # Skip vector search if environment variable is set
                skip_vector_search = os.getenv("SKIP_VECTOR_SEARCH", "").lower() == "true"
                similar_errors = []
                
                if not skip_vector_search:
                    try:
                        # Find similar errors in vector DB
                        error_embedding = llm_client.get_embeddings([error_context["full_error"]])[0]
                        similar_errors = vector_store.search("error_examples", error_embedding, limit=3)
                    except Exception as e:
                        print(f"Vector search error (non-critical): {e}")
                        # Continue without vector search results
            
                # Generate fix prompt
                fix_examples = ""
                if similar_errors:
                    fix_examples = "Here are some examples of similar errors and their fixes:\n\n"
                    for i, err in enumerate(similar_errors):
                        fix_examples += f"Example {i+1}:\n{err['error']}\nFix: {err['solution']}\n\n"
                
                fix_prompt = f"""
Here is a Rust project that failed to compile. Help me fix the compilation errors.

Project description: {request.description}

Compilation error:
{error_context["full_error"]}

{fix_examples}

Please provide the fixed code for all affected files.
"""
            
                # Get fix from LLM
                fix_response = llm_client.generate_text(fix_prompt)
                
                # Parse and apply fixes
                fixed_files = parser.parse_response(fix_response)
                for filename, content in fixed_files.items():
                    file_path = os.path.join(temp_dir, filename)
                    with open(file_path, 'w') as f:
                        f.write(content)
                
                # Try compiling again
                success, output = compiler.build_project(temp_dir)
            
            if success:
                # Project compiled successfully, try running it
                run_success, run_output = compiler.run_project(temp_dir)
                
                status.update({
                    "status": "completed",
                    "message": "Project generated successfully",
                    "build_output": output,
                    "run_output": run_output if run_success else "Failed to run project"
                })
                
                # Return all files as text with build success marker
                all_files_content = "\n".join([f"[filename: {f}]\n{open(os.path.join(temp_dir, f)).read()}\n" for f in file_paths])
                all_files_content += "\n# Build succeeded\n"
                return PlainTextResponse(content=all_files_content)
            else:
                status.update({
                    "status": "failed",
                    "message": "Failed to generate working project",
                    "build_output": output
                })
            
            save_status(temp_dir, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating project: {str(e)}")