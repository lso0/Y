# 🚀 Ubuntu Automation Server Setup Guide

This guide will help you deploy your persistent automation server on Ubuntu.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP API    ┌──────────────────────┐
│   Your MacBook  │ ──────────────► │   Ubuntu Server      │
│                 │                 │                      │
│ automation_     │                 │ ┌──────────────────┐ │
│ client.py       │                 │ │ automation_      │ │
│                 │                 │ │ server.py        │ │
└─────────────────┘                 │ │                  │ │
                                    │ │ FastAPI + Uvicorn│ │
                                    │ │ Persistent       │ │
                                    │ │ Chromium         │ │
                                    │ │ Fastmail Session │ │
                                    │ └──────────────────┘ │
                                    │                      │
                                    │ Port: 8888           │
                                    └──────────────────────┘
```

## 📦 What You Get

- **Persistent Browser**: Chromium stays running with login session
- **Auto Session Management**: Detects expiration and re-logs automatically
- **HTTP API**: Send requests from anywhere
- **Session Monitoring**: Track session health and patterns
- **Systemd Service**: Auto-restart on failure/reboot

## 🔧 Quick Setup

### 1. Connect to Your Ubuntu Server

```bash
ssh wgus1@100.124.55.82
```

### 2. Download and Run Setup Script

```bash
# Download setup script (copy from your Mac)
curl -o deploy_to_ubuntu.sh https://your-setup-script-url
# Or manually copy the script

# Make executable
chmod +x deploy_to_ubuntu.sh

# Run setup
./deploy_to_ubuntu.sh
```

### 3. Copy Server Files

```bash
# Copy these files to ~/automation_server/
cp automation_server.py ~/automation_server/
cp session_monitor.py ~/automation_server/
```

### 4. Start the Service

```bash
# Start automation server
sudo systemctl start automation-server

# Check status
sudo systemctl status automation-server

# View logs
sudo journalctl -u automation-server -f
```

## 🎮 How to Use

### From Your MacBook

```bash
# Test connection
python automation_client.py --server http://100.124.55.82:8888 status

# Create alias
python automation_client.py --server http://100.124.55.82:8888 alias nya20@fastmail.com wg0@fastmail.com --description "Test alias"

# Check session health
python automation_client.py --server http://100.124.55.82:8888 session health

# Force refresh session
python automation_client.py --server http://100.124.55.82:8888 session refresh
```

### Using curl

```bash
# Get status
curl http://100.124.55.82:8888/status

# Create alias
curl -X POST http://100.124.55.82:8888/alias/create \
  -H "Content-Type: application/json" \
  -d '{"alias_email": "nya21@fastmail.com", "target_email": "wg0@fastmail.com", "description": "API test"}'

# Check session health
curl http://100.124.55.82:8888/session/health
```

## 📊 Session Monitoring

### Monitor Session Health

```bash
# Single check
python session_monitor.py --server http://100.124.55.82:8888 --check

# Continuous monitoring (1-minute intervals)
python session_monitor.py --server http://100.124.55.82:8888 --interval 60

# Monitor for specific duration (1 hour)
python session_monitor.py --server http://100.124.55.82:8888 --duration 3600

# Analyze session patterns
python session_monitor.py --analyze
```

### Understanding Session Expiration

The monitor will help you understand:
- How long sessions typically last
- What causes session failures
- Optimal refresh intervals

## 🔍 API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/status` | GET | Server and session status |
| `/session/health` | GET | Check session health |
| `/session/refresh` | POST | Force session refresh |
| `/alias/create` | POST | Create new alias |

## 🛠️ Management Commands

```bash
# Service management
sudo systemctl start automation-server      # Start
sudo systemctl stop automation-server       # Stop
sudo systemctl restart automation-server    # Restart
sudo systemctl status automation-server     # Status

# View logs
sudo journalctl -u automation-server -f     # Follow logs
sudo journalctl -u automation-server -n 50  # Last 50 lines

# Configuration
sudo systemctl edit automation-server       # Edit service config
```

## 📈 Performance Benefits

Compared to running locally on MacBook:

- ✅ **24/7 Availability**: Server runs continuously
- ✅ **Faster Response**: No browser startup time
- ✅ **Resource Efficient**: Ubuntu server optimized for headless
- ✅ **Session Persistence**: Login once, use for hours
- ✅ **Auto Recovery**: Restarts on failures
- ✅ **Remote Access**: Use from any device

## 🔧 Customization

### Add New Automation Tasks

1. Add new endpoint to `automation_server.py`:

```python
@app.post("/email/send")
async def send_email(request: EmailRequest):
    # Your email automation logic
    pass
```

2. Add client method to `automation_client.py`:

```python
def send_email(self, to, subject, body):
    # Client implementation
    pass
```

3. Restart service:

```bash
sudo systemctl restart automation-server
```

## 🚨 Troubleshooting

### Server Won't Start

```bash
# Check logs
sudo journalctl -u automation-server -n 50

# Common issues:
# - Missing dependencies: reinstall packages
# - Port already in use: change port in automation_server.py
# - Permissions: check file ownership
```

### Session Issues

```bash
# Force refresh session
curl -X POST http://100.124.55.82:8888/session/refresh

# Check if Chromium is running
ps aux | grep chromium

# Restart service if needed
sudo systemctl restart automation-server
```

### Network Issues

```bash
# Check if port 8888 is open
sudo ufw allow 8888

# Test local connection
curl http://localhost:8888/status

# Check if service is listening
sudo netstat -tlnp | grep 8888
```

## 📝 Log Analysis

Session monitor creates `session_monitor.csv` with detailed metrics:

```bash
# View recent session data
tail -20 session_monitor.csv

# Import into spreadsheet for analysis
# Or use the built-in analyzer
python session_monitor.py --analyze
```

## 🎯 Next Steps

1. **Deploy to Ubuntu**: Follow setup steps above
2. **Test Basic Functions**: Create a few aliases
3. **Monitor Sessions**: Run 24-hour monitoring
4. **Optimize Refresh**: Based on session expiration patterns
5. **Add New Automations**: Email, calendar, etc.

## 💡 Pro Tips

- Monitor sessions for 24-48 hours to understand patterns
- Sessions typically last 2-6 hours depending on activity
- Use session refresh proactively rather than reactively
- Add firewall rules for security: `sudo ufw allow from YOUR_IP to any port 8888`
- Consider using nginx reverse proxy for HTTPS

Your automation server is now ready for enterprise-scale usage! 🚀 