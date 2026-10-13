# Pyker - Simple Python Process Manager

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)
![Dependencies](https://img.shields.io/badge/dependencies-minimal-brightgreen.svg)

A lightweight, user-friendly tool for managing Python scripts. Run Python processes in the background, monitor their status, and manage logs with ease.

## ✨ Features

- 🚀 **Simple Setup** - No sudo required, works in user space
- 📊 **Process Monitoring** - Real-time CPU and memory usage
- 📝 **Automatic Logging** - Each process gets its own log file
- 🔄 **Log Rotation** - Configurable log rotation to prevent disk space issues
- 📱 **Adaptive Interface** - Responsive tables that work on any terminal size
- 🎨 **Color-coded Status** - Visual status indicators with symbols
- ⚡ **Fast Operations** - Start, stop, restart processes instantly
- 📋 **Detailed Info** - Get comprehensive process information
- ⌨️ **Tab Completion** - Auto-complete commands and process names

## 🔧 Installation

### With uv / uvx (Recommended)

Install as a persistent user tool ([uv](https://docs.astral.sh/uv/) required):

```bash
uv tool install git+https://github.com/mrvi0/pyker.git
```

Run once without installing:

```bash
uvx --from git+https://github.com/mrvi0/pyker.git pyker list
```

Uninstall:

```bash
uv tool uninstall pyker
```

### One-Line Installation

```bash
# Download and run install script
curl -sSL https://raw.githubusercontent.com/mrvi0/pyker/main/install.sh | bash
```

Or with wget:
```bash
wget -qO- https://raw.githubusercontent.com/mrvi0/pyker/main/install.sh | bash
```

### Python Installer

```bash
# Download and run Python installer
curl -sSL https://raw.githubusercontent.com/mrvi0/pyker/main/install.py | python3
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/mrvi0/pyker.git
cd pyker

# Run installer (no sudo required!)
python3 install.py
```

### From Source

```bash
# Install psutil dependency
pip3 install --user psutil

# Copy pyker to local bin
mkdir -p ~/.local/bin
cp pyker.py ~/.local/bin/pyker
chmod +x ~/.local/bin/pyker

# Add to PATH (add this line to ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"
```

## 🚀 Quick Start

```bash
# Start a Python script
pyker start mybot /path/to/script.py

# Start with virtual environment
pyker start webapp app.py --venv ./venv

# List all processes
pyker list

# View process logs
pyker logs mybot

# Get detailed process info
pyker info mybot

# Stop a process
pyker stop mybot

# Restart a process
pyker restart mybot

# Delete a process
pyker delete mybot
```

## ⌨️ Tab Completion

Tab completion is automatically installed and works with:

- **Commands**: `pyker <TAB>` shows available commands
- **Process names**: `pyker stop <TAB>` completes with existing processes  
- **Files**: `pyker start mybot <TAB>` completes Python file paths
- **Options**: `pyker logs mybot <TAB>` shows available flags

*Restart your terminal after installation to enable completion.*

## 🐍 Virtual Environment Support

Pyker supports running scripts with virtual environments:

```bash
# Using relative path
pyker start myapp app.py --venv ./venv

# Using absolute path  
pyker start worker worker.py --venv /home/user/projects/myproject/venv

# Works with conda environments too
pyker start analyzer data.py --venv /home/user/miniconda3/envs/myenv
```

**Requirements:**
- Virtual environment must exist and be properly set up
- Pyker automatically detects Python executable in `bin/python` (Linux/macOS) or `Scripts/python.exe` (Windows)
- Environment information is saved and used during restarts

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `start <name> <script>` | Start a new process | `pyker start bot script.py` |
| `stop <name>` | Stop a running process | `pyker stop bot` |
| `restart <name>` | Restart a process | `pyker restart bot` |
| `delete <name>` | Remove process from list | `pyker delete bot` |
| `list` | Show all processes in table | `pyker list` |
| `logs <name>` | Show process logs | `pyker logs bot -f` |
| `info [name]` | Show detailed information | `pyker info bot` |
| `uninstall` | Uninstall Pyker completely | `pyker uninstall` |

### Command Options

- `start --auto-restart` - Enable automatic restart on failure
- `start --venv PATH` - Use virtual environment (e.g., `./venv`, `/path/to/venv`)
- `logs -f` - Follow logs in real-time
- `logs -n 100` - Show last 100 lines

## 📊 Process Status Display

### Full Table (Wide Terminals)
```
Process List:
┌───────────┬────────┬─────┬───────┬───────────────────┬───────────────────┬──────────────────┐
│Name       │PID     │CPU% │RAM    │Started            │Stopped            │Script            │
├───────────┼────────┼─────┼───────┼───────────────────┼───────────────────┼──────────────────┤
│✓ webserver│123456  │2.1  │45.2   │2025-08-19 09:30:15│-                  │server.py         │
│✗ worker   │-       │0.0  │0.0    │2025-08-19 09:25:10│2025-08-19 10:15:30│worker.py         │
└───────────┴────────┴─────┴───────┴───────────────────┴───────────────────┴──────────────────┘

Statistics: Total: 2 | Running: 1 | Stopped: 1
```

### Compact Table (Narrow Terminals)
```
Process List:
┌──────────────────┬──────────┬───────────────┐
│Name              │PID       │Script         │
├──────────────────┼──────────┼───────────────┤
│✓ webserver       │123456    │server.py      │
│✗ worker          │-         │worker.py      │
└──────────────────┴──────────┴───────────────┘

Total: 2 | Running: 1 | Stopped: 1
```

### Status Symbols
- ✓ (Green) - Process is running
- ✗ (Red) - Process is stopped
- ⚠ (Yellow) - Process error

## 📝 Detailed Process Information

```bash
pyker info mybot
```

Output:
```
Process Information: mybot
Status: ✓ Running
PID: 123456
Script: /home/user/scripts/bot.py
CPU Usage: 2.1%
Memory: 45.2 MB
Started: 2025-08-19 09:30:15
Log file: /home/user/.pyker/logs/mybot.log
Auto restart: No
Virtual env: /home/user/myproject/venv
Python executable: /home/user/myproject/venv/bin/python
```

## ⚙️ Configuration

Pyker uses a configuration file at `~/.pyker/config.json` for advanced settings:

```json
{
  "log_rotation": {
    "enabled": true,
    "max_size_mb": 10,
    "max_files": 5
  },
  "process_check_interval": 5,
  "auto_cleanup_stopped": false
}
```

### Configuration Options

- `log_rotation.enabled` - Enable/disable automatic log rotation
- `log_rotation.max_size_mb` - Maximum log file size before rotation (MB)
- `log_rotation.max_files` - Number of rotated log files to keep
- `process_check_interval` - Process status check interval (seconds)
- `auto_cleanup_stopped` - Automatically remove stopped processes

## 📁 File Structure

```
~/.pyker/
├── processes.json      # Process state information
├── config.json         # Configuration settings
└── logs/               # Process log files
    ├── mybot.log       # Current log
    ├── mybot.log.1     # Rotated log (newest)
    ├── mybot.log.2     # Rotated log
    └── ...
```

## 🎯 Why Pyker?

- **Python-first**: Built specifically for Python developers
- **Zero configuration**: Works out of the box with sensible defaults
- **User-friendly**: No complex setup or root permissions required
- **Lightweight**: Minimal dependencies and resource usage
- **Visual**: Beautiful tables and colored output that adapt to any terminal
- **Portable**: Runs anywhere Python runs

## 🔍 Troubleshooting

### Common Issues

**Q: Command not found after installation**
```bash
# Check if /usr/local/bin is in your PATH
echo $PATH

# Or run directly
/usr/local/bin/pyker list
```

**Q: Permission denied**
```bash
# Make sure the file is executable
sudo chmod +x /usr/local/bin/pyker
```

**Q: Process shows as stopped but still running**
```bash
# Update process status
pyker list

# Force kill if needed
kill -9 <PID>
pyker delete <name>
```

**Q: Logs are too large**
```bash
# Enable log rotation in config
nano ~/.pyker/config.json

# Or manually clean
rm ~/.pyker/logs/*.log.*
```

**Q: How to completely remove Pyker?**
```bash
# Use the built-in uninstall command
pyker uninstall

# This will:
# 1. Stop all running processes  
# 2. Remove pyker executable
# 3. Remove completion scripts
# 4. Optionally remove logs and config
```

**Q: "externally-managed-environment" error during installation**
```bash
# This happens on newer Linux systems (PEP 668)
# The installer will automatically try these solutions:

# Option 1: System package manager (recommended)
sudo apt install python3-psutil      # Ubuntu/Debian
sudo dnf install python3-psutil      # Fedora
sudo pacman -S python-psutil         # Arch Linux

# Option 2: Using pipx
pipx install psutil

# Option 3: Virtual environment
python3 -m venv venv
venv/bin/pip install psutil
# Then copy pyker to venv/bin/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for Python developers who need simple process management
- Thanks to the Python community for excellent libraries like `psutil`
- Inspired by the need for lightweight process management tools

---

**Made with ❤️ for Python developers** 