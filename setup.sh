#!/bin/bash
# Setup script for OpenAPI Generator

set -e

echo "OpenAPI Specification Generator - Setup"
echo "========================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package in editable mode
echo ""
echo "Installing package in editable mode..."
pip install -e .

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers (this may take a while)..."
playwright install chromium

echo ""
echo "========================================"
echo "✓ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To generate an OpenAPI spec, run:"
echo "  openapi-gen <base_url>"
echo ""
echo "For help, run:"
echo "  openapi-gen --help"
echo ""
