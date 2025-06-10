# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY RC/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Set the entrypoint to your shell script
ENTRYPOINT ["./RC/shell.sh"] 