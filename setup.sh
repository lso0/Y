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

# Check if user is logged into Infisical
echo "Checking Infisical authentication..."
if ! timeout 3 infisical export --projectId="13bce4c5-1ffc-478b-b1ce-76726074f358" --env="dev" --format=dotenv --silent >/dev/null 2>&1; then
    echo "❌ You are not logged into Infisical."
    echo "🔐 Automatically starting login process..."
    echo ""
    
    # Automatically trigger login
    if infisical login; then
        echo "✅ Login successful! Continuing with setup..."
        echo ""
    else
        echo "❌ Login failed. Please check your credentials and try again."
        echo "You can run this setup script again after resolving login issues:"
        echo "   ./setup.sh"
        exit 1
    fi
else
    echo "✅ Infisical authentication verified"
fi

# Export secrets to .env file using the advanced sync script
echo "Fetching secrets from Infisical using sync script..."
./infisical/sync-secrets-advanced.sh -e dev -q

# Also copy to RC directory for local development
cp .env RC/.env

# Load environment variables into current shell before building
set -a  # automatically export all variables
source .env
set +a  # turn off automatic export

# Build the Docker image
echo "Building Docker image..."
docker compose build

echo "Setup complete! You can now run your RC automation with:"
echo "docker compose run --rm rc-automation python rc_a.py [your arguments]" 