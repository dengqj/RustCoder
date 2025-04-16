# Rust Project Generator API

An API service that generates fully functional Rust projects from natural language descriptions. This service leverages LLMs to create Rust code, compiles it, and automatically fixes any errors.

---

## ✨ Features

- **Generate Rust Projects** 📦 - Transform text descriptions into complete Rust projects.
- **Automatic Compilation & Fixing** 🛠 - Detect and resolve errors during compilation.
- **Vector Search** 🔍 - Search for similar projects and errors.
- **Docker Containerization** 🐳 - Easy deployment with Docker.
- **Asynchronous Processing** ⏳ - Handle long-running operations efficiently.

---

## 📋 Prerequisites

Ensure you have the following installed:

- **Python 3.8+** 🐍
- **Docker & Docker Compose** 🐳
- **Rust Compiler** 🦀 (for local testing)

---

## 🚀 Installation

### Using Docker (Recommended)

```bash
git clone <repository-url>
cd Rust_coder_lfx
docker-compose up -d
```

To stop it

```bash
docker-compose stop
```

### Manual Setup

```bash
git clone <repository-url>
cd Rust_coder_lfx
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔥 Usage

The API provides the following endpoints:

### 🎯 Generate a Project

**Endpoint:** `POST /generate`

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

#### Example:

```bash
curl http://localhost:8000/generate \
  -d '{
  "description": "A command-line calculator in Rust",
  "requirements": "Should support addition, subtraction, multiplication, and division"
}'
```

### 📌 Check Project Status

**Endpoint:** `GET /project/{project_id}`

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

---

## 🔧 MCP (Model-Compiler-Processor) Endpoints

These endpoints provide direct compilation and error fixing for Rust code:

### 🛠 Compile Rust Code

**Endpoint:** `POST /mcp/compile`

#### 📥 Request Body:

```json
{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\");\n}"
}
```

#### 📤 Response:

```json
{
  "success": true,
  "files": ["Cargo.toml", "src/main.rs"],
  "build_output": "Build successful",
  "run_output": "Hello, World!"
}
```

### 🩹 Compile and Fix Rust Code

**Endpoint:** `POST /mcp/compile-and-fix`

### 📥 Request Body:

```json
{
  "code": "[filename: Cargo.toml]\n[package]\nname = \"hello_world\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n\n[filename: src/main.rs]\nfn main() {\n    println!(\"Hello, World!\" // Missing closing parenthesis\n}",
  "description": "A simple hello world program",
  "max_attempts": 3
}
```

### 📤 Response:

```json
{
  "success": true,
  "attempts": [...],
  "final_files": {...},
  "build_output": "Build successful",
  "run_output": "Hello, World!"
}
```

---

## 📂 Project Structure

```
Rust_coder_lfx/
├── app/                  # Application code
│   ├── compiler.py       # Rust compilation handling
│   ├── llm_client.py     # LLM API client
│   ├── main.py           # FastAPI application
│   ├── mcp_service.py    # Model-Compiler-Processor service
│   ├── prompt_generator.py # LLM prompt generation
│   ├── response_parser.py # Parse LLM responses into files
│   ├── vector_store.py   # Vector database interface
│   └── ...
├── data/                 # Data storage
│   ├── error_examples/   # Error examples for vector search
│   └── project_examples/ # Project examples for vector search
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── examples/             # Example scripts for using the API
├── output/               # Generated project output
├── parse_and_save_qna.py # Q&A parsing utility
├── qdrant_data/          # Vector database storage
├── requirements.txt      # Python dependencies
└── templates/            # API templates
```

---


## 🧠 How It Works

### Vector Search: The system uses Qdrant for storing and searching project examples and error solutions.
### LLM Integration: Communicates with LlamaEdge API for code generation and error fixing via llm_client.py.
### Compilation Feedback Loop: Automatically compiles, detects errors, and fixes them using compiler.py.
### File Parsing: Converts LLM responses into project files with response_parser.py.

---

## 🤝 Contributing
Contributions are welcome! Feel free to submit a Pull Request. 🚀

---

## 📜 License
Licensed under [No license]](LICENSE).
