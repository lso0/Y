# 🛠️ Shared Infrastructure

## Overview
Common utilities, security components, and configuration shared across all automation services.

## Directory Structure
```
shared/
├── utils/             # Security and utility scripts
├── config/            # Global configuration files  
└── docs/             # Shared documentation
```

## Security Components

### 🔐 Secure Token Manager (`utils/secure_token_manager.py`)
YubiKey-based token encryption system for secure credential storage.

**Features:**
- AES-256-CBC encryption with PBKDF2 key derivation
- YubiKey HMAC-SHA1 challenge-response authentication
- Multi-factor security (YubiKey + passcode + physical touch)
- No plaintext tokens in logs or command history

**Usage:**
```bash
# Encrypt a token
python3 shared/utils/secure_token_manager.py --encrypt 'your_token_here' --passcode 'your_passcode'

# Decrypt for display
python3 shared/utils/secure_token_manager.py --decrypt --passcode 'your_passcode'

# Decrypt for scripting (token only)
python3 shared/utils/secure_token_manager.py --token-only --passcode 'your_passcode'

# Run command with decrypted token
python3 shared/utils/secure_token_manager.py --run infisical run --token DECRYPTED_TOKEN -- your_command
```

### 🚀 Secure Server Launcher (`utils/secure_server.py`)
Wrapper for starting services with YubiKey-secured tokens.

### 📋 Deployment Scripts (`utils/deploy_to_ubuntu.sh`)
Shared deployment utilities for Ubuntu server setup.

## Documentation (`docs/`)
- `SECURE_TOKEN_SETUP.md` - Complete YubiKey setup guide
- Additional shared documentation

## Global Dependencies
See root `requirements.txt` for shared dependencies:
- `cryptography` - Encryption operations
- `fastapi` - Web framework
- `requests` - HTTP client
- `python-dotenv` - Environment management 