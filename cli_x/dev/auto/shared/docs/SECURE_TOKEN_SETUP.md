# 🔐 Secure Token Management with YubiKey

This system encrypts your Infisical token using **YubiKey + passcode** for maximum security.

## 🎯 Benefits

- ✅ **No exposed tokens** in command line or process lists
- ✅ **YubiKey hardware security** - physical device required
- ✅ **Passcode protection** - something you know
- ✅ **Portable across machines** - encrypted token can be copied
- ✅ **Audit trail** - YubiKey touch required for each use

## 📋 Prerequisites

### 1. YubiKey Setup
Your YubiKey needs HMAC-SHA1 challenge-response configured on slot 2:

```bash
# Install YubiKey Manager
pip install yubikey-manager

# Configure YubiKey slot 2 for HMAC-SHA1 (one-time setup)
ykman otp chalresp --touch --generate 2
```

### 2. Install Dependencies
```bash
pip install cryptography==41.0.7
```

## 🚀 Usage

### Step 1: Encrypt Your Token (One-time Setup)

```bash
# Encrypt your Infisical token
python3 utils/secure_token_manager.py --encrypt 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# Output:
# 🔐 Encrypting token with YubiKey...
# 👆 Please touch your YubiKey when it blinks...
# 🔒 Enter your passcode: ****
# ✅ Token encrypted and saved to: ~/.fastmail_automation/encrypted_token.json
```

### Step 2: Start Server Securely

```bash
# Start server with YubiKey authentication
python3 utils/secure_server.py

# Output:
# 🔐 Secure FastMail Automation Server Launcher
# 🔓 Decrypting token with YubiKey...
# 👆 Please touch your YubiKey when it blinks...
# 🔒 Enter your passcode: ****
# ✅ Token decrypted successfully!
# 🚀 Running secure infisical command...
# 2:15PM INF Injecting 9 Infisical secrets into your application process
# ✅ Server started successfully!
```

### Step 3: Run Any Infisical Command Securely

```bash
# Run any command with encrypted token
python3 utils/secure_token_manager.py --run python servers/enhanced_automation_server.py
python3 utils/secure_token_manager.py --run python -c "import os; print('FM_M_0:', os.getenv('FM_M_0')[:10])"
```

## 🔒 Security Features

### Multi-Factor Authentication
1. **Something you have**: YubiKey hardware device
2. **Something you know**: Your personal passcode
3. **Something you do**: Physical touch confirmation

### Encryption Details
- **Algorithm**: AES-256-CBC
- **Key Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations)
- **YubiKey Response**: HMAC-SHA1 challenge-response
- **Combined Secret**: `yubikey_response:passcode`

### Storage Security
- Token encrypted with YubiKey + passcode
- Stored in `~/.fastmail_automation/encrypted_token.json`
- No plaintext secrets anywhere
- Each decryption requires YubiKey touch

## 🛠 Advanced Usage

### Test Decryption
```bash
python3 utils/secure_token_manager.py --decrypt
```

### Batch Operations
```bash
# Multiple commands can use the same decrypted token
python3 utils/secure_token_manager.py --run bash -c "
  echo 'Starting server...' && 
  python servers/enhanced_automation_server.py
"
```

### Copy Encrypted Token to New Machine
```bash
# Copy encrypted token file to new machine
scp ~/.fastmail_automation/encrypted_token.json user@newmachine:~/.fastmail_automation/

# Token works on new machine with same YubiKey + passcode
```

## 🚨 Security Best Practices

### ✅ Do's
- Keep your YubiKey secure and with you
- Use a strong, unique passcode
- Regularly backup the encrypted token file
- Touch YubiKey only when you initiate commands

### ❌ Don'ts  
- Never share your passcode
- Don't leave YubiKey unattended in computers
- Don't copy the raw Infisical token anywhere
- Don't bypass the secure system

## 🔧 Troubleshooting

### YubiKey Not Detected
```bash
# Check if YubiKey is detected
ykman info

# Check if slot 2 is configured
ykman otp info 2
```

### Wrong Passcode/YubiKey
```bash
# Re-encrypt with correct YubiKey
python3 utils/secure_token_manager.py --encrypt 'your_new_token'
```

### Permission Issues
```bash
# Fix permissions
chmod 700 ~/.fastmail_automation
chmod 600 ~/.fastmail_automation/encrypted_token.json
```

## 📈 Migration from Raw Tokens

### Before (Insecure)
```bash
# ❌ Token visible everywhere
ssh server "infisical run --token='eyJhbGci...' -- python server.py"
```

### After (Secure)
```bash
# ✅ No tokens visible, YubiKey required
ssh server "python3 utils/secure_server.py"
```

This system provides military-grade security while maintaining the convenience of token-based authentication across multiple machines. 