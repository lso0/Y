#!/bin/bash

# Script to organize Tailscale files into a proper directory structure

echo "🗂️  Organizing Tailscale integration files..."

# Create directory structure
mkdir -p tailscale/{utils,config,docs,scripts}

# Move main scripts
echo "Moving setup and test scripts..."
mv tailscale-setup.sh tailscale/scripts/setup.sh
mv test-tailscale.sh tailscale/scripts/test.sh

# Move Python utilities
echo "Moving Python utilities..."
mv RC/tailscale_utils.py tailscale/utils/tailscale_client.py

# Move documentation
echo "Moving documentation..."
mv TAILSCALE_SETUP.md tailscale/docs/SETUP_GUIDE.md

# Create configuration examples
echo "Creating configuration examples..."
cat > tailscale/config/example.env << 'EOF'
# Tailscale Configuration Example
# Copy this to your main .env file or source separately

# Your Tailscale IP address (automatically set by setup)
TAILSCALE_IP=100.64.1.x

# Enable/disable Tailscale features
TAILSCALE_ENABLED=true

# Your hostname on the Tailscale network
TAILSCALE_HOSTNAME=your-hostname

# Optional: Specific peers you need to connect to
REQUIRED_TAILSCALE_PEERS=100.64.1.2,100.64.1.3
EOF

# Create main README
cat > tailscale/README.md << 'EOF'
# Tailscale Integration

This directory contains all Tailscale-related files for secure networking and authentication.

## Quick Start

1. **Install and configure Tailscale:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Test the integration:**
   ```bash
   ./scripts/test.sh
   ```

3. **Use in Python code:**
   ```python
   from tailscale.utils.tailscale_client import TailscaleClient
   client = TailscaleClient()
   ```

## Directory Structure

- `scripts/` - Installation and testing scripts
- `utils/` - Python libraries and utilities
- `config/` - Configuration files and examples
- `docs/` - Documentation and guides

See `docs/SETUP_GUIDE.md` for complete documentation.
EOF

# Create utility helper
cat > tailscale/utils/__init__.py << 'EOF'
"""
Tailscale utilities package.
Provides easy access to Tailscale networking functions.
"""

from .tailscale_client import TailscaleClient, get_tailscale_client, ensure_tailscale_connectivity

__all__ = ['TailscaleClient', 'get_tailscale_client', 'ensure_tailscale_connectivity']
EOF

# Update the main setup.sh to use new structure
echo "Updating main setup.sh..."
sed -i.bak 's|./tailscale-setup.sh|./tailscale/scripts/setup.sh|g' setup.sh

# Update imports in RC files if they exist
if [ -f "RC/rc_a.py" ]; then
    echo "Updating Python imports..."
    # Add path for new structure
    cat > RC/import_tailscale.py << 'EOF'
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Now you can import Tailscale utilities
from tailscale.utils import get_tailscale_client, ensure_tailscale_connectivity
EOF
fi

echo "✅ Tailscale files organized!"
echo ""
echo "📁 New structure:"
echo "tailscale/"
echo "├── README.md"
echo "├── scripts/"
echo "│   ├── setup.sh"
echo "│   └── test.sh"
echo "├── utils/"
echo "│   ├── __init__.py"
echo "│   └── tailscale_client.py"
echo "├── config/"
echo "│   └── example.env"
echo "└── docs/"
echo "    └── SETUP_GUIDE.md"
echo ""
echo "🚀 Run './tailscale/scripts/setup.sh' to get started!" 