# Pyker - Simple Python Process Manager

A lightweight, user-friendly alternative to PM2 for managing Python scripts. Run Python processes in the background, monitor their status, and manage logs with ease.

## ✨ Features

- 🚀 **Simple Setup** - No sudo required, works in user space
- 📊 **Process Monitoring** - Real-time CPU and memory usage
- 📝 **Automatic Logging** - Each process gets its own log file
- 🔄 **Log Rotation** - Configurable log rotation to prevent disk space issues
- 📱 **Adaptive Interface** - Responsive tables that work on any terminal size
- 🎨 **Color-coded Status** - Visual status indicators with symbols
- ⚡ **Fast Operations** - Start, stop, restart processes instantly
- 📋 **Detailed Info** - Get comprehensive process information

## 🔧 Installation

### Quick Installation (Recommended)

```bash
# Download and install
wget https://raw.githubusercontent.com/username/pyker/main/install_simple.py
sudo python3 install_simple.py
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/username/pyker.git
cd pyker

# Install dependencies
pip3 install psutil

# Make executable and install globally
sudo cp pyker.py /usr/local/bin/pyker
sudo chmod +x /usr/local/bin/pyker
```

## 🚀 Quick Start

```bash
# Start a Python script
pyker start mybot /path/to/script.py

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

### Command Options

- `start --auto-restart` - Enable automatic restart on failure
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

## 🆚 Comparison with PM2

| Feature | PM2 | Pyker |
|---------|-----|-------|
| Language | Node.js | Python |
| Installation | npm/global | pip/local |
| User permissions | Often requires sudo | User space only |
| Configuration | Complex | Simple JSON |
| Memory usage | Higher | Lightweight |
| Learning curve | Steep | Gentle |
| Python integration | Limited | Native |
| Log rotation | Built-in | Built-in |
| Web UI | Available | CLI only |
| Clustering | Yes | No |
| Auto-restart | Yes | Yes |

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by PM2 for Node.js
- Built for Python developers who need simple process management
- Thanks to the Python community for excellent libraries like `psutil`

---

**Made with ❤️ for Python developers** 