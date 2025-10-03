# MCP Server Setup Guide

This guide explains how to integrate the OpenAPI Generator with Claude Desktop using the Model Context Protocol (MCP).

---

##  Choose Your Installation Method

###  **Quick Install (Recommended for Everyone)**
**Run ONE command and you're done!**
- See **[INSTALL.md](INSTALL.md)** for the simplest, non-technical setup
- Takes 5 minutes, no manual configuration needed

### ️ **Manual Setup (Advanced Users)**
Continue reading this guide for step-by-step manual configuration

###  **Docker (Isolated Environment)**
See **[INSTALL.md](INSTALL.md#option-2-docker-installation)** for Docker-based setup

---

## What is MCP?

The **Model Context Protocol (MCP)** is Anthropic's standard for connecting Claude to external tools and data sources. Think of it as "the USB-C port for AI" - it provides a uniform way to give Claude access to specialized capabilities.

Once configured, Claude Desktop will have access to these tools:
- `generate_openapi_spec` - Generate OpenAPI specs from documentation URLs
- `validate_openapi_spec` - Validate existing OpenAPI specifications
- `analyze_spec_coverage` - Analyze quality and coverage metrics
- `save_openapi_spec` - Save specs to files
- `list_test_apis` - Get a list of test APIs to try

---

## Prerequisites

Before setting up the MCP server, ensure you have:

1. **Claude Desktop** installed ([download here](https://claude.ai/download))
2. **Python 3.11+** with the OpenAPI Generator installed
3. **Anthropic API key** ([get one here](https://console.anthropic.com/))
4. The OpenAPI Generator repository cloned and set up

---

## Automated Setup (Easiest)

### Mac/Linux
```bash
./install_mcp.sh
```

### Windows
```cmd
install_mcp.bat
```

That's it! The script does everything automatically.

**For detailed instructions, see [INSTALL.md](INSTALL.md)**

---

## Manual Setup (Advanced Users - 10 minutes)

### Step 1: Install FastMCP

```bash
# Navigate to the project directory
cd openapi-spec

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies (includes fastmcp)
pip install -r requirements.txt
```

### Step 2: Test the MCP Server

Before integrating with Claude Desktop, verify the server works:

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Test the server (it should start without errors)
python mcp_server.py

# Press Ctrl+C to stop
```

### Step 3: Configure Claude Desktop

The configuration file location depends on your operating system:

#### macOS
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

#### Windows
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

#### Linux
```bash
~/.config/Claude/claude_desktop_config.json
```

### Step 4: Add the MCP Server Configuration

Edit the `claude_desktop_config.json` file (create it if it doesn't exist):

```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": [
        "/absolute/path/to/openapi-spec/mcp_server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-api-key-here"
      }
    }
  }
}
```

**Important:**
- Replace `/absolute/path/to/openapi-spec/mcp_server.py` with the actual absolute path
- Replace `sk-ant-your-api-key-here` with your actual Anthropic API key
- Use forward slashes `/` even on Windows

**Example (macOS/Linux):**
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": [
        "/home/username/Projects/openapi-spec/mcp_server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-api03-..."
      }
    }
  }
}
```

**Example (Windows):**
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": [
        "C:/Users/username/Projects/openapi-spec/mcp_server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-api03-..."
      }
    }
  }
}
```

### Step 5: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Start Claude Desktop again
3. The MCP server will automatically connect

---

## Verification

To verify the MCP server is working:

1. Open Claude Desktop
2. Look for the **tools icon** () or **hammer icon** in the UI
3. Click it to see available tools - you should see:
   - `generate_openapi_spec`
   - `validate_openapi_spec`
   - `analyze_spec_coverage`
   - `save_openapi_spec`
   - `list_test_apis`

### Test with a Simple Request

Try this in Claude Desktop:

```
Use the generate_openapi_spec tool to create an OpenAPI spec for https://catfact.ninja
```

Claude should:
1. Use the `generate_openapi_spec` tool
2. Return a result with the generated OpenAPI specification
3. Show endpoint count and quality metrics

---

## Advanced Configuration

### Using a Virtual Environment

If you're using a virtual environment, you need to use the Python interpreter from that environment:

```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "/absolute/path/to/openapi-spec/venv/bin/python",
      "args": [
        "/absolute/path/to/openapi-spec/mcp_server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### Adding Multiple MCP Servers

You can have multiple MCP servers in your config:

```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": ["/path/to/openapi-spec/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    },
    "another-server": {
      "command": "node",
      "args": ["/path/to/another-server.js"]
    }
  }
}
```

### Using Environment Variables

Instead of hardcoding the API key, you can use environment variables:

**macOS/Linux:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY=sk-ant-...
```

**Windows:**
```powershell
# Add to system environment variables
setx ANTHROPIC_API_KEY "sk-ant-..."
```

Then in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": ["/path/to/openapi-spec/mcp_server.py"]
    }
  }
}
```

---

## Troubleshooting

### "MCP server failed to start"

**Cause:** Python can't find the dependencies or the script path is wrong.

**Solution:**
1. Verify the absolute path in the config is correct
2. Test the server manually: `python /path/to/mcp_server.py`
3. Make sure all dependencies are installed: `pip install -r requirements.txt`
4. Use the virtual environment Python if applicable

### "Tools not showing up in Claude Desktop"

**Cause:** Configuration file syntax error or Claude Desktop cache.

**Solution:**
1. Validate your JSON config using [jsonlint.com](https://jsonlint.com)
2. Make sure all quotes are double quotes (`"`)
3. Check for trailing commas (not allowed in JSON)
4. Completely quit and restart Claude Desktop
5. Check the Claude Desktop logs (see below)

### "ANTHROPIC_API_KEY not set"

**Cause:** The API key environment variable isn't being passed correctly.

**Solution:**
1. Add the `env` section to your config (see examples above)
2. Make sure the API key is valid (starts with `sk-ant-`)
3. Try setting it as a system environment variable

### Checking Claude Desktop Logs

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows:**
```powershell
# Check the logs in:
# %LOCALAPPDATA%\Claude\logs\
```

**Linux:**
```bash
tail -f ~/.config/Claude/logs/mcp*.log
```

### Testing the MCP Server Manually

You can test the MCP server without Claude Desktop:

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run the server (it communicates via stdio)
python mcp_server.py

# It should wait for input - press Ctrl+C to stop
```

If it starts without errors, the server itself is working. The issue is likely in the Claude Desktop configuration.

---

## Example Usage in Claude Desktop

Once configured, you can use natural language to interact with the tools:

### Generate a Spec
```
Generate an OpenAPI specification for the JSONPlaceholder API at https://jsonplaceholder.typicode.com
```

### Validate a Spec
```
Here's an OpenAPI spec: {paste spec}
Can you validate it for me?
```

### Analyze Coverage
```
Analyze the quality and coverage of this OpenAPI spec: {paste spec}
```

### List Test APIs
```
What test APIs can I try with the OpenAPI generator?
```

### Save a Spec
```
Save this OpenAPI spec to /path/to/output.json
```

---

## How It Works

1. **Claude Desktop** launches the MCP server as a subprocess using the config
2. The **MCP server** (`mcp_server.py`) starts and waits for messages via stdio
3. When you ask Claude to use a tool, **Claude Desktop** sends a message to the MCP server
4. The **MCP server** executes the tool (e.g., generates an OpenAPI spec)
5. The **result** is sent back to Claude Desktop
6. **Claude** uses the result to formulate its response

The entire flow is **automatic** and **transparent** - you just use natural language!

---

## Security Notes

- The MCP server runs with your user permissions
- The API key in the config file should be kept secure
- Consider using environment variables instead of hardcoding secrets
- The server only has access to the tools you configure

---

## Uninstalling

To remove the MCP server from Claude Desktop:

1. Open `claude_desktop_config.json`
2. Remove the `"openapi-generator"` entry from `mcpServers`
3. Restart Claude Desktop

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Test the server manually: `python mcp_server.py`
3. Check Claude Desktop logs
4. Verify your `claude_desktop_config.json` syntax
5. Open an issue on GitHub with:
   - Your OS and Claude Desktop version
   - The error message
   - Relevant log output

---

## Additional Resources

- [FastMCP Documentation](https://gofastmcp.com)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/mcp)
- [OpenAPI Generator README](README.md)

---

**Next Steps:**
- Try generating specs for different APIs
- Experiment with the validation and analysis tools
- Check out [EXAMPLES.md](EXAMPLES.md) for more usage examples
