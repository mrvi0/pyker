#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Pyker - Simple Python Process Manager${NC}"
echo -e "${BLUE}=====================================${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Error: This script should not be run as root${NC}"
   echo -e "${YELLOW}Pyker works in user space and doesn't require sudo${NC}"
   exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is not installed. Installing...${NC}"
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python python-pip
    else
        echo -e "${RED}Could not install Python 3. Please install it manually.${NC}"
        exit 1
    fi
fi

# Check if pip is available
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${YELLOW}pip is not available. Installing...${NC}"
    if command -v apt &> /dev/null; then
        sudo apt install -y python3-pip
    else
        echo -e "${RED}Could not install pip. Please install it manually.${NC}"
        exit 1
    fi
fi

# Install psutil
echo -e "${YELLOW}Installing psutil dependency...${NC}"

# Try different installation methods for psutil
if python3 -c "import psutil" 2>/dev/null; then
    echo -e "${GREEN}✓ psutil is already installed${NC}"
elif python3 -m pip install --user psutil 2>/dev/null; then
    echo -e "${GREEN}✓ psutil installed via pip --user${NC}"
elif command -v apt &> /dev/null && sudo apt install -y python3-psutil 2>/dev/null; then
    echo -e "${GREEN}✓ psutil installed via apt${NC}"
elif command -v yum &> /dev/null && sudo yum install -y python3-psutil 2>/dev/null; then
    echo -e "${GREEN}✓ psutil installed via yum${NC}"
elif command -v dnf &> /dev/null && sudo dnf install -y python3-psutil 2>/dev/null; then
    echo -e "${GREEN}✓ psutil installed via dnf${NC}"
elif command -v pacman &> /dev/null && sudo pacman -S --noconfirm python-psutil 2>/dev/null; then
    echo -e "${GREEN}✓ psutil installed via pacman${NC}"
elif command -v pipx &> /dev/null; then
    echo -e "${YELLOW}Using pipx to install psutil...${NC}"
    pipx install psutil --include-deps
    echo -e "${GREEN}✓ psutil installed via pipx${NC}"
else
    echo -e "${RED}Could not install psutil automatically${NC}"
    echo -e "${YELLOW}Please install psutil manually using one of these methods:${NC}"
    echo -e "  ${CYAN}sudo apt install python3-psutil${NC}     # Ubuntu/Debian"
    echo -e "  ${CYAN}sudo yum install python3-psutil${NC}     # CentOS/RHEL"
    echo -e "  ${CYAN}sudo dnf install python3-psutil${NC}     # Fedora"
    echo -e "  ${CYAN}sudo pacman -S python-psutil${NC}        # Arch Linux"
    echo -e "  ${CYAN}pipx install psutil${NC}                 # Using pipx"
    echo -e "  ${CYAN}python3 -m venv venv && venv/bin/pip install psutil${NC}  # Virtual env"
    exit 1
fi

# Download pyker.py if not present
if [ ! -f "pyker.py" ]; then
    echo -e "${YELLOW}Downloading pyker.py...${NC}"
    if command -v curl &> /dev/null; then
        curl -sSL https://raw.githubusercontent.com/mrvi0/pyker/main/pyker.py -o pyker.py
    elif command -v wget &> /dev/null; then
        wget -q https://raw.githubusercontent.com/mrvi0/pyker/main/pyker.py
    else
        echo -e "${RED}Error: Neither curl nor wget is available${NC}"
        echo -e "${YELLOW}Please download pyker.py manually and run this script again${NC}"
        exit 1
    fi
fi

# Make pyker.py executable
chmod +x pyker.py

# Create local bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Copy pyker to local bin
cp pyker.py ~/.local/bin/pyker

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}Adding ~/.local/bin to PATH...${NC}"
    
    # Add to bashrc if it exists
    if [ -f ~/.bashrc ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
    
    # Add to zshrc if it exists
    if [ -f ~/.zshrc ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    fi
    
    # Add to profile as fallback
    if [ -f ~/.profile ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.profile
    fi
    
    echo -e "${BLUE}PATH updated. Please run: source ~/.bashrc${NC}"
    echo -e "${BLUE}Or start a new terminal session${NC}"
fi

# Create pyker directory
mkdir -p ~/.pyker/logs

# Install bash completion
echo -e "${YELLOW}Setting up bash completion...${NC}"
mkdir -p ~/.local/share/bash-completion/completions

# Download completion script if not present
if [ ! -f "completions/pyker-completion.bash" ]; then
    echo -e "${YELLOW}Downloading bash completion...${NC}"
    mkdir -p completions
    if command -v curl &> /dev/null; then
        curl -sSL https://raw.githubusercontent.com/username/pyker/main/completions/pyker-completion.bash -o completions/pyker-completion.bash
    elif command -v wget &> /dev/null; then
        wget -q https://raw.githubusercontent.com/username/pyker/main/completions/pyker-completion.bash -O completions/pyker-completion.bash
    fi
fi

# Install bash completion
if [ -f "completions/pyker-completion.bash" ]; then
    cp completions/pyker-completion.bash ~/.local/share/bash-completion/completions/pyker
    echo -e "${GREEN}✓ Bash completion installed${NC}"
else
    echo -e "${YELLOW}⚠ Bash completion not available (optional)${NC}"
fi

# Install zsh completion if zsh is available
if command -v zsh &> /dev/null; then
    echo -e "${YELLOW}Setting up zsh completion...${NC}"
    
    # Create zsh completion directory
    if [[ -d ~/.oh-my-zsh ]]; then
        # Oh My Zsh
        ZSH_COMP_DIR=~/.oh-my-zsh/completions
    else
        # Standard zsh
        ZSH_COMP_DIR=~/.local/share/zsh/site-functions
    fi
    
    mkdir -p "$ZSH_COMP_DIR"
    
    # Download zsh completion if not present
    if [ ! -f "completions/_pyker" ]; then
        echo -e "${YELLOW}Downloading zsh completion...${NC}"
        mkdir -p completions
        if command -v curl &> /dev/null; then
            curl -sSL https://raw.githubusercontent.com/username/pyker/main/completions/_pyker -o completions/_pyker
        elif command -v wget &> /dev/null; then
            wget -q https://raw.githubusercontent.com/username/pyker/main/completions/_pyker -O completions/_pyker
        fi
    fi
    
    # Install zsh completion
    if [ -f "completions/_pyker" ]; then
        cp completions/_pyker "$ZSH_COMP_DIR/_pyker"
        echo -e "${GREEN}✓ Zsh completion installed${NC}"
        
        # Add to fpath if needed
        if [[ ! -d ~/.oh-my-zsh ]] && ! grep -q "fpath=.*$ZSH_COMP_DIR" ~/.zshrc 2>/dev/null; then
            echo "fpath=(~/.local/share/zsh/site-functions \$fpath)" >> ~/.zshrc
            echo -e "${BLUE}Added completion directory to ~/.zshrc${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Zsh completion not available (optional)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✓ Pyker installed successfully!${NC}"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo -e "  pyker start mybot script.py    # Start a process"
echo -e "  pyker list                     # List all processes"
echo -e "  pyker logs mybot              # View logs"
echo -e "  pyker info mybot              # Process information"
echo -e "  pyker --help                  # Show help"
echo ""
echo -e "${YELLOW}Note: If 'pyker' command is not found, restart your terminal${NC}"
echo -e "${YELLOW}or run: export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}" 