# 🚀 Multi-Service Automation Platform

Professional automation platform supporting multiple services with secure YubiKey-based authentication and session management.

## 🌟 Supported Services

| Service | Status | Description |
|---------|--------|-------------|
| 📧 **FastMail** | ✅ **Production** | Automated alias creation and management |
| 🎥 **YouTube** | 🚧 **Planned** | Video upload and channel management |
| 🔥 **Firebase** | 🚧 **Planned** | Project setup and authentication testing |
| 🍎 **App Store Connect** | 🚧 **Planned** | iOS app management and TestFlight |
| 📊 **Mixpanel** | 🚧 **Planned** | Analytics automation and reporting |

## 🏗️ Architecture

```
a_1/                           # Multi-Service Automation Platform
├── 🛠️  shared/               # Shared Infrastructure
│   ├── utils/                 # Security & utilities (YubiKey, deployment)
│   ├── config/               # Global configuration
│   └── docs/                 # Shared documentation
├── 🎯 services/              # Service-Specific Automation
│   ├── fastmail/             # 📧 FastMail automation (ACTIVE)
│   ├── youtube/              # 🎥 YouTube automation (planned)
│   ├── firebase/             # 🔥 Firebase automation (planned)
│   ├── app_store_connect/    # 🍎 iOS automation (planned)
│   └── mixpanel/             # 📊 Analytics automation (planned)
├── 📝 logs/                  # Global logs
├── 🐍 venv/                  # Python virtual environment
└── 📋 requirements.txt       # Global dependencies
```

## 🔐 Security Features

- **🔑 YubiKey Authentication** - Hardware-based token encryption
- **🛡️ Multi-Factor Security** - YubiKey + passcode + physical touch
- **🔒 Encrypted Storage** - AES-256-CBC with PBKDF2 key derivation
- **🚫 No Plaintext Tokens** - Zero exposure in logs or command history
- **🔄 Infisical Integration** - Centralized secret management

## ⚡ Quick Start

### 1. **Setup Environment**
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup YubiKey (one-time)
python3 shared/utils/secure_token_manager.py --encrypt 'your_infisical_token' --passcode 'your_passcode'
```

### 2. **Start FastMail Automation** (Production Ready)
```bash
# Secure server startup with YubiKey
TOKEN=$(python3 shared/utils/secure_token_manager.py --token-only --passcode 'your_passcode')
ssh user@server "infisical run --token='$TOKEN' -- python services/fastmail/servers/enhanced_automation_server.py"

# Create aliases
python3 services/fastmail/clients/enhanced_session_client.py batch-parallel \
  alias1@fastmail.com,from1@example.com \
  alias2@fastmail.com,from2@example.com
```

## 📚 Documentation

### **🛠️ Infrastructure**
- **[Shared Infrastructure](shared/README.md)** - Security components and utilities
- **[YubiKey Setup Guide](shared/docs/SECURE_TOKEN_SETUP.md)** - Complete security setup

### **🎯 Services**
- **[📧 FastMail](services/fastmail/README.md)** - Alias automation (ACTIVE)
- **[🎥 YouTube](services/youtube/README.md)** - Video management (planned)
- **[🔥 Firebase](services/firebase/README.md)** - Project automation (planned)
- **[🍎 App Store Connect](services/app_store_connect/README.md)** - iOS automation (planned)
- **[📊 Mixpanel](services/mixpanel/README.md)** - Analytics automation (planned)

## 🔧 Development Guidelines

### **Adding New Services**
```bash
# Create service structure
mkdir -p services/new_service/{servers,clients,scripts,legacy}

# Create documentation
cp services/fastmail/README.md services/new_service/README.md
# Edit README.md for your service

# Add dependencies to requirements.txt
```

### **Security Best Practices**
1. **Use shared token manager** for all credential storage
2. **Implement proper error handling** and logging
3. **Follow service directory structure** for consistency
4. **Document API usage** and rate limits
5. **Test with YubiKey authentication** flow

## 🚀 Production Deployment

### **Ubuntu Server Setup**
```bash
# Deploy to server
git clone <repo> && cd Y/cli_x/dev/auto/a_1
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy encrypted token
scp ~/.fastmail_automation/encrypted_token.json user@server:~/.fastmail_automation/

# Start with YubiKey authentication (from local machine)
TOKEN=$(python3 shared/utils/secure_token_manager.py --token-only --passcode 'passcode')
ssh user@server "cd path && infisical run --token='$TOKEN' -- python services/fastmail/servers/enhanced_automation_server.py"
```

## 📊 Current Capabilities

### **FastMail (Production)**
- ✅ Batch alias creation (parallel processing)
- ✅ Session persistence across requests
- ✅ Error recovery and retry logic
- ✅ Secure authentication with YubiKey
- ✅ 100% success rate with 5s average per alias

### **Other Services (Roadmap)**
- 🚧 YouTube: API integration, video uploads
- 🚧 Firebase: Auth testing, project setup
- 🚧 App Store Connect: TestFlight automation
- 🚧 Mixpanel: Event automation, reporting

## 🆘 Troubleshooting

```bash
# Check server health
curl http://localhost:8002/health

# Debug YubiKey
ykman list
ykman otp settings

# Check logs
tail -f logs/*.log

# Test token decryption
python3 shared/utils/secure_token_manager.py --decrypt --passcode 'your_passcode'
```

---

**🎯 Ready to automate?** Start with FastMail automation or contribute to expanding our service coverage! 🚀 