# Troubleshooting Guide

Common issues and solutions for the OpenAPI Specification Generator.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Runtime Errors](#runtime-errors)
- [API & LLM Issues](#api--llm-issues)
- [Quality & Output Issues](#quality--output-issues)
- [Performance Issues](#performance-issues)
- [MCP Integration Issues](#mcp-integration-issues)
- [Platform-Specific Issues](#platform-specific-issues)

---

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'openapi_generator'`

**Cause**: Package not installed or virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install package
pip install -e .

# Verify installation
pip list | grep openapi
```

---

### Issue: `playwright: command not found`

**Cause**: Playwright browsers not installed

**Solution**:
```bash
# Install Playwright browsers
playwright install chromium

# On Linux, may need system dependencies
playwright install-deps chromium

# Verify installation
playwright --version
```

---

### Issue: `pip install` fails with dependency conflicts

**Cause**: Incompatible package versions

**Solution**:
```bash
# Create fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
pip install -e .
```

---

## Configuration Issues

### Issue: `ValidationError: ANTHROPIC_API_KEY field required`

**Cause**: API key not set

**Solution**:
```bash
# Option 1: Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-your-key-here
EOF

# Option 2: Set environment variable
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option 3: Pass directly (not recommended)
ANTHROPIC_API_KEY=sk-ant-... openapi-gen https://api.example.com
```

**Get API Key**: https://console.anthropic.com/

---

### Issue: `.env` file not being loaded

**Cause**: File in wrong location or wrong format

**Solution**:
```bash
# Ensure .env is in project root
ls -la .env

# Check file format (should be KEY=VALUE, no quotes needed)
cat .env

# Correct format:
ANTHROPIC_API_KEY=sk-ant-api03-xxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Incorrect formats:
# ANTHROPIC_API_KEY = sk-ant-...  #  No spaces around =
# ANTHROPIC_API_KEY="sk-ant-..."  #  No quotes (unless value has spaces)
```

---

### Issue: Settings not being applied

**Cause**: Environment variables not overriding defaults

**Solution**:
```bash
# Environment variables take precedence over .env
export MAX_CONCURRENT_LLM_CALLS=5

# Verify setting
python -c "from openapi_generator.config import get_settings; print(get_settings().max_concurrent_llm_calls)"

# Check all settings
python -c "from openapi_generator.config import get_settings; import json; print(json.dumps(get_settings().model_dump(), default=str, indent=2))"
```

---

## Runtime Errors

### Issue: `No documentation pages found`

**Cause**: URL doesn't have accessible API documentation

**Solutions**:

1. **Try common doc paths manually**:
   ```bash
   # Check if these URLs work in browser
   https://api.example.com/docs
   https://api.example.com/api
   https://api.example.com/reference
   ```

2. **Enable debug logging**:
   ```bash
   LOG_LEVEL=DEBUG openapi-gen https://api.example.com
   ```

3. **Test with known-working API**:
   ```bash
   openapi-gen https://catfact.ninja
   ```

4. **Check robots.txt**:
   ```bash
   curl https://api.example.com/robots.txt
   ```

---

### Issue: `HTTPError: 403 Forbidden` or `429 Too Many Requests`

**Cause**: Server blocking or rate limiting

**Solutions**:

1. **Increase rate limit delay**:
   ```bash
   RATE_LIMIT_DELAY=3.0 openapi-gen https://api.example.com
   ```

2. **Change user agent**:
   ```bash
   USER_AGENT="Mozilla/5.0" openapi-gen https://api.example.com
   ```

3. **Reduce concurrent requests**:
   ```bash
   MAX_CONCURRENT_REQUESTS=1 openapi-gen https://api.example.com
   ```

---

### Issue: `TimeoutError: Request timed out`

**Cause**: Slow server or network issues

**Solutions**:

1. **Increase timeout**:
   ```bash
   REQUEST_TIMEOUT=120 openapi-gen https://api.example.com
   ```

2. **Check network**:
   ```bash
   curl -v https://api.example.com
   ```

3. **Try smaller page limit**:
   ```bash
   MAX_PAGES_PER_SITE=10 openapi-gen https://api.example.com
   ```

---

## API & LLM Issues

### Issue: `AnthropicError: Invalid API key`

**Cause**: Incorrect or expired API key

**Solution**:
```bash
# Check API key format (should start with sk-ant-)
echo $ANTHROPIC_API_KEY

# Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
  }'

# Get new API key at: https://console.anthropic.com/settings/keys
```

---

### Issue: `RateLimitError: Too many requests`

**Cause**: Exceeded Anthropic API rate limits

**Solutions**:

1. **Reduce concurrency**:
   ```bash
   MAX_CONCURRENT_LLM_CALLS=1 openapi-gen https://api.example.com
   ```

2. **Enable caching** (avoids re-calls):
   ```bash
   ENABLE_LLM_CACHE=true openapi-gen https://api.example.com
   ```

3. **Wait and retry**:
   ```bash
   sleep 60 && openapi-gen https://api.example.com
   ```

4. **Check rate limits**:
   - Visit: https://console.anthropic.com/settings/limits

---

### Issue: `Model not found: claude-sonnet-4`

**Cause**: Incorrect model name or unavailable model

**Solution**:
```bash
# Use correct model name
export ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Or use alternative model
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# List available models
# See: https://docs.anthropic.com/en/docs/models-overview
```

---

### Issue: LLM extraction returns empty results

**Cause**: Documentation format not recognized by LLM

**Solutions**:

1. **Check input content**:
   ```bash
   LOG_LEVEL=DEBUG openapi-gen https://api.example.com 2>&1 | grep "Extracted content"
   ```

2. **Try different documentation page**:
   ```bash
   # If auto-discovery fails, try specific page
   # (Feature request: manual page specification)
   ```

3. **Verify API documentation exists**:
   ```bash
   curl https://api.example.com/docs | grep -i "api\|endpoint\|request"
   ```

---

## Quality & Output Issues

### Issue: Low quality score (< 50%)

**Cause**: Poor documentation or incomplete extraction

**Solutions**:

1. **Review coverage report**:
   ```bash
   openapi-gen https://api.example.com | grep -A 10 "Coverage Report"
   ```

2. **Check confidence distribution**:
   - High "low confidence" entries indicate uncertain extractions

3. **Manually review spec**:
   ```bash
   cat output/api_example_com.openapi.json | jq '.paths'
   ```

4. **Try with known-good documentation**:
   ```bash
   openapi-gen https://catfact.ninja  # Should get 70%+ score
   ```

---

### Issue: Generated spec fails validation

**Cause**: Invalid OpenAPI structure

**Solutions**:

1. **Check validation errors**:
   ```bash
   openapi-gen https://api.example.com 2>&1 | grep "Validation"
   ```

2. **Validate manually**:
   ```bash
   # Install validator
   pip install openapi-spec-validator

   # Validate spec
   openapi-spec-validator output/api_example_com.openapi.json
   ```

3. **Use Swagger Editor**:
   - Go to https://editor.swagger.io/
   - Paste generated spec
   - Review validation errors

---

### Issue: Missing endpoints that exist in docs

**Cause**: Extraction incomplete or pages not discovered

**Solutions**:

1. **Increase page limit**:
   ```bash
   MAX_PAGES_PER_SITE=100 openapi-gen https://api.example.com
   ```

2. **Increase crawl depth**:
   ```bash
   MAX_DEPTH=5 openapi-gen https://api.example.com
   ```

3. **Check which pages were found**:
   ```bash
   LOG_LEVEL=DEBUG openapi-gen https://api.example.com 2>&1 | grep "Found.*documentation"
   ```

---

### Issue: Hallucinated endpoints (endpoints that don't exist)

**Cause**: LLM inferring from examples

**Identification**:
- Check `confidence: "low"` endpoints
- Review `source_url` field

**Solution**:
1. **Filter low-confidence results** (manual post-processing)
2. **Cross-reference with actual API**
3. **Report issue with example** (helps improve prompts)

---

## Performance Issues

### Issue: Generation takes too long (> 20 minutes)

**Cause**: Sequential processing or large doc site

**Solutions**:

1. **Enable parallel processing**:
   ```bash
   MAX_CONCURRENT_LLM_CALLS=5 openapi-gen https://api.example.com
   ```

2. **Enable caching**:
   ```bash
   ENABLE_HTTP_CACHE=true ENABLE_LLM_CACHE=true openapi-gen https://api.example.com
   ```

3. **Reduce page limit**:
   ```bash
   MAX_PAGES_PER_SITE=20 openapi-gen https://api.example.com
   ```

4. **Check if re-run is faster**:
   ```bash
   # Second run should be near-instant with caching
   openapi-gen https://api.example.com
   ```

---

### Issue: High memory usage

**Cause**: Large documentation pages in memory

**Solutions**:

1. **Reduce concurrent operations**:
   ```bash
   MAX_CONCURRENT_LLM_CALLS=1 openapi-gen https://api.example.com
   ```

2. **Monitor memory**:
   ```bash
   # Linux/Mac
   watch -n 1 'ps aux | grep python | grep openapi'
   ```

3. **Use smaller chunks** (feature request: chunking by size)

---

## MCP Integration Issues

### Issue: Claude Desktop doesn't show OpenAPI Generator

**Cause**: Configuration error or server not running

**Solutions**:

1. **Check config file location**:
   ```bash
   # Mac
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Windows
   type %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Validate JSON**:
   ```bash
   # Use jq to validate
   jq . ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Test MCP server manually**:
   ```bash
   # Run server to check for errors
   python mcp_server.py
   # Should run without errors (Ctrl+C to stop)
   ```

4. **Restart Claude Desktop** after config changes

5. **Check server logs** (see [MCP_SETUP.md](MCP_SETUP.md))

---

### Issue: MCP tools fail with "API key not set"

**Cause**: Environment variable not passed to MCP server

**Solution**:
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-actual-key-here"  ← Must be here!
      }
    }
  }
}
```

---

## Platform-Specific Issues

### Linux: `playwright: error while loading shared libraries`

**Solution**:
```bash
# Install system dependencies
playwright install-deps chromium

# Or manually install
sudo apt-get install libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
  libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libatspi2.0-0 \
  libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
  libgbm1 libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2
```

---

### macOS: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
```bash
# Install SSL certificates for Python
/Applications/Python\ 3.11/Install\ Certificates.command

# Or upgrade certifi
pip install --upgrade certifi
```

---

### Windows: `playwright install` fails

**Solution**:
```cmd
# Run PowerShell as Administrator
playwright install chromium

# If still fails, install manually:
# Download Chromium for Windows and set PLAYWRIGHT_BROWSERS_PATH
```

---

## Debugging Tips

### Enable Maximum Verbosity

```bash
LOG_LEVEL=DEBUG \
ANTHROPIC_LOG=debug \
openapi-gen https://api.example.com 2>&1 | tee debug.log
```

### Check Component Health

```bash
# Test discovery
python -c "import asyncio; from openapi_generator.extractors.discovery import DocumentationDiscovery; print(asyncio.run(DocumentationDiscovery('https://catfact.ninja').discover()))"

# Test LLM connection
python -c "from anthropic import Anthropic; print(Anthropic().messages.create(model='claude-sonnet-4-20250514', max_tokens=10, messages=[{'role':'user','content':'Hi'}]))"
```

### Generate Diagnostic Report

```bash
# Create diagnostic script
cat > diagnose.sh << 'EOF'
#!/bin/bash
echo "=== Python Version ==="
python --version

echo -e "\n=== Installed Packages ==="
pip list | grep -E "anthropic|pydantic|playwright|openapi"

echo -e "\n=== Environment Variables ==="
env | grep -E "ANTHROPIC|OPENAPI|LOG_LEVEL"

echo -e "\n=== Test API Key ==="
python -c "from openapi_generator.config import get_settings; s = get_settings(); print(f'API Key: {s.anthropic_api_key[:10]}...')"

echo -e "\n=== Run Tests ==="
pytest tests/unit/ -v --tb=short | tail -20
EOF

chmod +x diagnose.sh
./diagnose.sh > diagnostic_report.txt
```

---

## Getting Help

If your issue isn't covered here:

1. **Search existing issues**: https://github.com/YOUR_USERNAME/openapi-spec-generator/issues
2. **Check discussions**: https://github.com/YOUR_USERNAME/openapi-spec-generator/discussions
3. **Create new issue** with:
   - Error message
   - Steps to reproduce
   - Environment info (OS, Python version)
   - Diagnostic report output

---

## Useful Resources

- **Documentation**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **MCP Setup**: [MCP_SETUP.md](MCP_SETUP.md)
- **Testing**: [TESTING.md](TESTING.md)
- **Anthropic Docs**: https://docs.anthropic.com/
- **OpenAPI Spec**: https://spec.openapis.org/oas/v3.0.3

---

**Last Updated**: 2025-10-01
