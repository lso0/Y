# Tailscale Status Checking

This project now includes comprehensive Tailscale status checking capabilities to help you verify VPN connectivity, authentication, and network status.

## Quick Start

### Check Tailscale Status

```bash
# Comprehensive Tailscale check (bash version)
./run.sh tailscale-check

# Python version with more detailed output
python3 scripts/tailscale-status.py
```

## Available Tools

### 1. Bash Script: `scripts/tailscale-check.sh`

A comprehensive bash script that checks:
- ✅ Tailscale installation and version
- ✅ Service status (running/stopped)
- ✅ Authentication status
- ✅ Network connectivity and IP addresses
- ✅ Peer discovery and connectivity
- ✅ Environment configuration
- ✅ Python integration
- ✅ VPN traffic testing

**Usage:**
```bash
# Run directly
./scripts/tailscale-check.sh

# Or via the main runner
./run.sh tailscale-check
```

### 2. Python Script: `scripts/tailscale-status.py`

A Python script that provides detailed status information using the existing `tailscale_utils.py` library.

**Usage:**
```bash
# Comprehensive check
python3 scripts/tailscale-status.py

# Get raw JSON data
python3 scripts/tailscale-status.py json

# Get just the IP address
python3 scripts/tailscale-status.py ip

# Ping a specific peer
python3 scripts/tailscale-status.py ping 100.64.1.2

# Test connectivity to multiple peers
python3 scripts/tailscale-status.py connectivity 100.64.1.2 100.64.1.3
```

### 3. Existing Tailscale Utilities

The project already includes:
- `tailscale/test-tailscale.sh` - Basic Tailscale testing
- `RC/tailscale_utils.py` - Python library for Tailscale integration
- `tailscale/tailscale-setup.sh` - Tailscale setup script

## What Gets Checked

### Installation Status
- ✅ Tailscale CLI availability
- ✅ Version information
- ✅ Installation recommendations if missing

### Service Status
- ✅ Tailscale daemon running status
- ✅ Authentication status
- ✅ Current user and tailnet information

### Network Connectivity
- ✅ Tailscale IPv4 and IPv6 addresses
- ✅ Connectivity to Tailscale coordination server
- ✅ Peer discovery and status
- ✅ Peer-to-peer connectivity testing

### Configuration
- ✅ Environment variables (`.env.tailscale`)
- ✅ Python integration status
- ✅ Docker configuration compatibility

## Example Output

### When Tailscale is Not Running
```
🔗 Tailscale Comprehensive Status Check
================================================

🔍 Step 1: Checking Tailscale Installation
✅ Tailscale CLI is installed (version: 1.xx.x)

🔍 Step 2: Checking Tailscale Service Status
❌ Tailscale service is not running
ℹ️ Start Tailscale with: sudo tailscale up

🔍 Step 3: Checking Authentication Status
⚠️ Cannot check authentication - service not running

📋 Tailscale Status Summary
================================================
✅ Tailscale is installed
❌ Tailscale service is not running
❌ Not authenticated with Tailscale
❌ VPN connection is not active
```

### When Tailscale is Working
```
🔗 Tailscale Comprehensive Status Check
================================================

🔍 Step 1: Checking Tailscale Installation
✅ Tailscale CLI is installed (version: 1.xx.x)

🔍 Step 2: Checking Tailscale Service Status
✅ Tailscale service is running

🔍 Step 3: Checking Authentication Status
✅ Authenticated with Tailscale
ℹ️ User: username
ℹ️ Tailnet: your-tailnet

🔍 Step 4: Checking Network Connectivity
✅ Tailscale IPv4: 100.64.1.1
✅ Can reach Tailscale coordination server

🔍 Step 5: Checking Peer Connectivity
✅ Found 2 peer(s) in your tailnet
ℹ️ Peer details:
  ✅ laptop (100.64.1.2) - Online
  ⚠️ server (100.64.1.3) - Offline

🎉 All Tailscale checks passed! Your VPN is working correctly.
```

## Integration with Main System

The Tailscale check is now integrated into the main `run.sh` script:

```bash
# Show all available commands (including tailscale-check)
./run.sh help

# Run the Tailscale check
./run.sh tailscale-check
```

## Troubleshooting

### Common Issues

1. **Tailscale not installed**
   ```bash
   # Linux
   curl -fsSL https://tailscale.com/install.sh | sh
   
   # macOS
   brew install tailscale
   ```

2. **Service not running**
   ```bash
   sudo tailscale up
   ```

3. **Python integration issues**
   ```bash
   pip install -r RC/requirements.txt
   ```

4. **Environment configuration missing**
   ```bash
   ./tailscale/tailscale-setup.sh
   ```

### Getting Help

- Run `./run.sh tailscale-check` for detailed status
- Check the existing documentation in `tailscale/TAILSCALE_SETUP.md`
- Use the existing test script: `./tailscale/test-tailscale.sh`

## Integration with Existing Tools

These new tools work alongside the existing Tailscale infrastructure:

- **Complements** the existing `tailscale/test-tailscale.sh`
- **Uses** the existing `RC/tailscale_utils.py` library
- **Works with** the existing setup scripts
- **Provides** more detailed diagnostics and troubleshooting

The new tools provide more comprehensive checking and better integration with the overall system check workflow. 