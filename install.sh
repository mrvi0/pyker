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
python3 -m pip install --user psutil

# Download pyker.py if not present
if [ ! -f "pyker.py" ]; then
    echo -e "${YELLOW}Downloading pyker.py...${NC}"
    if command -v curl &> /dev/null; then
        curl -sSL https://raw.githubusercontent.com/username/pyker/main/pyker.py -o pyker.py
    elif command -v wget &> /dev/null; then
        wget -q https://raw.githubusercontent.com/username/pyker/main/pyker.py
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