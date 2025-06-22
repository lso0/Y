# Use Python 3.12 as the base image with more tools
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    tar \
    gzip \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install Infisical CLI (optional - install if download works)
RUN echo "Attempting to install Infisical CLI..." && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        INFISICAL_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        INFISICAL_ARCH="arm64"; \
    else \
        echo "Unsupported architecture: $ARCH, skipping Infisical" && exit 0; \
    fi && \
    (curl -L -o /usr/local/bin/infisical "https://github.com/Infisical/infisical/releases/download/infisical-cli%2Fv0.28.1/infisical_0.28.1_linux_${INFISICAL_ARCH}" && \
     chmod +x /usr/local/bin/infisical && \
     infisical --version && \
     echo "✅ Infisical CLI installed successfully") || \
    (echo "⚠️  Infisical CLI installation failed - continuing without it" && \
     echo "#!/bin/bash" > /usr/local/bin/infisical && \
     echo "echo 'Infisical CLI not available. Please install manually or set environment variables directly.'" >> /usr/local/bin/infisical && \
     chmod +x /usr/local/bin/infisical)

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY RC/requirements.txt RC/

# Install Python dependencies
RUN pip install --no-cache-dir -r RC/requirements.txt

# Copy the entire application
COPY . .

# Copy and make setup scripts executable
RUN chmod +x run.sh && \
    chmod +x scripts/*.sh && \
    chmod +x scripts/docker-entrypoint.sh && \
    chmod +x tailscale/*.sh && \
    find RC/ -name "*.sh" -exec chmod +x {} \;

# Create a non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/scripts/docker-entrypoint.sh
USER appuser

# Create directories for configuration and logs
RUN mkdir -p /app/config /app/logs

# Set the working directory to app root
WORKDIR /app

# Set environment variables with defaults
ENV RC_E_1=""
ENV RC_P_1=""
ENV RC_E_2=""
ENV RC_P_2=""
ENV INFISICAL_TOKEN=""
ENV TAILSCALE_IP=""
ENV TAILSCALE_ENABLED="false"
ENV TAILSCALE_HOSTNAME=""

# Use the entrypoint script from scripts directory
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["help"] 