#  Easy Installation for Non-Technical Users

This guide will help you install the OpenAPI Generator MCP server for Claude Desktop **in 5 minutes** with **ONE command**.

No programming knowledge required! Just copy, paste, and run.

---

## Choose Your Installation Method

Pick the easiest option for you:

###  **Option 1: Automated Installer** (Recommended - 5 minutes)
-  Easiest - just run one command
-  Auto-installs everything
-  Auto-configures Claude Desktop
-  Requires Python 3.11+ installed

###  **Option 2: Docker** (Alternative - 10 minutes)
-  No Python needed
-  Completely isolated
-  Requires Docker installed
-  Slightly more configuration

---

## Option 1: Automated Installer (Recommended)

### For Mac/Linux Users

**Step 1:** Open Terminal

**Step 2:** Navigate to the project folder:
```bash
cd /path/to/openapi-spec
```

**Step 3:** Run the installer:
```bash
./install_mcp.sh
```

**Step 4:** Enter your Anthropic API key when prompted
- Get your key here: https://console.anthropic.com/
- It looks like: `sk-ant-...`

**Step 5:** Restart Claude Desktop (completely quit and reopen)

**Done!** 

### For Windows Users

**Step 1:** Open Command Prompt or PowerShell

**Step 2:** Navigate to the project folder:
```cmd
cd C:\path\to\openapi-spec
```

**Step 3:** Run the installer:
```cmd
install_mcp.bat
```

**Step 4:** Enter your Anthropic API key when prompted
- Get your key here: https://console.anthropic.com/
- It looks like: `sk-ant-...`

**Step 5:** Restart Claude Desktop (completely quit and reopen)

**Done!** 

---

## Option 2: Docker Installation

### Prerequisites
- Docker installed ([Download here](https://www.docker.com/products/docker-desktop))

### Installation Steps

**Step 1:** Open Terminal (Mac/Linux) or Command Prompt (Windows)

**Step 2:** Navigate to the project folder:
```bash
cd /path/to/openapi-spec
```

**Step 3:** Run the Docker setup:
```bash
./docker_mcp.sh
```
(On Windows, you may need to run this in Git Bash or WSL)

**Step 4:** Follow the on-screen instructions to configure Claude Desktop

**Step 5:** Restart Claude Desktop

**Done!** 

---

## How to Verify It's Working

After installation and restarting Claude Desktop:

1. Open Claude Desktop
2. Look for a **tools icon** ( or hammer) in the interface
3. Start a new conversation
4. Try this: **"Generate an OpenAPI spec for https://catfact.ninja"**

If Claude uses a tool called `generate_openapi_spec`, **it's working!** 

---

## What Can You Do With This?

Once installed, you can ask Claude to:

### Generate API Specifications
```
Generate an OpenAPI spec for https://api.stripe.com
```

### Validate Specifications
```
Here's my OpenAPI spec: {paste spec}
Can you validate it for me?
```

### Analyze Quality
```
Analyze the quality and coverage of this OpenAPI spec: {paste spec}
```

### List Test APIs
```
What test APIs can I try?
```

---

## Troubleshooting

### "Python not found" (Option 1)

**Problem:** Python 3.11+ is not installed

**Solution:**
- **Mac:** Install with Homebrew: `brew install python@3.11`
- **Windows:** Download from https://www.python.org/downloads/
- **Linux:** Use your package manager: `sudo apt install python3.11`

### "Docker not found" (Option 2)

**Problem:** Docker is not installed

**Solution:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop
- Try again

### "Tools not showing up in Claude Desktop"

**Problem:** Claude Desktop doesn't show the MCP tools

**Solutions:**
1. Make sure you **completely quit** Claude Desktop (not just close the window)
2. Check the configuration file was created:
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`
3. Verify your API key is correct (starts with `sk-ant-`)
4. Try restarting your computer

### "API key not working"

**Problem:** Anthropic API key is invalid

**Solution:**
1. Go to https://console.anthropic.com/
2. Create a new API key
3. Run the installer again with the new key

### Still Having Issues?

See the detailed troubleshooting guide in [MCP_SETUP.md](MCP_SETUP.md#troubleshooting)

---

## Configuration Files

After installation, these files are created/modified:

### Mac
- Config: `~/Library/Application Support/Claude/claude_desktop_config.json`
- API Key: `.env` in the project folder

### Windows
- Config: `%APPDATA%\Claude\claude_desktop_config.json`
- API Key: `.env` in the project folder

### Linux
- Config: `~/.config/Claude/claude_desktop_config.json`
- API Key: `.env` in the project folder

---

## Uninstalling

### Option 1 (Automated Installer)
1. Open the Claude Desktop config file (see locations above)
2. Remove the `"openapi-generator"` section
3. Restart Claude Desktop
4. Delete the project folder

### Option 2 (Docker)
1. Remove the configuration from Claude Desktop config file
2. Restart Claude Desktop
3. Remove Docker image: `docker rmi openapi-generator-mcp:latest`
4. Delete the project folder

---

## Security Notes

- Your API key is stored in `.env` file (keep it private)
- Never share your API key with anyone
- Never commit `.env` to version control (already in `.gitignore`)
- The MCP server only runs when Claude Desktop needs it

---

## What Happens During Installation?

The automated installer does the following:

1.  Checks for Python 3.11+
2.  Creates a virtual environment
3.  Installs all dependencies
4.  Installs Playwright browsers
5.  Saves your API key securely
6.  Configures Claude Desktop automatically
7.  Tests the installation

**Total time:** ~5 minutes (depending on internet speed)

---

## Getting Help

If you're stuck:

1. Read the [Troubleshooting](#troubleshooting) section above
2. Check [MCP_SETUP.md](MCP_SETUP.md) for detailed setup
3. See [QUICKSTART.md](QUICKSTART.md) for usage examples
4. Open an issue on GitHub with:
   - Your operating system
   - The error message
   - What you tried

---

## Success Checklist

After installation, you should have:

-  Claude Desktop restarted
-  Tools icon () visible in Claude Desktop
-  Can ask Claude to generate OpenAPI specs
-  Claude responds using the MCP tools
-  Generated specs appear in `output/` folder

**If all checked, you're ready to go!** 

---

## What's Next?

1. **Try it out** - Ask Claude to generate a spec for your favorite API
2. **Read examples** - See [EXAMPLES.md](EXAMPLES.md) for more usage patterns
3. **Explore features** - Try validation, analysis, and other tools
4. **Share feedback** - Let us know how it works for you!

---

**Happy API spec generating!** 

For advanced users and detailed documentation, see [MCP_SETUP.md](MCP_SETUP.md).
