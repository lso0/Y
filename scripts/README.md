# Scripts Directory

This directory contains the internal scripts used by the RC Automation containerized system.

## 📁 Script Organization

### Main Entry Point (Root Directory)
- **`../run.sh`** - Main user interface script (cross-platform wrapper)
  - Provides simple commands like `./run.sh setup`, `./run.sh run`
  - Handles OS detection and Docker management
  - References the scripts in this directory

### Internal Scripts (This Directory)
- **`docker-entrypoint.sh`** - Container entrypoint script
  - Handles setup logic inside the Docker container
  - Manages Infisical authentication and secret fetching
  - Provides containerized commands: setup, run, shell, help

- **`setup.sh`** - Legacy setup script (for reference)
  - Original host-based setup logic
  - Fixed OS-specific issues but now containerized approach is preferred
  - Kept for backwards compatibility

- **`system-check.sh`** - Comprehensive system prerequisites checker
  - Checks Docker installation and status
  - Verifies network connectivity
  - Validates environment setup
  - Provides detailed OS-specific installation instructions

## 🚀 Usage

**For users:** Always use the main entry point:
```bash
# From project root directory
./run.sh [command]
```

**For development:** Scripts in this directory are called internally:
```bash
# These are called automatically by run.sh
./scripts/system-check.sh      # System prerequisites check
./scripts/docker-entrypoint.sh # Container entrypoint (used in Docker)
./scripts/setup.sh             # Legacy setup (reference only)
```

## 🔧 File Permissions

All scripts maintain their executable permissions:
```bash
-rwxr-xr-x docker-entrypoint.sh
-rwxr-xr-x setup.sh
-rwxr-xr-x system-check.sh
```

## 📋 Dependencies

- **docker-entrypoint.sh**: Requires Infisical CLI (installed in container)
- **system-check.sh**: Requires curl, basic system tools
- **setup.sh**: Requires Docker, curl (legacy - not used in containerized setup)

## 🔄 Integration

These scripts are integrated into the build process:
- **Dockerfile** references `scripts/docker-entrypoint.sh`
- **run.sh** calls `scripts/system-check.sh` for prerequisites
- All scripts copied and made executable during Docker build

---

**Note:** Users should interact with `../run.sh` rather than calling these scripts directly. 