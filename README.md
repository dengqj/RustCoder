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
cd Project3
docker-compose up -d

### Manual Setup
```bash
git clone <repository-url>
cd Project3
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 🔥 Usage
The API provides the following endpoints:

### 🎯 Generate a Project
Endpoint: POST /generate

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

## 📂 Project Structure
```
Project3/
├── app/                  # Application code
├── data/                 # Data storage
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── output/               # Generated project output
├── parse_and_save_qna.py # Q&A parsing utility
├── qdrant_data/          # Vector database storage
├── requirements.txt      # Python dependencies
├── templates/            # API templates
└── tests/ 
```

---

## 🤝 Contributing
Contributions are welcome! Feel free to submit a Pull Request. 🚀

---

## 📜 License
Licensed under [No license]](LICENSE).
