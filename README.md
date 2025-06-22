# 🚀 RC Automation - Cross-Platform Containerized Solution

A fully containerized automation solution that works consistently across **Linux**, **macOS**, and **Windows**.

## ⚡ Quick Start

For new machines, use our one-command setup:

```bash
git clone <your-repo>
cd Y
./run.sh auto-setup
./run.sh run
```

That's it! The `auto-setup` command handles everything automatically.

## 🛠️ Main Commands

| Command | Description |
|---------|-------------|
| `./run.sh auto-setup` | **Complete setup from scratch (recommended)** |
| `./run.sh run` | Run RC automation |
| `./run.sh check` | Check system prerequisites |
| `./run.sh shell` | Open interactive shell for debugging |
| `./run.sh logs` | View container logs |
| `./run.sh help` | Show all available commands |

## 📋 Requirements

- **Docker** (auto-installed on Linux, manual on macOS/Windows)
- **4GB+ RAM** and **2GB+ disk space**
- **Internet connection** for dependencies

## 🌍 Platform Support

- **Linux**: Full automation with Docker auto-installation
- **macOS**: Guided setup with Docker Desktop  
- **Windows**: WSL2/Git Bash support with Docker Desktop

## 📚 Documentation

### **📖 For Users**
- **[Complete Setup Guide](docs/CONTAINERIZED_SETUP.md)** ⭐ **Most comprehensive**
- **[Getting Started](docs/GETTING_STARTED.md)** - Step-by-step manual setup
- **[Quick Commands](docs/ONE_COMMAND_SETUP.md)** - Auto-setup explained

### **🔧 For Developers**  
- **[Auto-Install Details](docs/AUTO_INSTALL_SUMMARY.md)** - Technical implementation
- **[Scripts Documentation](scripts/README.md)** - Script organization
- **[All Documentation](docs/README.md)** - Complete documentation index

## 🚀 Key Features

- **🌍 Cross-Platform**: Same commands work on Linux, macOS, Windows
- **🐳 Containerized**: No host dependencies except Docker
- **🤖 Auto-Installation**: One-command Docker setup on Linux
- **🔍 Smart Checks**: Comprehensive prerequisite validation
- **⚙️ CI/CD Ready**: Non-interactive automation support

## 🐛 Troubleshooting

### Quick Diagnostics
```bash
./run.sh check  # Comprehensive system check with solutions
```

### Common Issues
- **Docker not installed**: Run `./run.sh auto-setup` for automatic installation
- **Permission issues**: Log out/in after Docker installation for group changes
- **Service not running**: Start Docker Desktop or `sudo systemctl start docker`

## 📁 Project Structure

```
├── 🚀 run.sh                   # Main automation script  
├── 📂 scripts/                 # Internal scripts
├── 📂 docs/                    # Documentation
├── 🐳 docker-compose.yml       # Container orchestration
├── 🐳 Dockerfile              # Container definition
├── 📂 RC/                     # RevenueCat automation code
├── 📂 auto/                   # Additional automation tools
└── 📂 mail/                   # Email automation components
```

## 🆘 Need Help?

1. **📖 Read the docs**: [docs/README.md](docs/README.md)
2. **🔍 Run diagnostics**: `./run.sh check`
3. **🐛 Check logs**: `./run.sh logs`
4. **💻 Debug mode**: `./run.sh shell`

---

**Ready to start?** Run `./run.sh auto-setup` and you'll be up and running in minutes! 🎊 