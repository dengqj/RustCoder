# Base image with Python and Rust
FROM python:3.10-slim

# Install Rust toolchain
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . $HOME/.cargo/env

# Add cargo to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Install openmcp proxy with robust extraction handling
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -LO https://github.com/decentralized-mcp/proxy/releases/latest/download/openmcp-x86_64-unknown-linux-gnu.tgz && \
        mkdir -p openmcp_extract && \
        tar -xzf openmcp-x86_64-unknown-linux-gnu.tgz -C openmcp_extract && \
        find openmcp_extract -name "openmcp" -type f -exec cp {} /usr/local/bin/ \; || \
        echo "OpenMCP binary not found, trying alternative path" && \
        find openmcp_extract -type f -perm -u+x -exec cp {} /usr/local/bin/openmcp \; && \
        chmod +x /usr/local/bin/openmcp && \
        rm -rf openmcp_extract openmcp-x86_64-unknown-linux-gnu.tgz; \
    elif [ "$ARCH" = "aarch64" ]; then \
        curl -LO https://github.com/decentralized-mcp/proxy/releases/latest/download/openmcp-aarch64-unknown-linux-gnu.tgz && \
        mkdir -p openmcp_extract && \
        tar -xzf openmcp-aarch64-unknown-linux-gnu.tgz -C openmcp_extract && \
        find openmcp_extract -name "openmcp" -type f -exec cp {} /usr/local/bin/ \; || \
        echo "OpenMCP binary not found, trying alternative path" && \
        find openmcp_extract -type f -perm -u+x -exec cp {} /usr/local/bin/openmcp \; && \
        chmod +x /usr/local/bin/openmcp && \
        rm -rf openmcp_extract openmcp-aarch64-unknown-linux-gnu.tgz; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi

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
