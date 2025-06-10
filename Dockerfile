# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install infisical CLI
RUN apt-get update && apt-get install -y curl && \
    curl -L https://github.com/Infisical/infisical/releases/latest/download/infisical_linux_amd64.tar.gz | tar xz && \
    mv infisical /usr/local/bin/ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY RC/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the RC automation
CMD ["python", "RC/rc_a.py"] 