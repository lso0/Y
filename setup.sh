#!/bin/bash

# Check if Infisical CLI is installed
if ! command -v infisical &> /dev/null; then
    echo "Installing Infisical CLI..."
    curl -L https://github.com/Infisical/infisical/releases/latest/download/infisical_darwin_arm64.tar.gz | tar xz
    sudo mv infisical /usr/local/bin/
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Please install Docker Desktop first: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Please start Docker Desktop first"
    exit 1
fi

# Authenticate with Infisical
echo "Please authenticate with Infisical..."
infisical login

# Export secrets to .env file in root directory
echo "Fetching secrets from Infisical..."
infisical export --env=prod --format=dotenv > .env

# Also copy to RC directory for local development
cp .env RC/.env

# Build the Docker image
echo "Building Docker image..."
docker compose build

echo "Setup complete! You can now run your RC automation with:"
echo "docker compose run --rm rc-automation python rc_a.py [your arguments]" 