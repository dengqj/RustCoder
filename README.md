# Rust Coder

API and MCP services that generate fully functional Rust projects from natural language descriptions. These services leverage LLMs to create complete Rust cargo projects, compile Rust source code, and automatically fix compiler errors.

---

## ✨ Features

- **Generate Rust Projects** 📦 - Transform text descriptions into complete Rust projects.
- **Automatic Compilation & Fixing** 🛠 - Detect and resolve errors during compilation.
- **Vector Search** 🔍 - Search for similar projects and errors.
- **Docker Containerization** 🐳 - Easy deployment with Docker.
- **Asynchronous Processing** ⏳ - Handle long-running operations efficiently.
- **Multiple Service Interfaces** 🔄 - REST API and MCP (Model-Compiler-Processor) interface.

---

## 📋 Prerequisites

Ensure you have the following installed:

- **Docker & Docker Compose** 🐳

Or, if you want to run the services directly on your own computer:

- **Python 3.8+** 🐍
- **Rust Compiler and cargo tools** 🦀 
- **Rust Compiler and cargo tools** 🦀 

---

## 📦 Install

```bash
git clone https://github.com/WasmEdge/Rust_coder
cd Rust_coder
```

## 🚀 Configure and run

### Using Docker (Recommended)

Edit the `docker-compose.yml` file and specify your own LLM API server. The default config assumes that you have a [Gaia node like this](https://github.com/GaiaNet-AI/node-configs/tree/main/qwen-2.5-coder-3b-instruct-gte) running on `localhost` port `8080`. The alternative configuration shown below uses a [public Gaia node for coding assistance](https://docs.gaianet.ai/nodes#coding-assistant-agents).

```
- LLM_API_BASE=https://coder.gaia.domains/v1
- LLM_MODEL=Qwen2.5-Coder-32B-Instruct-Q5_K_M
- LLM_EMBED_MODEL=nomic-embed
- LLM_API_KEY=<YOUR API KEY FROM GAIANET.AI>
- LLM_EMBED_SIZE=768
```

Start the services.

```bash
docker-compose up -d
```

Stop the services.

```bash
docker-compose stop
```

### Manual Setup

By default, you will need a [Qdrant server](https://qdrant.tech/documentation/quickstart/) running on `localhost` port `6333`. You also need a [local Gaia node](https://github.com/GaiaNet-AI/node-configs/tree/main/qwen-2.5-coder-3b-instruct-gte). Set the following environment variables in your terminal to point to the Qdrant and Gaia instances, as well as your Rust compiler tools.

```
QDRANT_HOST=localhost
QDRANT_PORT=6333
LLM_API_BASE=http://localhost:8080/v1
LLM_MODEL=Qwen2.5-Coder-3B-Instruct
LLM_EMBED_MODEL=nomic-embed
LLM_API_KEY=your_api_key
LLM_EMBED_SIZE=768
CARGO_PATH=/path/to/cargo
RUST_COMPILER_PATH=/path/to/rustc
```

Start the services.

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔥 Usage

The API provides the following endpoints:

### 🎯 Generate a Project

**Endpoint:** `POST /generate-sync`

**Example:**

```bash
  curl -X POST http://localhost:8000/generate-sync \
  -H "Content-Type: application/json" \
  -d '{"description": "A command-line calculator in Rust", "requirements": "Should support addition, subtraction, multiplication, and division"}'
```

#### 📥 Request Body:

```
{
  "description": "A command-line calculator in Rust",
  "requirements": "Should support addition, subtraction, multiplication, and division"
}
```

#### 📤 Response:

```
[filename: Cargo.toml]
[package]
name = "calculator"
version = "0.1.0"
edition = "2021"

[dependencies]
... ...

[filename: src/main.rs]
fn main() {
    // Calculator implementation
}
... ...
```

### 🛠 Compile a Project

**Endpoint:** `POST /compile`

**Example:**

```bash
curl -X POST http://localhost:8000/compile \
-H "Content-Type: application/json" \
-d '{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}"
}'
```

#### 📥 Request Body:

```
{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}"
}
```

#### 📤 Response:

```
{
  "success": true,
  "files": [
    "Cargo.toml",
    "src/main.rs"
  ],
  "build_output": "Build successful",
  "run_output": "Hello, World!\n"
}
```

### 🩹 Compile and fix errors 

**Endpoint:** `POST /compile-and-fix`

**Example:**

```bash
curl -X POST http://localhost:8000/compile-and-fix \
-H "Content-Type: application/json" \
-d '{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\" // Missing closing parenthesis\n}",
  "description": "A simple hello world program",
  "max_attempts": 3
}'
```

#### 📥 Request Body:

```
{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\" // Missing closing parenthesis\n}",
  "description": "A simple hello world program",
  "max_attempts": 3
}
```
     
#### 📤 Response:

```
{
  "success": true,
  "attempts": [
    {
      "attempt": 1,
      "success": false,
      "output": "   Compiling hello_world v0.1.0 (/tmp/tmpk_0n65md)\nerror: mismatched closing delimiter: `}`\n --> src/main.rs:2:13\n  |\n1 | fn main() {\n  |           - closing delimiter possibly meant for this\n2 |     println!(\"Hello, World!\" // Missing closing parenthesis\n  |             ^ unclosed delimiter\n3 | }\n  | ^ mismatched closing delimiter\n\nerror: could not compile `hello_world` (bin \"hello_world\") due to 1 previous error\n"
    },
    {
      "attempt": 2,
      "success": true,
      "output": null
    }
  ],
  "final_files": {
    "Cargo.toml": "[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]",
    "src/main.rs": "fn main() {\n    println!(\"Hello, World!\");\n}"
  },
  "build_output": "Build successful",
  "run_output": "Hello, World!\n",
  "similar_project_used": false,
  "combined_text": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}"
}
```

### 🎯 Generate a Project Async

**Endpoint:** `POST /generate`

**Example:**

```bash
  curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"description": "A command-line calculator in Rust", "requirements": "Should support addition, subtraction, multiplication, and division"}'
```

#### 📥 Request Body:

```json
{
  "description": "A command-line calculator in Rust",
  "requirements": "Should support addition, subtraction, multiplication, and division"
}
```

#### 📤 Response:

```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Project generation started"
}
```

### 📌 Check Project Status

**Endpoint:** `GET /project/{project_id}`

**Example:**

```bash
curl http://localhost:8000/project/123e4567-e89b-12d3-a456-426614174000
```

#### 📤 Response:

```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "message": "Project generated successfully",
  "files": ["Cargo.toml", "src/main.rs", "README.md"],
  "build_output": "...",
  "run_output": "..."
}
```

### 📌 Get Generated Files

**Endpoint:** `GET /project/{project_id}/files/path_to_file`

**Example:**

```bash
curl http://localhost:8000/project/123e4567-e89b-12d3-a456-426614174000/files/src/main.rs
```

#### 📤 Response:

```
fn main() {
    ... ...
}
```

---

## 🔧 MCP (Model-Compiler-Processor) tools

The MCP server is available via the HTTP SSE transport via the `http://localhost:3000/sse` URL. The MCP server can be accessed using the [cmcp command-line client](https://github.com/RussellLuo/cmcp). To install the `cmcp` tool,

```bash
pip install cmcp
```

### 🎯 Generate a new project

**tool:** `generate`

#### 📥 Request example:

```bash
cmcp http://localhost:3000 tools/call name=generate arguments:='{"description": "A command-line calculator in Rust", "requirements": "Should support addition, subtraction, multiplication, and division"}'
```

#### 📤 Response:

```json
{
  "meta": null,
  "content": [
    {
      "type": "text",
      "text": "[filename: Cargo.toml] ... [filename: src/main.rs] ... ",
      "annotations": null
    }
  ],
  "isError": false
}
```
### 🩹 Compile and Fix Rust Code

**tool:** `compile_and_fix`

#### 📥 Request example:

```bash
cmcp http://localhost:3000 tools/call name=compile_and_fix arguments:='{"code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\" // Missing closing parenthesis \n}" }'
```

#### 📤 Response:

```json
{
  "meta": null,
  "content": [
    {
      "type": "text",
      "text": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\"); \n}",
      "annotations": null
    }
  ],
  "isError": false
}
```

---

## 📂 Project Structure

```
Rust_coder_lfx/
├── app/                  # Application code
│   ├── compiler.py       # Rust compilation handling
│   ├── llm_client.py     # LLM API client
│   ├── llm_tools.py      # Tools for LLM interactions
│   ├── load_data.py      # Data loading utilities
│   ├── main.py           # FastAPI application & endpoints
│   ├── mcp_server.py     # MCP server implementation
│   ├── mcp_service.py    # Model-Compiler-Processor service
│   ├── mcp_tools.py      # MCP-specific tools
│   ├── prompt_generator.py # LLM prompt generation
│   ├── response_parser.py # Parse LLM responses into files
│   ├── utils.py          # Utility functions
│   └── vector_store.py   # Vector database interface
├── data/                 # Data storage
│   ├── error_examples/   # Error examples for vector search
│   └── project_examples/ # Project examples for vector search
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── examples/             # Example scripts for using the API
│   ├── compile_endpoint.txt        # Example for compile endpoint
│   ├── compile_and_fix_endpoint.txt # Example for compile-and-fix endpoint
│   ├── mcp_client_example.py       # Example MCP client usage
│   └── run_mcp_server.py           # Example for running MCP server
├── templates/            # Prompt templates
│   └── project_prompts.txt # Templates for project generation
├── mcp-proxy-config.json # MCP proxy configuration
├── parse_and_save_qna.py # Q&A parsing utility
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

---


## 🧠 How It Works

Vector Search: The system uses Qdrant for storing and searching project examples and error solutions.

LLM Integration: Communicates with LlamaEdge API for code generation and error fixing via `llm_client.py`.

Compilation Feedback Loop: Automatically compiles, detects errors, and fixes them using `compiler.py`.

File Parsing: Converts LLM responses into project files with `response_parser.py`.

#### Architecture

REST API Interface (app/main.py): FastAPI application exposing HTTP endpoints for project generation, compilation, and error fixing.

MCP Interface (mcp_server.py, app/mcp_service.py): Server-Sent Events interface for the same functionality.

Vector Database (app/vector_store.py): Qdrant is used for storing and searching similar projects and error examples.

LLM Integration (app/llm_client.py): Communicates with LLM APIs (like Gaia nodes) for code generation and error fixing.

Compilation Pipeline (app/compiler.py): Handles Rust code compilation, error detection, and provides feedback for fixing.

#### Process Flow

Project Generation:

User provides a description and requirements
System creates a prompt using templates (templates/project_prompts.txt)
LLM generates a complete Rust project
Response is parsed into individual files (app/response_parser.py)
Project is compiled to verify correctness

Error Fixing:

System attempts to compile the provided code
If errors occur, they're extracted and analyzed
Vector search may find similar past errors
LLM receives the errors and original code to generate fixes
Process repeats until successful or max attempts reached

---

## 🤝 Contributing
Contributions are welcome! Feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add some amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

---

## 📜 License
Licensed under [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).
