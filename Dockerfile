# Use Python 3.11 as the base image for better package compatibility
FROM python:3.11-slim

# Install system dependencies for automation
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    tar \
    gzip \
    ca-certificates \
    bash \
    git \
    gnupg \
    lsb-release \
    # Virtual display for headless automation
    xvfb \
    # Build tools for Python packages (pyscard, etc.)
    build-essential \
    gcc \
    pkg-config \
    # PCSC development headers for pyscard (YubiKey support)
    libpcsclite-dev \
    pcscd \
    && rm -rf /var/lib/apt/lists/*

# Install Infisical CLI (optional - fallback to dummy if download fails)
RUN ARCH=$(dpkg --print-architecture) && \
    echo "Detected architecture: $ARCH" && \
    if [ "$ARCH" = "amd64" ]; then \
        INFISICAL_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        INFISICAL_ARCH="arm64"; \
    else \
        echo "Unsupported architecture: $ARCH, creating dummy Infisical binary"; \
        echo '#!/bin/bash\necho "Infisical CLI not available for this architecture"' > /usr/local/bin/infisical; \
        chmod +x /usr/local/bin/infisical; \
        exit 0; \
    fi && \
    echo "Attempting to download Infisical CLI..." && \
    (curl -fsSL -o /usr/local/bin/infisical \
        "https://github.com/Infisical/infisical/releases/latest/download/infisical_linux_${INFISICAL_ARCH}" \
    || echo "Download failed, creating fallback") && \
    if [ ! -s /usr/local/bin/infisical ]; then \
        echo "Creating fallback Infisical binary..."; \
        echo '#!/bin/bash\necho "Infisical CLI download failed - using local secrets only"' > /usr/local/bin/infisical; \
    fi && \
    chmod +x /usr/local/bin/infisical && \
    echo "Infisical setup complete"

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Copy and make scripts executable
RUN chmod +x run.sh && \
    chmod +x scripts/infisical/*.py && \
    chmod +x scripts/infisical/*.sh && \
    chmod +x scripts/tailscale/*.sh && \
    chmod +x scripts/*.sh && \
    find cli_x/ -name "*.py" -exec chmod +x {} \; && \
    find cli_x/ -name "*.sh" -exec chmod +x {} \;

# Create directories and set up user
RUN useradd -m appuser && \
    mkdir -p /app/config /app/logs /app/cli_x/dev/auto/services/youtube/data/screenshots && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/config /app/logs

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Environment variables for automation
ENV INFISICAL_TOKEN=""
ENV TAILSCALE_IP=""
ENV TAILSCALE_ENABLED="false"
ENV TAILSCALE_HOSTNAME=""

# Use the entrypoint script
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["help"] 