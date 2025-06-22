# 🐳 Containerized RC Automation

A fully containerized solution for running RC Automation that works consistently across **Linux**, **macOS**, and **Windows**.

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** installed and running
   - Linux: [Docker Engine](https://docs.docker.com/engine/install/)
   - macOS/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **Infisical Token** (required for secret management)
   - Get your token from your Infisical dashboard
   - You'll add this to the `.env` file during setup

### First Time Setup

1. **Clone and navigate to your project:**
   ```bash
   cd /path/to/your/project
   ```

2. **Run the setup:**
   ```bash
   ./run.sh setup
   ```
   
   This will:
   - Create a `.env` template file
   - Prompt you to add your `INFISICAL_TOKEN`
   - Build the Docker image
   - Set up the containerized environment

3. **Edit your `.env` file:**
   ```bash
   # Add your Infisical token
   INFISICAL_TOKEN=your_actual_token_here
   ```

4. **Run setup again after adding your token:**
   ```bash
   ./run.sh setup
   ```

## 📖 Usage

### Basic Commands

```bash
# Run RC automation (most common usage)
./run.sh run

# Run with custom arguments
./run.sh run --some-argument value

# Open interactive shell for debugging
./run.sh shell

# View container logs
./run.sh logs

# Build/rebuild the Docker image
./run.sh build

# Clean up containers and images
./run.sh clean

# Show help
./run.sh help
```

### Advanced Usage

#### Development Mode
```bash
# Open shell for development/debugging
./run.sh shell

# Inside the shell, you can:
cd /app/RC
python rc_a.py --debug
```

#### Custom Environment Variables
Edit `.env` file to customize:
```env
# Infisical Configuration (REQUIRED)
INFISICAL_TOKEN=your_token_here

# RC Automation Variables (Optional)
RC_E_1=custom_email
RC_P_1=custom_password

# Tailscale Configuration (Optional)
TAILSCALE_IP=100.x.x.x
TAILSCALE_ENABLED=true
TAILSCALE_HOSTNAME=your-hostname
```

## 🏗️ Architecture

### What's Inside the Container

- **Python 3.12** runtime environment
- **Infisical CLI** (automatically installed for correct architecture)
- **All Python dependencies** from `RC/requirements.txt`
- **Your application code** mounted as volumes
- **Cross-platform compatibility** (Linux AMD64/ARM64)

### File Structure
```
├── run.sh                    # Cross-platform runner script
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Container definition
├── docker-entrypoint.sh     # Container entrypoint logic
├── .env                     # Environment variables (created on first run)
├── RC/                      # Your RC automation code
│   ├── rc_a.py
│   ├── requirements.txt
│   └── ...
└── config/                  # Persistent configuration storage
```

## 🔧 Platform-Specific Notes

### Linux
- Uses **host networking** by default for better Tailscale integration
- All features fully supported
- Docker runs natively

### macOS
- Uses **bridge networking** (host networking not available on macOS)
- Docker Desktop required
- All features supported through port mapping

### Windows
- Requires **WSL2** or **Git Bash** for the shell script
- Uses **bridge networking**
- Docker Desktop with WSL2 backend recommended

## 🐛 Troubleshooting

### Common Issues

#### 1. "Docker is not running"
```bash
# Solution: Start Docker Desktop
# On Linux: sudo systemctl start docker
```

#### 2. "INFISICAL_TOKEN not set"
```bash
# Solution: Edit .env file and add your token
INFISICAL_TOKEN=your_actual_token_here
```

#### 3. "Infisical authentication failed"
```bash
# Solution: Verify your token is correct
# Check your Infisical dashboard for the right token
```

#### 4. Permission denied on run.sh
```bash
# Solution: Make the script executable
chmod +x run.sh
```

#### 5. Container build fails
```bash
# Solution: Clean and rebuild
./run.sh clean
./run.sh build
```

### Debug Mode

Open an interactive shell to debug issues:
```bash
./run.sh shell

# Inside container:
cd /app
ls -la
env | grep INFISICAL
infisical --version
```

### Logs and Diagnostics

```bash
# View container logs
./run.sh logs

# Check Docker status
docker info

# Check if image was built
docker images | grep rc-automation
```

## 🔄 Migration from Original Setup

If you were using the original `setup.sh`, here's how to migrate:

### Before (Original)
```bash
./setup.sh  # Had OS-specific issues
```

### After (Containerized)
```bash
./run.sh setup  # Works on any OS
./run.sh run    # Run your automation
```

### Key Benefits
- ✅ **Cross-platform compatibility**
- ✅ **No host dependencies** (except Docker)
- ✅ **Consistent environment** across all machines
- ✅ **Easier troubleshooting** with containerized logs
- ✅ **Simplified deployment** 

## 🔐 Security Notes

- **Environment variables** are handled securely within containers
- **Secrets** are fetched from Infisical at runtime
- **No secrets** are baked into Docker images
- **Volumes** are used for persistent data only

## 🤝 Support

If you encounter issues:

1. **Check the logs:** `./run.sh logs`
2. **Try the shell:** `./run.sh shell`
3. **Clean and rebuild:** `./run.sh clean && ./run.sh setup`
4. **Verify Docker:** `docker info`

---

**Happy containerizing! 🐳** 