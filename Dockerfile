# Use Python 3.12 as the base image with more tools
FROM python:3.12-slim

# Install system dependencies for Chrome and automation
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    tar \
    gzip \
    ca-certificates \
    bash \
    git \
    # Chrome dependencies 
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libnss3 \
    # Virtual display for headless Chrome
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome repository and install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install latest Infisical CLI
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        INFISICAL_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        INFISICAL_ARCH="arm64"; \
    else \
        echo "Unsupported architecture: $ARCH, skipping Infisical" && exit 1; \
    fi && \
    curl -L -o /usr/local/bin/infisical "https://github.com/Infisical/infisical/releases/latest/download/infisical_linux_${INFISICAL_ARCH}" && \
    chmod +x /usr/local/bin/infisical && \
    infisical --version

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