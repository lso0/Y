# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY RC/requirements.txt RC/

# Install Python dependencies
RUN pip install --no-cache-dir -r RC/requirements.txt

# Copy the rest of the application
COPY . .

# Make shell script executable
RUN chmod +x RC/shell.sh

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set the working directory to RC
WORKDIR /app/RC

# Set environment variables (these can be overridden by docker-compose)
ENV RC_E_1=""
ENV RC_P_1=""
ENV RC_E_2=""
ENV RC_P_2=""

# Command to run the shell script
CMD ["/app/RC/shell.sh"] 