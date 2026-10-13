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
    
    # Try to import psutil first
    try:
        import psutil
        print_colored("✓ psutil is already installed", Colors.GREEN)
        return
    except ImportError:
        pass
    
    # Try pip --user first
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--user", "psutil"
        ], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        print_colored("✓ psutil installed via pip --user", Colors.GREEN)
        return
    except subprocess.CalledProcessError:
        pass
    
    # Try system package managers
    install_methods = [
        (["apt", "install", "-y", "python3-psutil"], "apt (Ubuntu/Debian)"),
        (["yum", "install", "-y", "python3-psutil"], "yum (CentOS/RHEL)"),
        (["dnf", "install", "-y", "python3-psutil"], "dnf (Fedora)"),
        (["pacman", "-S", "--noconfirm", "python-psutil"], "pacman (Arch Linux)")
    ]
    
    for cmd, name in install_methods:
        if shutil.which(cmd[0]):
            try:
                print_colored(f"Trying to install via {name}...", Colors.YELLOW)
                subprocess.run(["sudo"] + cmd, check=True, capture_output=True)
                print_colored(f"✓ psutil installed via {name}", Colors.GREEN)
                return
            except subprocess.CalledProcessError:
                continue
    
    # Try pipx
    if shutil.which("pipx"):
        try:
            print_colored("Trying to install via pipx...", Colors.YELLOW)
            subprocess.run(["pipx", "install", "psutil", "--include-deps"], 
                         check=True, capture_output=True)
            print_colored("✓ psutil installed via pipx", Colors.GREEN)
            return
        except subprocess.CalledProcessError:
            pass
    
    # All methods failed
    print_colored("Could not install psutil automatically", Colors.RED)
    print_colored("Please install psutil manually using one of these methods:", Colors.YELLOW)
    print_colored("  sudo apt install python3-psutil     # Ubuntu/Debian", Colors.CYAN)
    print_colored("  sudo yum install python3-psutil     # CentOS/RHEL", Colors.CYAN)
    print_colored("  sudo dnf install python3-psutil     # Fedora", Colors.CYAN)
    print_colored("  sudo pacman -S python-psutil        # Arch Linux", Colors.CYAN)
    print_colored("  pipx install psutil                 # Using pipx", Colors.CYAN)
    print_colored("  python3 -m venv venv && venv/bin/pip install psutil  # Virtual env", Colors.CYAN)
    sys.exit(1)

def setup_local_bin():
    """Setup ~/.local/bin directory"""
    local_bin = Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    print_colored("✓ ~/.local/bin directory ready", Colors.GREEN)
    return local_bin

def install_pyker():
    """Install pyker package (pip --user) providing the pyker CLI."""
    print_colored("Installing Pyker...", Colors.YELLOW)
    local_bin = setup_local_bin()

    if Path("pyproject.toml").exists() and Path("pyker").is_dir():
        cmd = [sys.executable, "-m", "pip", "install", "--user", "--upgrade", "."]
        source = "local package"
    else:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--user",
            "--upgrade",
            "git+https://github.com/mrvi0/pyker.git",
        ]
        source = "GitHub"

    try:
        subprocess.run(cmd, check=True)
        print_colored(f"✓ Pyker installed from {source}", Colors.GREEN)
    except subprocess.CalledProcessError as e:
        print_colored(f"Error installing package: {e}", Colors.RED)
        print_colored("Try: uv tool install git+https://github.com/mrvi0/pyker.git", Colors.YELLOW)
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

def setup_completions():
    """Setup shell completions"""
    print_colored("Setting up shell completions...", Colors.YELLOW)
    
    # Setup bash completion
    bash_comp_dir = Path.home() / ".local" / "share" / "bash-completion" / "completions"
    bash_comp_dir.mkdir(parents=True, exist_ok=True)
    
    bash_comp_file = Path("completions/pyker-completion.bash")
    if bash_comp_file.exists():
        shutil.copy2(bash_comp_file, bash_comp_dir / "pyker")
        print_colored("✓ Bash completion installed", Colors.GREEN)
    else:
        print_colored("⚠ Bash completion file not found (optional)", Colors.YELLOW)
    
    # Setup zsh completion if zsh is available
    if shutil.which("zsh"):
        # Determine zsh completion directory
        oh_my_zsh = Path.home() / ".oh-my-zsh"
        if oh_my_zsh.exists():
            zsh_comp_dir = oh_my_zsh / "completions"
        else:
            zsh_comp_dir = Path.home() / ".local" / "share" / "zsh" / "site-functions"
        
        zsh_comp_dir.mkdir(parents=True, exist_ok=True)
        
        zsh_comp_file = Path("completions/_pyker")
        if zsh_comp_file.exists():
            shutil.copy2(zsh_comp_file, zsh_comp_dir / "_pyker")
            print_colored("✓ Zsh completion installed", Colors.GREEN)
            
            # Add to fpath if needed (non-oh-my-zsh)
            if not oh_my_zsh.exists():
                zshrc = Path.home() / ".zshrc"
                fpath_line = f"fpath=({zsh_comp_dir} $fpath)"
                if zshrc.exists():
                    zshrc_content = zshrc.read_text()
                    if str(zsh_comp_dir) not in zshrc_content:
                        with open(zshrc, 'a') as f:
                            f.write(f"\n{fpath_line}\n")
                        print_colored("Added completion directory to ~/.zshrc", Colors.BLUE)
        else:
            print_colored("⚠ Zsh completion file not found (optional)", Colors.YELLOW)

def main():
    print_colored("Pyker - Simple Python Process Manager", Colors.BOLD + Colors.CYAN)
    print_colored("=" * 50, Colors.CYAN)
    
    check_not_root()
    check_python()
    install_psutil()
    local_bin = install_pyker()
    create_pyker_dir()
    setup_completions()
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