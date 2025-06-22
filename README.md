# 🚀 RC Automation - Cross-Platform Setup

A fully containerized automation solution that works consistently across **Linux**, **macOS**, and **Windows**.

## ⚡ Quick Start (New Machines)

For new machines, use our one-command setup:

```bash
git clone <your-repo>
cd Y
./run.sh auto-setup
./run.sh run
```

That's it! The `auto-setup` command will:
- ✅ Check system prerequisites automatically
- ✅ Auto-install Docker (Linux only, with prompts)
- ✅ Start Docker service if needed
- ✅ Build the containerized environment
- ✅ Complete the full setup process

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `./run.sh auto-setup` | **Complete setup from scratch (recommended for new machines)** |
| `./run.sh check` | Check system prerequisites |
| `./run.sh install-docker` | Auto-install Docker (Linux only) |
| `./run.sh setup` | Initial setup and build |
| `./run.sh run` | Run RC automation |
| `./run.sh shell` | Open interactive shell for debugging |
| `./run.sh logs` | View container logs |
| `./run.sh clean` | Clean up containers and images |
| `./run.sh help` | Show help information |

## 📋 System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2/Git Bash)
- **Docker**: Will be auto-installed on Linux, manual installation required for macOS/Windows
- **Memory**: At least 4GB RAM recommended
- **Disk Space**: 2GB+ free space for Docker images
- **Network**: Internet connection for downloading dependencies

## 🤖 Automated Setup (CI/CD)

For fully automated setups without prompts:

```bash
export AUTO_INSTALL_DOCKER=true
export AUTO_START_DOCKER=true
./run.sh auto-setup
./run.sh run
```

## 🔧 Manual Setup (Advanced Users)

If you prefer step-by-step control:

```bash
./run.sh check          # Check system prerequisites
./run.sh install-docker # Auto-install Docker (Linux only)
./run.sh setup          # Initial setup and build
./run.sh run            # Run automation
```

## 🌍 Cross-Platform Support

### Linux (Recommended)
- ✅ Full automation with Docker auto-installation
- ✅ Supports Ubuntu, Debian, Kali, Fedora, CentOS, Arch
- ✅ Intelligent distribution detection with fallbacks

### macOS
- ✅ Guided Docker Desktop installation
- ✅ Complete setup automation after Docker installation

### Windows
- ✅ WSL2/Git Bash support
- ✅ Guided Docker Desktop installation
- ✅ Complete setup automation after Docker installation

## 🐛 Troubleshooting

### Docker Issues
- **Docker not installed**: Run `./run.sh auto-setup` for automatic installation (Linux)
- **Docker not running**: Start Docker Desktop or run `sudo systemctl start docker` on Linux
- **Permission issues**: Log out and back in after installation for group changes

### Quick Diagnostics
```bash
./run.sh check  # Comprehensive system check with solutions
```

## 📚 Documentation

- [`GETTING_STARTED.md`](GETTING_STARTED.md) - Detailed setup guide
- [`AUTO_INSTALL_SUMMARY.md`](AUTO_INSTALL_SUMMARY.md) - Auto-installation features
- [`ONE_COMMAND_SETUP.md`](ONE_COMMAND_SETUP.md) - Complete solution overview
- [`CONTAINERIZED_SETUP.md`](CONTAINERIZED_SETUP.md) - Docker architecture details

## 🎉 What's New

- **🚀 One-Command Setup**: Complete automation from scratch
- **🐳 Auto Docker Installation**: Intelligent installation across Linux distributions
- **🔍 Smart System Checks**: Comprehensive prerequisite validation
- **🌍 Cross-Platform**: Same commands work everywhere
- **🤖 CI/CD Ready**: Non-interactive automation support

## 📁 Project Structure

```
├── run.sh                    # Main automation script
├── system-check.sh          # System prerequisites checker
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Container definition
├── RC/                     # RevenueCat automation code
├── auto/                   # Additional automation tools
├── mail/                   # Email automation components
└── docs/                   # Documentation files
```

## 🆘 Need Help?

1. **Run system check**: `./run.sh check`
2. **View help**: `./run.sh help`
3. **Check logs**: `./run.sh logs`
4. **Open debug shell**: `./run.sh shell`

---

**Ready to get started?** Run `./run.sh auto-setup` and you'll be up and running in minutes! 🎊 