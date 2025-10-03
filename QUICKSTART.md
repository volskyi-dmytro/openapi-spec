# Quick Start Guide

Get up and running in 5 minutes!

##  Super Quick Start (ONE COMMAND)

**Want to use with Claude Desktop? Just run:**

**Mac/Linux:**
```bash
./install_mcp.sh
```

**Windows:**
```cmd
install_mcp.bat
```

**Done!** See **[INSTALL.md](INSTALL.md)** for details.

---

## Command Line Usage

## Prerequisites

- Python 3.11 or higher
- 500MB disk space
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Installation (2 minutes)

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd openapi-spec-generator

# Run automated setup
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Configuration (30 seconds)

### For Local Development

```bash
# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=your_key_here
EOF
```

### For GitHub Actions

Add `ANTHROPIC_API_KEY` to your repository secrets:
- Go to Settings -> Secrets and variables -> Actions
- Click "New repository secret"
- Name: `ANTHROPIC_API_KEY`
- Value: Your Anthropic API key

## Your First Generation (2 minutes)

### Test with JSONPlaceholder (Simple API)

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Set your API key (if not in .env)
export ANTHROPIC_API_KEY=sk-ant-...

# Generate OpenAPI spec
openapi-gen https://jsonplaceholder.typicode.com
```

Expected output:
```
 Found 8 documentation pages
 Extracted content from 8 pages
 Processed 8 pages with LLM
 Extracted 10 endpoints
 Quality Score: 78.5%
 Specification written to: output/jsonplaceholder_typicode_com.openapi.json

Success! Generated OpenAPI spec with 10 paths
```

### View the Generated Spec

```bash
# Pretty print JSON
cat output/jsonplaceholder_typicode_com.openapi.json | jq

# Open in Swagger Editor (paste content)
# https://editor.swagger.io/
```

## Next Steps

### Try Different APIs

```bash
# Simple REST API
openapi-gen https://restcountries.com

# Larger API with more endpoints
openapi-gen https://pokeapi.co

# Save to custom location
openapi-gen https://api.example.com -o my-api-spec.json

# Generate YAML instead of JSON
openapi-gen https://api.example.com -f yaml
```

### Run the Demo Script

```bash
# Interactive demo with detailed output
python demo.py https://jsonplaceholder.typicode.com
```

### Test Multiple APIs

```bash
# Test a simple API
python test_api.py jsonplaceholder

# Test multiple APIs
python test_api.py jsonplaceholder restcountries pokeapi

# See all available test APIs
python test_api.py
```

### Run Unit Tests

```bash
# Run tests (no API key needed)
pytest tests/unit/ -v

# With coverage report
pytest tests/unit/ --cov=openapi_generator
```

### Integrate with Claude Desktop (MCP) 

Use the OpenAPI Generator directly from Claude Desktop!

```bash
# 1. Make sure dependencies are installed
pip install -r requirements.txt

# 2. Test the MCP server
python mcp_server.py
# (Press Ctrl+C to stop)

# 3. Add to Claude Desktop config
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
# Add:
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-key"
      }
    }
  }
}

# 4. Restart Claude Desktop

# 5. Ask Claude:
# "Generate an OpenAPI spec for https://catfact.ninja"
```

**Full guide:** See [MCP_SETUP.md](MCP_SETUP.md) for detailed setup instructions.

## Common Commands

```bash
# Activate environment
source venv/bin/activate

# Generate spec
openapi-gen <url>

# Generate with options
openapi-gen <url> -o output.json -f yaml

# Run demo
python demo.py <url>

# Run tests
python test_api.py <api_name>

# Check help
openapi-gen --help
```

## Directory Structure After First Run

```
openapi-spec-generator/
├── venv/                    # Virtual environment
├── output/                  # Generated OpenAPI specs
│   └── *.openapi.json      # Your generated specs
├── openapi_generator/       # Source code
├── tests/                   # Test suite
├── demo.py                  # Demo script
└── test_api.py             # API test suite
```

## Troubleshooting

### "ModuleNotFoundError"

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall if needed
pip install -e .
```

### "ANTHROPIC_API_KEY not set"

```bash
# Set environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Or create .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### "No documentation pages found"

```bash
# Try with debug logging
LOG_LEVEL=DEBUG openapi-gen <url>

# Try a different API
openapi-gen https://jsonplaceholder.typicode.com
```

### "playwright: command not found"

```bash
# Install Playwright browsers
playwright install chromium
playwright install-deps  # If on Linux
```

## What's Next?

1. **Integrate with Claude Desktop** - See [MCP_SETUP.md](MCP_SETUP.md) for MCP integration
2. **Read the full README** for architecture details
3. **Check TESTING.md** for comprehensive testing guide
4. **Try more APIs** from the test suite
5. **Customize configuration** in .env
6. **Explore the code** in `openapi_generator/`

## Getting Help

-  Read: [README.md](README.md) for full documentation
-  MCP Setup: [MCP_SETUP.md](MCP_SETUP.md) for Claude Desktop integration
-  Testing: [TESTING.md](TESTING.md) for testing guide
-  Examples: [EXAMPLES.md](EXAMPLES.md) for usage examples
-  Issues: [GitHub Issues](https://github.com/yourusername/repo/issues)

## Success Metrics

After your first generation, you should see:

 Valid OpenAPI 3.0 specification
 60%+ quality score
 Multiple endpoints extracted
 Parameters and responses defined
 No validation errors

Congratulations! You're ready to generate OpenAPI specs from any API documentation! 
