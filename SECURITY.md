# Security Policy

**OpenAPI Specification Generator - Security Best Practices**

---

## Table of Contents

- [Reporting Security Issues](#reporting-security-issues)
- [Security Best Practices](#security-best-practices)
- [API Key Security](#api-key-security)
- [Input Validation](#input-validation)
- [Network Security](#network-security)
- [Dependency Security](#dependency-security)
- [Deployment Security](#deployment-security)

---

## Reporting Security Issues

### How to Report

** DO NOT report security issues publicly!**

If you discover a security vulnerability, please email:
- **Security Team**: security@example.com
- **Maintainer**: dmytro@example.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Response Time**: We aim to respond within 48 hours.

---

## Security Best Practices

### General Principles

1. ** Keep secrets out of code**
2. ** Validate all inputs**
3. ** Use HTTPS only**
4. ** Keep dependencies updated**
5. ** Follow least privilege principle**
6. ** Enable security features by default**

---

## API Key Security

###  Critical: Never Commit API Keys

**Bad**:
```python
#  NEVER DO THIS
api_key = "sk-ant-api03-xxx"  # Hard-coded key
```

```bash
#  NEVER DO THIS
export ANTHROPIC_API_KEY=sk-ant-xxx  # In shell history
git commit -m "add api key"           # In git history
```

**Good**:
```python
#  Load from environment
from openapi_generator.config import get_settings
settings = get_settings()
api_key = settings.anthropic_api_key
```

```bash
#  Use .env file (git ignored)
echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> .env

#  Or set in environment
export ANTHROPIC_API_KEY=sk-ant-xxx
```

### API Key Management

**Development**:
```bash
# Use .env file
cp .env.example .env
# Add development key to .env (git ignored)
```

**Production**:
```bash
# Use environment variables
export ANTHROPIC_API_KEY=sk-ant-prod-xxx

# Or use secrets manager
# AWS Secrets Manager, Azure Key Vault, etc.
```

**CI/CD**:
```bash
# GitHub Actions: Use repository secrets
# Settings -> Secrets -> Actions -> New secret
# Name: ANTHROPIC_API_KEY
# Value: sk-ant-ci-xxx
```

### Rotate Keys Regularly

1. **Generate new key**: https://console.anthropic.com/settings/keys
2. **Update in all environments**
3. **Delete old key** after verification
4. **Document rotation date**

### Key Compromise Response

If API key is compromised:

1. **Immediately delete** from Anthropic console
2. **Generate new key**
3. **Update in all environments**
4. **Review usage logs** for unauthorized access
5. **Report if suspicious activity detected**

---

## Input Validation

### URL Validation

**Security Risks**:
- Server-Side Request Forgery (SSRF)
- Open redirect
- Local file inclusion

**Protection**:
```python
#  Validate URL scheme
def validate_url(url: str) -> bool:
    """Validate URL is safe to crawl."""
    parsed = urlparse(url)

    # Only allow HTTP/HTTPS
    if parsed.scheme not in ["http", "https"]:
        raise ValueError(f"Invalid scheme: {parsed.scheme}")

    # Block internal IPs
    if parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
        raise ValueError("Cannot crawl localhost")

    # Block private networks
    ip = socket.gethostbyname(parsed.hostname)
    if ip.startswith(("10.", "172.", "192.168.")):
        raise ValueError("Cannot crawl private networks")

    return True
```

**Current Implementation**:
-  URL scheme validation
-  HTTP/HTTPS only
-  Todo: IP range blocking (private networks)

### Content Validation

**Risk**: Malicious documentation pages with XSS, injection

**Protection**:
```python
#  Sanitize extracted content
from html import escape

def sanitize_content(content: str) -> str:
    """Sanitize extracted content."""
    # Remove script tags
    content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)

    # Escape HTML
    return escape(content)
```

**Current Implementation**:
-  BeautifulSoup text extraction (strips HTML)
-  Pydantic validation
-  No eval() or exec() used

---

## Network Security

### HTTPS Enforcement

```python
#  Upgrade HTTP to HTTPS
if url.startswith("http://"):
    url = url.replace("http://", "https://")
```

**Current Implementation**: CLI auto-upgrades HTTP -> HTTPS

### Certificate Verification

```python
#  Verify SSL certificates (default)
import httpx

client = httpx.AsyncClient(verify=True)  # ← Enabled by default
```

** Never Disable**: Don't use `verify=False` (man-in-the-middle risk)

### Rate Limiting & Backoff

```python
#  Respect server limits
RATE_LIMIT_DELAY = 1.0  # seconds between requests

#  Exponential backoff on errors
for attempt in range(3):
    try:
        response = await client.get(url)
        break
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

### User Agent

```python
#  Identify as bot
USER_AGENT = "OpenAPI-Generator-Bot/1.0 (Educational Project)"

#  Don't spoof as browser
# USER_AGENT = "Mozilla/5.0 ..."  # Violates ToS
```

### robots.txt Compliance

```python
#  Respect robots.txt
from openapi_generator.utils.robots import RobotsChecker

checker = RobotsChecker(base_url)
if not checker.can_fetch(url):
    logger.info(f"Skipping {url} (disallowed by robots.txt)")
    return None
```

**Current Implementation**:  Full robots.txt support

---

## Dependency Security

### Keep Dependencies Updated

```bash
# Check for vulnerabilities
pip install safety
safety check

# Check for outdated packages
pip list --outdated
```

### Automated Scanning

**GitHub Actions** (see `.github/workflows/ci.yml`):
```yaml
- name: Security scan
  run: |
    pip install safety bandit
    safety check --json
    bandit -r openapi_generator/ -f json
```

### Vulnerability Response

1. **Monitor security advisories**
   - GitHub Dependabot
   - PyUp
   - Snyk

2. **Update immediately** for critical vulnerabilities
3. **Test after updates**
4. **Document in CHANGELOG**

### Pinning Dependencies

**Development**:
```txt
# requirements.txt - Allow minor updates
anthropic>=0.39.0,<1.0.0
pydantic>=2.9.0,<3.0.0
```

**Production**:
```txt
# requirements.lock - Exact versions
anthropic==0.39.0
pydantic==2.9.0
```

---

## Deployment Security

### Environment Separation

**Development**:
```bash
ANTHROPIC_API_KEY=sk-ant-dev-xxx
LOG_LEVEL=DEBUG
ENABLE_HTTP_CACHE=true
```

**Production**:
```bash
ANTHROPIC_API_KEY=sk-ant-prod-xxx  # Different key!
LOG_LEVEL=WARNING
ENABLE_HTTP_CACHE=true
```

### Secrets Management

**AWS**:
```python
import boto3

def get_api_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='anthropic-api-key')
    return response['SecretString']
```

**Azure**:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_api_key():
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)
    return client.get_secret("anthropic-api-key").value
```

**Docker**:
```dockerfile
# Use build args (not ENV for secrets)
ARG ANTHROPIC_API_KEY
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Or use Docker secrets
docker run -e ANTHROPIC_API_KEY_FILE=/run/secrets/api_key ...
```

### File Permissions

```bash
# Restrict .env file access
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (read/write for owner only)
```

### Logging Security

** Never log sensitive data**:

```python
#  Bad
logger.info(f"Using API key: {api_key}")

#  Good
logger.info("Using API key: [REDACTED]")

#  Good
logger.debug(f"Using API key: {api_key[:10]}...")
```

**Current Implementation**:
-  API keys never logged
-  Sensitive fields masked
-  Debug mode warnings

---

## MCP Security

### Claude Desktop Config

**Secure config**:
```json
{
  "mcpServers": {
    "openapi-generator": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-xxx"
      }
    }
  }
}
```

**Security notes**:
-  Absolute paths (no shell injection)
-  API key in env (not args)
-  Config file has user-only permissions

### MCP Input Validation

All MCP tool inputs are validated:

```python
@mcp.tool
async def generate_openapi_spec(
    base_url: str,  # ← Type validated by FastMCP
    output_format: str = "json",  # ← Limited to ["json", "yaml"]
    max_pages: Optional[int] = None,  # ← Validated range
):
    # Additional validation
    if max_pages and max_pages > 1000:
        raise ValueError("max_pages too high (max: 1000)")
```

---

## Security Checklist

### Before Deployment

- [ ] All API keys in environment variables (not code)
- [ ] `.env` file in `.gitignore`
- [ ] SSL certificate verification enabled
- [ ] Input validation on all user inputs
- [ ] Dependencies scanned for vulnerabilities
- [ ] Security tests passing
- [ ] Logs don't contain secrets
- [ ] Error messages don't leak internals
- [ ] Rate limiting configured
- [ ] robots.txt respected

### Production Hardening

- [ ] Separate prod/dev API keys
- [ ] Secrets manager integrated
- [ ] HTTPS enforced
- [ ] File permissions restricted
- [ ] Monitoring enabled
- [ ] Alerts configured
- [ ] Backup & recovery tested
- [ ] Incident response plan documented

---

## Security Features

### Built-in Security Features

 **Implemented**:
- Environment-based configuration
- HTTPS enforcement
- SSL certificate verification
- robots.txt compliance
- Input validation (Pydantic)
- No eval/exec usage
- Dependency scanning (CI/CD)
- Rate limiting
- User-agent identification

 **Todo** (Future enhancements):
- SSRF protection (private IP blocking)
- Content Security Policy headers
- Audit logging
- Secrets encryption at rest

---

## Incident Response

### If Security Breach Suspected

1. **Immediate Actions**:
   - Rotate all API keys
   - Review access logs
   - Disable compromised accounts
   - Document timeline

2. **Investigation**:
   - Identify attack vector
   - Assess damage scope
   - Check for data exfiltration
   - Preserve evidence

3. **Remediation**:
   - Apply security patches
   - Update vulnerable code
   - Enhance monitoring
   - Test fixes

4. **Communication**:
   - Notify affected users
   - Publish security advisory
   - Submit CVE if applicable
   - Update documentation

---

## Compliance

### Data Privacy

**What data is collected**:
-  No user data stored
-  No PII collected
-  Only API documentation crawled
-  Cached data stored locally only

**GDPR/CCPA**:
- N/A (no personal data processed)
- Users responsible for their API keys

### Third-Party Services

**Anthropic Claude**:
- Documentation content sent for extraction
- See: https://www.anthropic.com/legal/privacy

**User Responsibility**:
- Don't send proprietary/confidential docs without authorization
- Check API documentation license before extraction

---

## Security Audit

### Last Audit

**Date**: 2025-10-01
**Tools Used**:
- Bandit (Python security linter)
- Safety (dependency vulnerability scanner)
- Manual code review

**Findings**: No critical issues
**Status**:  Secure

### Audit Schedule

- **Minor releases**: Automated scans (CI/CD)
- **Major releases**: Manual security review
- **Dependencies**: Weekly automated scans
- **Full audit**: Annually or on major changes

---

## Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Python Security**: https://docs.python.org/3/library/security_warnings.html
- **Anthropic Security**: https://www.anthropic.com/security
- **OpenAPI Security**: https://swagger.io/docs/specification/authentication/

---

## Contact

**Security Issues**: security@example.com
**General Questions**: dmytro@example.com
**GitHub Issues**: https://github.com/YOUR_USERNAME/openapi-spec-generator/issues

---

**Last Updated**: 2025-10-01
**Version**: 1.0
