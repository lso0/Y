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

# Install Infisical CLI (detect architecture and install appropriate version)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        INFISICAL_ARCH="linux_amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        INFISICAL_ARCH="linux_arm64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -L "https://github.com/Infisical/infisical/releases/latest/download/infisical_${INFISICAL_ARCH}.tar.gz" | tar xz && \
    mv infisical /usr/local/bin/ && \
    chmod +x /usr/local/bin/infisical

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY RC/requirements.txt RC/

# Install Python dependencies
RUN pip install --no-cache-dir -r RC/requirements.txt

# Copy the entire application
COPY . .

# Copy and make setup scripts executable
RUN chmod +x setup.sh && \
    chmod +x tailscale/*.sh && \
    find RC/ -name "*.sh" -exec chmod +x {} \;

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Create directories for configuration and logs
RUN mkdir -p /app/config /app/logs

# Set the working directory to app root
WORKDIR /app

# Create entrypoint script
COPY docker-entrypoint.sh /app/
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER appuser

# Set environment variables with defaults
ENV RC_E_1=""
ENV RC_P_1=""
ENV RC_E_2=""
ENV RC_P_2=""
ENV INFISICAL_TOKEN=""
ENV TAILSCALE_IP=""
ENV TAILSCALE_ENABLED="false"
ENV TAILSCALE_HOSTNAME=""

# Use the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["help"] 