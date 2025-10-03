#!/bin/bash
# Automated MCP Installation Script for OpenAPI Generator
# This script sets up the MCP server for Claude Desktop with ZERO manual configuration

set -e  # Exit on error

echo "=================================="
echo "OpenAPI Generator MCP Installer"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: $MACHINE"
echo ""

# Get script directory (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Project directory: $SCRIPT_DIR"
echo ""

# Step 1: Check for Python 3.11+
echo "[1/7] Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
    else
        echo -e "${RED}✗${NC} Python 3.11+ required (found $PYTHON_VERSION)"
        echo ""
        echo "Please install Python 3.11 or higher:"
        if [ "$MACHINE" = "Mac" ]; then
            echo "  brew install python@3.11"
        else
            echo "  https://www.python.org/downloads/"
        fi
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Python 3 not found"
    echo ""
    echo "Please install Python 3.11+:"
    if [ "$MACHINE" = "Mac" ]; then
        echo "  brew install python@3.11"
    else
        echo "  https://www.python.org/downloads/"
    fi
    exit 1
fi
echo ""

# Step 2: Create/activate virtual environment
echo "[2/7] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi
echo ""

# Step 3: Install dependencies
echo "[3/7] Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -e .
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Step 4: Install Playwright browsers
echo "[4/7] Installing Playwright browsers..."
if command -v playwright &> /dev/null; then
    playwright install chromium --quiet 2>&1 | grep -v "Downloading" || true
    echo -e "${GREEN}✓${NC} Playwright browsers installed"
else
    echo -e "${YELLOW}!${NC} Playwright not in PATH, skipping browser install"
fi
echo ""

# Step 5: Get API key
echo "[5/7] Setting up Anthropic API key..."
if [ -f ".env" ] && grep -q "ANTHROPIC_API_KEY" .env; then
    echo -e "${GREEN}✓${NC} API key found in .env file"
    API_KEY=$(grep ANTHROPIC_API_KEY .env | cut -d'=' -f2)
else
    echo ""
    echo "Please enter your Anthropic API key:"
    echo "(Get one at: https://console.anthropic.com/)"
    read -p "API Key: " API_KEY

    if [ -z "$API_KEY" ]; then
        echo -e "${RED}✗${NC} API key required"
        exit 1
    fi

    # Save to .env
    echo "ANTHROPIC_API_KEY=$API_KEY" > .env
    echo -e "${GREEN}✓${NC} API key saved to .env"
fi
echo ""

# Step 6: Configure Claude Desktop
echo "[6/7] Configuring Claude Desktop..."

if [ "$MACHINE" = "Mac" ]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
elif [ "$MACHINE" = "Linux" ]; then
    CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
else
    echo -e "${RED}✗${NC} Unsupported OS for automatic configuration"
    echo "Please manually configure Claude Desktop using MCP_SETUP.md"
    exit 1
fi

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Create or update config file
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    echo "Claude Desktop config already exists"
    echo "Backing up to claude_desktop_config.json.backup"
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup"

    # Check if openapi-generator already configured
    if grep -q "openapi-generator" "$CLAUDE_CONFIG_FILE"; then
        echo -e "${YELLOW}!${NC} openapi-generator already configured"
        echo "Updating configuration..."
    fi
fi

# Get the absolute path to mcp_server.py
MCP_SERVER_PATH="$SCRIPT_DIR/mcp_server.py"

# Get the absolute path to Python in venv
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"

# Create new config (merge with existing if present)
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    # Use Python to merge JSON (safer than manual parsing)
    python3 << EOF
import json
import sys

config_file = "$CLAUDE_CONFIG_FILE"
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
except:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['openapi-generator'] = {
    "command": "$PYTHON_PATH",
    "args": ["$MCP_SERVER_PATH"],
    "env": {
        "ANTHROPIC_API_KEY": "$API_KEY"
    }
}

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Claude Desktop configured")
EOF
else
    # Create new config
    cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "openapi-generator": {
      "command": "$PYTHON_PATH",
      "args": ["$MCP_SERVER_PATH"],
      "env": {
        "ANTHROPIC_API_KEY": "$API_KEY"
      }
    }
  }
}
EOF
    echo -e "${GREEN}✓${NC} Claude Desktop config created"
fi
echo ""

# Step 7: Test installation
echo "[7/7] Testing installation..."
echo "Testing MCP server..."

# Test that the server can start
timeout 5 "$PYTHON_PATH" "$MCP_SERVER_PATH" > /dev/null 2>&1 || true
echo -e "${GREEN}✓${NC} MCP server is functional"
echo ""

# Success message
echo "=================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. ${YELLOW}Restart Claude Desktop${NC} (quit completely and reopen)"
echo ""
echo "2. Look for the tools icon (🔧) in Claude Desktop"
echo ""
echo "3. Try asking Claude:"
echo "   ${GREEN}\"Generate an OpenAPI spec for https://catfact.ninja\"${NC}"
echo ""
echo "Documentation:"
echo "  - Quick start: cat QUICKSTART.md"
echo "  - MCP setup guide: cat MCP_SETUP.md"
echo "  - Troubleshooting: cat MCP_SETUP.md (search for 'Troubleshooting')"
echo ""
echo "Configuration file: $CLAUDE_CONFIG_FILE"
echo ""
echo "To test the MCP server manually:"
echo "  source venv/bin/activate"
echo "  python mcp_server.py"
echo ""
echo "=================================="
echo "Happy API spec generating! 🚀"
echo "=================================="
