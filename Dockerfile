# Start with Python base image
FROM python:3.10-slim

# Install Rust and Cargo
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && echo 'source $HOME/.cargo/env' >> $HOME/.bashrc

# Add cargo to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]