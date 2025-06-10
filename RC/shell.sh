#!/bin/bash

# Check if .env file exists, if not create it using Infisical
if [ ! -f .env ]; then
    echo "No .env file found. Fetching secrets from Infisical..."
    infisical export --env=prod --format=dotenv > .env
    echo ".env file created with secrets from Infisical."
else
    echo ".env file already exists."
fi

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "No virtual environment found. Creating one..."
    python3.12 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete. You can now run your RC automation."