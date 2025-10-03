#!/bin/bash
# Docker-based MCP Server Setup
# Easiest option - just requires Docker installed

set -e

echo "=================================="
echo "OpenAPI Generator MCP (Docker)"
echo "=================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo ""
    echo "Install Docker:"
    echo "  Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi

# Check for docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: docker-compose not found, using 'docker compose' instead"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Get API key
echo "Please enter your Anthropic API key:"
echo "(Get one at: https://console.anthropic.com/)"
read -p "API Key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "Error: API key required"
    exit 1
fi

# Save to .env for docker-compose
echo "ANTHROPIC_API_KEY=$API_KEY" > .env
echo "API key saved"
echo ""

# Build and run
echo "Building Docker image..."
docker build -t openapi-generator-mcp:latest .
echo ""

echo "Starting MCP server..."
echo ""
echo "Configuration for Claude Desktop:"
echo ""

# Detect OS for config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG="~/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG="~/.config/Claude/claude_desktop_config.json"
fi

echo "Add this to: $CLAUDE_CONFIG"
echo ""
echo "{"
echo "  \"mcpServers\": {"
echo "    \"openapi-generator\": {"
echo "      \"command\": \"docker\","
echo "      \"args\": ["
echo "        \"run\","
echo "        \"--rm\","
echo "        \"-i\","
echo "        \"-e\", \"ANTHROPIC_API_KEY=$API_KEY\","
echo "        \"-v\", \"$(pwd)/output:/app/output\","
echo "        \"openapi-generator-mcp:latest\""
echo "      ]"
echo "    }"
echo "  }"
echo "}"
echo ""
echo "=================================="
echo "Docker setup complete!"
echo ""
echo "To test manually:"
echo "  docker run --rm -it -e ANTHROPIC_API_KEY=$API_KEY openapi-generator-mcp:latest"
echo ""
echo "To configure Claude Desktop:"
echo "  1. Edit: $CLAUDE_CONFIG"
echo "  2. Add the configuration shown above"
echo "  3. Restart Claude Desktop"
echo "=================================="
