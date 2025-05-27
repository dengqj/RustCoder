# Base image with Python and Rust
FROM python:3.10-slim

# Install Rust toolchain
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . $HOME/.cargo/env

# Add cargo to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Install openmcp proxy - Use architecture detection
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -LO https://github.com/decentralized-mcp/proxy/releases/latest/download/openmcp-x86_64-unknown-linux-gnu.tgz && \
        tar zxvf openmcp-x86_64-unknown-linux-gnu.tgz; \
    elif [ "$ARCH" = "aarch64" ]; then \
        curl -LO https://github.com/decentralized-mcp/proxy/releases/latest/download/openmcp-aarch64-unknown-linux-gnu.tgz && \
        tar zxvf openmcp-aarch64-unknown-linux-gnu.tgz; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    mv openmcp /usr/local/bin/ && \
    chmod +x /usr/local/bin/openmcp

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
