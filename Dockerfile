# Base image with Python and Rust - Using a newer base image with modern GLIBC
FROM python:3.11-bullseye

# Install Rust toolchain
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    . $HOME/.cargo/env

# Add cargo to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Directly download and install OpenMCP from source to avoid binary compatibility issues
# RUN apt-get install -y git && \
#     git clone https://github.com/decentralized-mcp/proxy.git && \
#     cd proxy && \
#     cargo build --release && \
#     cp target/release/openmcp /usr/local/bin/ && \
#     chmod +x /usr/local/bin/openmcp && \
#     cd .. && \
#     rm -rf proxy

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
