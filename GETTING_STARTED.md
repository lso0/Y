# 🚀 Getting Started - New Machine Setup

This guide will help you set up the RC Automation on a new machine with automated OS detection and Docker checking.

## 🔧 Quick Setup for New Machines

### Option 1: One-Command Auto-Setup (Recommended)

For new machines, use the automated setup that handles everything:

```bash
git clone <your-repo-url>
cd Y  # or your project directory name
./run.sh auto-setup
```

This single command will:
- ✅ Run comprehensive system checks
- ✅ Auto-install Docker (Linux only, with prompts)
- ✅ Start Docker service if needed
- ✅ Build the containerized environment
- ✅ Complete the full setup process

### Option 2: Manual Step-by-Step Setup

If you prefer more control over the process:

#### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd Y  # or your project directory name
```

#### Step 2: Run System Check (Recommended)
Before setting up, run the comprehensive system check to verify all prerequisites:

```bash
./run.sh check
```

This will:
- ✅ Detect your operating system and architecture
- ✅ Check if Docker and Docker Compose are installed and running
- ✅ Verify network connectivity
- ✅ Check disk space availability
- ✅ Validate basic system tools (curl, git, bash)
- ✅ Check environment configuration

#### Step 3: Install Docker (if needed)
If the system check indicates Docker is missing, you have several options:

#### 🚀 Option 1: Auto-Install (Linux only)
For Linux systems, you can use the automatic installation:
```bash
./run.sh install-docker
```

This will automatically:
- Download and run the official Docker installation script
- Add your user to the docker group
- Start and enable the Docker service
- Verify the installation

**⚠️ Important:** After auto-installation, you may need to log out and back in (or restart your terminal) for the docker group changes to take effect. Until then, you might see permission errors when running `docker` commands without `sudo`.

#### 📋 Option 2: Manual Installation
Follow the OS-specific instructions provided:

#### 🐧 Linux (Ubuntu/Debian)
```bash
# Option 1: Official Docker script (recommended)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes

# Option 2: Package manager
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

#### 🍎 macOS
```bash
# Option 1: Download Docker Desktop (recommended)
# Visit: https://www.docker.com/products/docker-desktop

# Option 2: Homebrew
brew install --cask docker
# Then start Docker Desktop from Applications
```

#### 🪟 Windows
```bash
# Download Docker Desktop for Windows
# Visit: https://www.docker.com/products/docker-desktop
# Requires Windows 10/11 with WSL2

# Or use winget:
winget install Docker.DockerDesktop

# Ensure WSL2 is enabled:
wsl --install
wsl --set-default-version 2
```

#### Step 4: Run Setup
Once Docker is installed and running:

```bash
./run.sh setup
```

This enhanced setup will:
- 🔍 Automatically detect your OS and configure networking accordingly
- 🐳 Verify Docker is properly installed and running
- 📦 Build the containerized environment
- 🔐 Create configuration templates
- ✅ Test the entire setup

#### Step 5: Configure Secrets
Edit the `.env` file and add your Infisical token:

```bash
# Edit .env file
INFISICAL_TOKEN=your_actual_token_here
```

Then run setup again to fetch your secrets:
```bash
./run.sh setup
```

#### Step 6: Run the Automation
```bash
./run.sh run
```

## 🔧 After Setup (Both Options)

Once setup is complete (either via auto-setup or manual), you can run your automation:

```bash
./run.sh run
```

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `./run.sh auto-setup` | Complete setup from scratch (recommended for new machines) |
| `./run.sh check` | Check system prerequisites |
| `./run.sh install-docker` | Auto-install Docker (Linux only) |
| `./run.sh setup` | Initial setup and build |
| `./run.sh run` | Run RC automation |
| `./run.sh shell` | Open interactive shell for debugging |
| `./run.sh build` | Build/rebuild Docker image |
| `./run.sh logs` | View container logs |
| `./run.sh clean` | Clean up containers and images |
| `./run.sh help` | Show help information |

## 🤖 Automated/Non-Interactive Setup

For CI/CD pipelines or automated deployments, you can use environment variables to skip interactive prompts:

```bash
# Auto-install Docker without prompting (Linux only)
export AUTO_INSTALL_DOCKER=true

# Auto-start Docker service without prompting (Linux only)
export AUTO_START_DOCKER=true

# Run complete auto-setup (recommended for CI/CD)
./run.sh auto-setup

# Or run individual setup (these variables are automatically detected in CI environments)
./run.sh setup
```

The system automatically detects CI environments (when `CI=true`) and enables non-interactive mode.

## 🐛 Troubleshooting

### Docker Issues
If you encounter Docker-related problems:

1. **Docker not installed**: Run `./run.sh install-docker` for auto-installation (Linux only) or `./run.sh check` for manual instructions
2. **Docker not running**: Start Docker Desktop or run `sudo systemctl start docker` on Linux
3. **Permission issues on Linux**: 
   ```bash
   sudo usermod -aG docker $USER
   # Then log out and back in, or restart your terminal
   ```
4. **"Permission denied" after installation**: This is normal! The docker group changes require a logout/login or terminal restart to take effect
5. **System check shows Docker not running**: If you just installed Docker, try `sudo systemctl start docker` or restart your terminal

### Network Issues
If you have network connectivity problems:
- Check your firewall settings
- Verify you can access docker.com and github.com
- If behind a corporate proxy, configure Docker proxy settings

### Environment Issues
If setup fails with environment issues:
- Ensure you're in the correct project directory
- Verify your `.env` file has the correct `INFISICAL_TOKEN`
- Run `./run.sh check` to diagnose configuration problems

## 🔄 Migration from Old Setup

If you were using the old `setup.sh` script:

### Before (Old Method)
```bash
./setup.sh  # Had OS-specific issues, manual Docker installation required
```

### After (New Method - One Command)
```bash
./run.sh auto-setup  # Complete setup from scratch
./run.sh run         # Run automation
```

### After (New Method - Step by Step)
```bash
./run.sh check       # Check prerequisites first
./run.sh install-docker  # Auto-install Docker (Linux)
./run.sh setup       # Cross-platform setup
./run.sh run         # Run automation
```

## 📋 System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2/Git Bash)
- **Docker**: Version 20.10+ recommended
- **Docker Compose**: Version 2.0+ (included with Docker Desktop)
- **Memory**: At least 4GB RAM recommended
- **Disk Space**: 2GB+ free space for Docker images
- **Network**: Internet connection for downloading dependencies

## 🎯 What's New

The enhanced setup process provides:

- ✅ **Cross-platform compatibility** - Works on Linux, macOS, and Windows
- ✅ **Intelligent OS detection** - Automatically configures based on your system
- ✅ **Comprehensive prerequisite checking** - Verifies all requirements before setup
- ✅ **Automatic Docker installation** - One-command Docker setup on Linux
- ✅ **Interactive and non-interactive modes** - Works in CI/CD and manual setups
- ✅ **Better error messages** - Clear, actionable error messages with solutions
- ✅ **Docker health verification** - Tests Docker functionality, not just installation
- ✅ **Auto-start Docker service** - Automatically starts Docker when needed
- ✅ **Network and disk space validation** - Ensures sufficient resources
- ✅ **Automated troubleshooting guidance** - Provides OS-specific fix instructions

---

**Need help?** Run `./run.sh check` to diagnose issues or `./run.sh help` for command reference. 