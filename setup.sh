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

# Function to check if user is logged in
check_infisical_login() {
    if ! infisical token list &> /dev/null; then
        return 1
    fi
    return 0
}

# Authenticate with Infisical
echo "Checking Infisical authentication..."
if ! check_infisical_login; then
    echo "Please authenticate with Infisical..."
    infisical login
    
    # Verify login was successful
    # if ! check_infisical_login; then
    #     echo "Error: Infisical authentication failed. Please try again."
    #     exit 1
    # fi
fi

wait

# Ask for service token
echo "Please enter your Infisical service token (you can get this from https://app.infisical.com/dashboard > Project Settings > Service Tokens):"
read -p "Service Token: " SERVICE_TOKEN

# Validate service token
# if [ -z "$SERVICE_TOKEN" ]; then
#     echo "Error: Service token cannot be empty"
#     exit 1
# fi

# Export secrets to .env file in root directory
echo "Fetching secrets from Infisical..."
if ! INFISICAL_TOKEN="$SERVICE_TOKEN" infisical export --env=prod --format=dotenv > .env; then
    echo "Error: Failed to export secrets. Please check your service token and try again."
    exit 1
fi

# Also copy to RC directory for local development
cp .env RC/.env

# Build the Docker image
echo "Building Docker image..."
docker compose build

echo "Setup complete! You can now run your RC automation with:"
echo "docker compose run --rm rc-automation python rc_a.py [your arguments]" 