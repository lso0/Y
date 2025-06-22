#!/bin/bash

# Infisical Secrets Sync Script
# Automatically initializes and exports secrets from Infisical

set -e  # Exit on any error

# Configuration
PROJECT_NAME="Y"
PROJECT_ID="13bce4c5-1ffc-478b-b1ce-76726074f358"  # Project Y ID
ENV_FILE=".env"
ENVIRONMENT="dev"  # Change this to your desired environment (dev, staging, production, etc.)

echo "🔐 Starting Infisical secrets sync..."

# Check if infisical CLI is installed
if ! command -v infisical &> /dev/null; then
    echo "❌ Infisical CLI is not installed. Please install it first."
    echo "   You can install it with: brew install infisical/infisical/infisical"
    exit 1
fi

# Check if user is logged in
if ! infisical user --help &> /dev/null; then
    echo "❌ Please login to Infisical first with: infisical login"
    exit 1
fi

# Export secrets to .env file using project ID directly (fully automated)
echo "📤 Exporting secrets from environment: $ENVIRONMENT"
echo "📋 Using project: $PROJECT_NAME (ID: $PROJECT_ID)"
if infisical export --projectId="$PROJECT_ID" --env="$ENVIRONMENT" --format=dotenv > "$ENV_FILE"; then
    echo "✅ Secrets successfully exported to $ENV_FILE"
    
    # Optional: Show number of secrets exported (without revealing values)
    SECRET_COUNT=$(grep -c "^[^#]" "$ENV_FILE" 2>/dev/null || echo "0")
    echo "📊 Exported $SECRET_COUNT secrets"
    
    # Set appropriate permissions on .env file
    chmod 600 "$ENV_FILE"
    echo "🔒 Set secure permissions on $ENV_FILE"
    
else
    echo "❌ Failed to export secrets"
    exit 1
fi

echo "🎉 Secrets sync completed successfully!"
echo ""
echo "💡 To use the secrets in your current shell:"
echo "   source $ENV_FILE"
echo ""
echo "💡 To run a command with secrets loaded:"
echo "   infisical run --env=$ENVIRONMENT -- your-command"
