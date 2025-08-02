# Base image with Python and Rust - Using a newer base image with modern GLIBC
FROM python:3.11-bullseye

# Install Rust toolchain
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . $HOME/.cargo/env

# Add cargo to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Install openmcp proxy via the installer
RUN curl -sSfL 'https://raw.githubusercontent.com/decentralized-mcp/proxy/refs/heads/master/install.sh' | bash

# Set working directory
WORKDIR /app

# Install pip dependencies first for better caching
COPY requirements.txt .

# Install packages
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir openai && \
    pip install --no-cache-dir cmcp mcp-python mcp-proxy && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output

# Expose ports
EXPOSE 8000 3000

# Default command - start the REST API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
