# Base image with Python and Rust
FROM python:3.10-slim

# Install Rust toolchain
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . $HOME/.cargo/env

# Add cargo to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || echo "Some packages not found, continuing..."

# Install MCP packages explicitly
RUN pip install mcp-python mcp-proxy

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output

# Expose port for FastAPI
EXPOSE 8000

# Add entry point for MCP server
CMD ["python", "-m", "app.mcp_server"]