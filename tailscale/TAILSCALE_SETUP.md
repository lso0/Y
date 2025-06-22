# Tailscale Integration Guide

This guide explains how to set up and use Tailscale with your RC automation project for secure networking and authentication.

## Overview

Tailscale provides a secure, zero-configuration VPN that creates a private network between your devices. This integration allows your RC automation to:

- Securely communicate with other devices on your Tailscale network
- Authenticate using Tailscale's identity-aware networking
- Access remote services without exposing them to the public internet

## Quick Start

### 1. Run the Setup

```bash
# This will install Tailscale, authenticate, and configure your project
./setup.sh
```

The setup script will automatically:
- Install Tailscale (via Homebrew on macOS or apt on Linux)
- Authenticate with your Tailscale account
- Configure environment variables
- Integrate with your existing Infisical setup

### 2. Verify Installation

```bash
# Check Tailscale status
sudo tailscale status

# Test the Python integration
cd RC
python tailscale_utils.py status
```

## Manual Tailscale Setup

If you prefer to set up Tailscale manually:

### macOS
```bash
brew install tailscale
sudo tailscale up
```

### Linux
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Then run the Tailscale setup script:
```bash
./tailscale-setup.sh
```

## Using Tailscale in Your Code

The project includes a Python utility module for Tailscale integration:

```python
from tailscale_utils import get_tailscale_client, ensure_tailscale_connectivity

# Get a Tailscale client
client = get_tailscale_client()

# Check if Tailscale is enabled
if client.is_enabled():
    print(f"Tailscale IP: {client.get_ip()}")
    
    # Get network information
    network_info = client.get_network_info()
    
    # Make requests to peers
    response = client.make_request('100.64.1.2', 8080, '/api/status')
    
    # Check peer connectivity
    online, ping_time = client.ping_peer('100.64.1.2')
```

## Environment Variables

The following environment variables are automatically configured:

- `TAILSCALE_IP`: Your device's Tailscale IP address
- `TAILSCALE_ENABLED`: Whether Tailscale is active (true/false)
- `TAILSCALE_HOSTNAME`: Your device's hostname

## Docker Integration

The Docker setup has been configured to work with Tailscale:

- Uses host networking mode to access Tailscale
- Includes Tailscale environment variables
- Allows containers to communicate with Tailscale peers

## Common Use Cases

### 1. Secure API Access

```python
# Access a service running on another Tailscale device
client = get_tailscale_client()
response = client.make_request('100.64.1.5', 3000, '/api/data')
```

### 2. Peer Discovery

```python
# List all peers on your Tailscale network
client = get_tailscale_client()
peers = client.get_peers()
for peer in peers:
    print(f"Peer: {peer.get('HostName')} - {peer.get('TailscaleIPs')}")
```

### 3. Connectivity Checks

```python
# Ensure required peers are accessible before proceeding
required_peers = ['100.64.1.2', '100.64.1.3']
if ensure_tailscale_connectivity(required_peers):
    print("All required peers are accessible")
else:
    print("Some peers are not accessible")
```

## CLI Tools

The Tailscale utilities can be used from the command line:

```bash
cd RC

# Show network status
python tailscale_utils.py status

# Get your Tailscale IP
python tailscale_utils.py ip

# List peers
python tailscale_utils.py peers

# Ping a peer
python tailscale_utils.py ping 100.64.1.2
```

## Troubleshooting

### Tailscale Not Working in Docker

If Tailscale doesn't work inside Docker containers:

1. Ensure the container uses host networking:
   ```yaml
   network_mode: "host"
   ```

2. Verify Tailscale is running on the host:
   ```bash
   sudo tailscale status
   ```

### Authentication Issues

If authentication fails:

1. Check your Tailscale account at https://login.tailscale.com/admin/machines
2. Re-authenticate:
   ```bash
   sudo tailscale down
   sudo tailscale up
   ```

### IP Address Changes

Tailscale IPs can change. To update:

```bash
# Re-run the Tailscale setup
./tailscale-setup.sh

# Or manually update
./setup.sh
```

## Security Considerations

- Tailscale provides end-to-end encryption for all traffic
- Access is controlled by your Tailscale admin console
- Consider using Tailscale ACLs for fine-grained access control
- Regularly review connected devices in the admin console

## Advanced Configuration

### Custom ACLs

Configure access control lists in your Tailscale admin console to restrict which devices can communicate.

### Exit Nodes

Use Tailscale exit nodes to route internet traffic through specific devices:

```bash
sudo tailscale up --exit-node=100.64.1.1
```

### MagicDNS

Enable MagicDNS in your Tailscale settings to use hostnames instead of IP addresses:

```python
# Instead of IP addresses, use hostnames
client.make_request('my-server', 8080, '/api/status')
```

## Support

- Tailscale Documentation: https://tailscale.com/kb/
- Admin Console: https://login.tailscale.com/admin/
- Community: https://tailscale.com/contact/support/ 