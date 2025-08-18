#!/usr/bin/env python3
"""
Simple Pyker installer - No sudo required!
Installs pyker in user space (~/.local/bin)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_colored(message, color):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def check_not_root():
    """Check that script is NOT run as root"""
    if os.geteuid() == 0:
        print_colored("Error: This script should NOT be run as root", Colors.RED)
        print_colored("Pyker works in user space and doesn't require sudo", Colors.YELLOW)
        sys.exit(1)

def check_python():
    """Check if Python 3 is available"""
    if sys.version_info < (3, 6):
        print_colored("Error: Python 3.6 or higher is required", Colors.RED)
        sys.exit(1)
    print_colored("✓ Python 3 is available", Colors.GREEN)

def install_psutil():
    """Install psutil dependency"""
    print_colored("Installing psutil dependency...", Colors.YELLOW)
    try:
        # Try to import psutil first
        import psutil
        print_colored("✓ psutil is already installed", Colors.GREEN)
        return
    except ImportError:
        pass
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--user", "psutil"
        ], check=True, capture_output=True)
        print_colored("✓ psutil installed successfully", Colors.GREEN)
    except subprocess.CalledProcessError as e:
        print_colored("Error installing psutil:", Colors.RED)
        print_colored("Please install it manually: pip install --user psutil", Colors.YELLOW)
        sys.exit(1)

def setup_local_bin():
    """Setup ~/.local/bin directory"""
    local_bin = Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    print_colored("✓ ~/.local/bin directory ready", Colors.GREEN)
    return local_bin

def install_pyker():
    """Install pyker to ~/.local/bin"""
    print_colored("Installing Pyker...", Colors.YELLOW)
    
    # Check if pyker.py exists
    if not Path("pyker.py").exists():
        print_colored("Error: pyker.py not found in current directory", Colors.RED)
        print_colored("Please run this script from the pyker directory", Colors.YELLOW)
        sys.exit(1)
    
    # Setup local bin
    local_bin = setup_local_bin()
    target_path = local_bin / "pyker"
    
    try:
        shutil.copy2("pyker.py", target_path)
        os.chmod(target_path, 0o755)
        print_colored(f"✓ pyker installed to {target_path}", Colors.GREEN)
    except Exception as e:
        print_colored(f"Error copying file: {e}", Colors.RED)
        sys.exit(1)
    
    return local_bin

def check_path(local_bin):
    """Check if ~/.local/bin is in PATH"""
    path_env = os.environ.get('PATH', '')
    local_bin_str = str(local_bin)
    
    if local_bin_str in path_env:
        print_colored("✓ ~/.local/bin is already in PATH", Colors.GREEN)
        return True
    else:
        print_colored("Warning: ~/.local/bin is not in PATH", Colors.YELLOW)
        print_colored("Add this line to your ~/.bashrc or ~/.zshrc:", Colors.CYAN)
        print_colored(f'export PATH="$HOME/.local/bin:$PATH"', Colors.BOLD)
        print_colored("Then restart your terminal or run: source ~/.bashrc", Colors.CYAN)
        return False

def create_pyker_dir():
    """Create pyker directory structure"""
    pyker_dir = Path.home() / ".pyker"
    logs_dir = pyker_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    print_colored("✓ ~/.pyker directory structure created", Colors.GREEN)

def main():
    print_colored("Pyker - Simple Python Process Manager", Colors.BOLD + Colors.CYAN)
    print_colored("=" * 50, Colors.CYAN)
    
    check_not_root()
    check_python()
    install_psutil()
    local_bin = install_pyker()
    create_pyker_dir()
    path_ok = check_path(local_bin)
    
    print()
    print_colored("🎉 Installation completed!", Colors.GREEN + Colors.BOLD)
    print()
    print_colored("Usage:", Colors.BOLD)
    print("  pyker start mybot script.py  # Start a process")
    print("  pyker list                   # List all processes")
    print("  pyker logs mybot            # Show logs")
    print("  pyker info mybot            # Process information")
    print("  pyker --help                # Show help")
    
    print()
    print_colored("Example:", Colors.BOLD)
    print("  pyker start mybot /path/to/bot.py")
    
    if not path_ok:
        print()
        print_colored("Important: Restart your terminal or update PATH manually", Colors.YELLOW)

if __name__ == "__main__":
    main() 