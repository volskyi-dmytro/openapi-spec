# OpenAPI Specification Generator

Automated OpenAPI 3.0 specification generation from API documentation using LLM-powered extraction.

---

## Documentation Hub

**Quick Start**:
- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[EXAMPLES.md](EXAMPLES.md)** - Usage examples and patterns
- **[INSTALL.md](INSTALL.md)** - Detailed installation guide

**Advanced**:
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and internals
- **[TESTING.md](TESTING.md)** - Testing guide and strategies
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

**Integration**:
- **[MCP_SETUP.md](MCP_SETUP.md)** - Claude Desktop integration

**Contributing**:
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[SECURITY.md](SECURITY.md)** - Security best practices

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [MCP Integration](#mcp-integration)
- [Project Structure](#project-structure)
- [Performance](#performance)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This tool automates the generation of OpenAPI 3.0 specifications from API documentation websites that don't provide machine-readable specs. Given a base URL, the system discovers documentation pages, extracts content, analyzes it using LLM-powered extraction, and generates valid OpenAPI specifications.

### Use Cases

- **Reverse Engineering**: Generate OpenAPI specs for APIs without official specifications
- **Documentation Modernization**: Convert legacy documentation to OpenAPI format
- **API Client Generation**: Create specifications to use with code generators (Swagger Codegen, OpenAPI Generator)
- **API Testing**: Generate specs for automated testing frameworks
- **Integration Development**: Quickly understand and integrate with third-party APIs

### Why LLM-Powered Extraction?

Traditional approaches using regex patterns and CSS selectors are brittle and fail when documentation formats change. This tool uses large language models to understand documentation semantically:

- **Adaptability**: Works with diverse documentation formats without custom parsers
- **Semantic Understanding**: Extracts not just structure, but meaning (e.g., parameter optionality, data types)
- **Context-Aware**: Understands relationships between endpoints, parameters, and schemas
- **Low Maintenance**: No need to update parsers when documentation sites redesign

The system uses Claude's 200K context window and structured output capabilities (tool use) to ensure accurate, validated extraction.

---

## Features

### Core Capabilities

- **Automated Discovery**: Finds API documentation pages using heuristic-based crawling
  - Checks 31+ common documentation paths (`/api`, `/docs`, `/guide`, etc.)
  - Parses sitemaps for documentation URLs
  - Breadth-first crawl with intelligent filtering

- **Intelligent Content Extraction**: Handles both static and JavaScript-rendered pages
  - Automatic SPA detection
  - Playwright integration for dynamic content
  - Code sample extraction for schema inference

- **LLM-Powered Analysis**: Uses Claude AI with structured outputs
  - Tool-use pattern ensures valid JSON extraction
  - Pydantic validation for type safety
  - Confidence scoring for each extracted endpoint
  - Supports authentication scheme detection

- **OpenAPI 3.0.3 Generation**: Produces valid, complete specifications
  - Automatic endpoint deduplication
  - Operation ID generation
  - Schema inference from examples
  - JSON and YAML output formats

- **Quality Assurance**: Built-in validation and coverage analysis
  - OpenAPI specification validation
  - Coverage metrics (parameters, responses, examples)
  - Quality scoring
  - Detailed reporting

### Advanced Features

**1. Authentication Detection**
- Automatic detection of API authentication schemes
- Supports: API Keys, Bearer tokens, Basic auth, OAuth2, OpenID Connect
- Pattern-based and LLM-based detection
- Auto-detects header names and OAuth2 flows

**2. Natural Language Query Filtering**
```bash
# Filter endpoints by natural language query
openapi-gen https://api.stripe.com --filter "payment endpoints only"
```
- Keyword-based filtering with semantic expansion
- Relevance scoring
- Reduces spec size for targeted use cases

**3. Manual URL Override**
```bash
# Bypass discovery when you know the documentation URL
openapi-gen https://api.example.com --doc-url https://api.example.com/guide/
```
- Faster execution (skips discovery)
- Useful when auto-discovery fails
- Supports multiple documentation URLs

**4. Performance Optimizations**
- Parallel LLM processing (configurable concurrency)
- HTTP response caching (24-hour TTL)
- LLM result caching (avoid re-extraction)
- Configurable rate limiting

**5. MCP Integration (Model Context Protocol)**
- FastMCP server with 5 tools
- Claude Desktop integration
- Automated installation scripts
- Docker support

---

## Architecture

### High-Level Pipeline

```
Input: Base URL
    ↓
┌─────────────────────────────────────┐
│ 1. Documentation Discovery          │  <- Intelligent URL finding
│    - Common paths (/api, /docs)     │
│    - Sitemap.xml parsing            │
│    - Breadth-first crawling         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Content Extraction               │  <- Clean text extraction
│    - HTML parsing (BeautifulSoup)   │
│    - SPA detection -> Playwright     │
│    - Code sample extraction         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. LLM-Powered Extraction           │  <- Semantic understanding
│    - Claude with tool use           │
│    - Structured output (Pydantic)   │
│    - Map-reduce pattern             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. OpenAPI Assembly                 │  <- Spec generation
│    - Deduplicate endpoints          │
│    - Build valid OpenAPI 3.0        │
│    - Add metadata & examples        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Validation & Reporting           │  <- Quality assurance
│    - openapi-spec-validator         │
│    - Coverage metrics               │
│    - Confidence scoring             │
└─────────────────────────────────────┘
    ↓
Output: OpenAPI Spec (JSON/YAML) + Quality Report
```

### Key Design Decisions

**1. LLM-First Approach**

Instead of building format-specific parsers, we leverage LLMs for semantic understanding:
- **Adaptability**: Works with any documentation format
- **Accuracy**: Understands context and relationships
- **Maintainability**: No parser updates needed for new formats

**2. Structured Output via Tool Use**

Rather than asking LLMs to return JSON (prone to hallucination), we use Anthropic's tool use feature:
```python
tools = [{
    "name": "record_endpoint",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "method": {"enum": ["get", "post", "put", ...]},
            "parameters": [...],
            "responses": [...]
        }
    }
}]
```
This forces structured, validated output that Pydantic can verify.

**3. Map-Reduce Pattern**

Large documentation sites exceed context limits, so we:
- **Map**: Process each documentation page independently (parallel)
- **Reduce**: Merge and deduplicate results

This scales to arbitrarily large documentation sites while maintaining quality.

**4. Multi-Strategy Discovery**

Documentation discovery uses three complementary strategies:
- **URL patterns**: Strong matches (e.g., `/api/docs`)
- **Content analysis**: Keyword density and HTTP method detection
- **OpenAPI detection**: Direct spec embedding

This increases success rate from ~50% to 100% on tested APIs.

---

## Installation

### Prerequisites

- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- 500MB disk space (for Playwright browser)

### Quick Setup

```bash
# Clone repository
git clone <repo-url>
cd openapi-spec-generator

# Run automated setup
chmod +x setup.sh
./setup.sh

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Activate environment
source venv/bin/activate
```

The setup script will:
- Create virtual environment
- Install dependencies
- Install Playwright browsers
- Install package in editable mode

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

---

## Usage

### Basic Usage

```bash
# Generate OpenAPI spec from a base URL
openapi-gen https://api.example.com

# Specify output path
openapi-gen https://api.example.com -o my-spec.json

# Generate YAML instead of JSON
openapi-gen https://api.example.com -f yaml

# Skip validation (faster)
openapi-gen https://api.example.com --no-validate
```

### Advanced Usage

```bash
# Filter endpoints with natural language
openapi-gen https://api.example.com --filter "payment endpoints only"

# Manually specify documentation URL (bypasses discovery)
openapi-gen https://jsonplaceholder.typicode.com \
  --doc-url https://jsonplaceholder.typicode.com/guide/

# Multiple documentation URLs
openapi-gen https://api.example.com \
  --doc-url https://api.example.com/guide/ \
  --doc-url https://api.example.com/reference/
```

### Performance Tuning

```bash
# Increase parallel LLM calls (faster, more API usage)
MAX_CONCURRENT_LLM_CALLS=5 openapi-gen https://api.example.com

# Disable caching (for testing)
ENABLE_HTTP_CACHE=false ENABLE_LLM_CACHE=false openapi-gen https://api.example.com

# Increase crawl depth for deep documentation sites
MAX_DEPTH=5 openapi-gen https://api.example.com
```

### Example Output

```
OpenAPI Specification Generator
================================

Target: https://api.stripe.com

Found 23 documentation pages
Extracted content from 23 pages
Processed 23 pages with LLM
OpenAPI specification built

Coverage Report:
┌──────────────────────┬───────┬────────────┐
│ Metric               │ Value │ Percentage │
├──────────────────────┼───────┼────────────┤
│ Total Endpoints      │   127 │     100%   │
│ With Parameters      │    98 │    77.2%   │
│ With Request Body    │    45 │    35.4%   │
│ With Responses       │   112 │    88.2%   │
│ With Examples        │    73 │    57.5%   │
└──────────────────────┴───────┴────────────┘

Confidence Distribution:
┌────────┬────┐
│ High   │ 89 │
│ Medium │ 31 │
│ Low    │  7 │
└────────┴────┘

Overall Quality Score: 76.3%

Validation:
Specification is valid!

Output:
Specification written to: output/api_stripe_com.openapi.json
  Format: JSON
  Size: 143,291 bytes

Success!
Generated OpenAPI spec with 127 paths
```

### Configuration

Environment variables (`.env` or system environment):

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
ANTHROPIC_MODEL=claude-sonnet-4-20250514
REQUEST_TIMEOUT=60
LLM_TIMEOUT=120
MAX_CONCURRENT_REQUESTS=5
MAX_CONCURRENT_LLM_CALLS=3
RATE_LIMIT_DELAY=1.0
MAX_PAGES_PER_SITE=50
MAX_DEPTH=3
LOG_LEVEL=INFO
OUTPUT_DIR=output
USER_AGENT="OpenAPI-Generator-Bot/1.0"

# Caching
ENABLE_HTTP_CACHE=true
ENABLE_LLM_CACHE=true
CACHE_DIR=.cache
CACHE_TTL=86400

# Discovery Override
FORCE_DOC_URLS="https://example.com/guide/,https://example.com/api/"
```

For more examples, see [EXAMPLES.md](EXAMPLES.md).

---

## MCP Integration

The OpenAPI Generator is available as a Model Context Protocol (MCP) server, enabling integration with Claude Desktop and other MCP-compatible clients.

### One-Command Installation

**Mac/Linux:**
```bash
./install_mcp.sh
```

**Windows:**
```cmd
install_mcp.bat
```

The script automatically:
- Installs dependencies
- Configures Claude Desktop
- Sets up API key
- Tests the installation

### Available Tools

When integrated with Claude Desktop, you can:
- Generate OpenAPI specs from documentation URLs
- Validate existing OpenAPI specifications
- Analyze spec quality and coverage
- Save specs to files
- Get test API suggestions

### Example Usage

In Claude Desktop, simply ask:
```
Generate an OpenAPI spec for https://api.stripe.com
```

Claude will use the MCP tools automatically and return the specification with quality metrics.

For detailed setup instructions, see [MCP_SETUP.md](MCP_SETUP.md).

---

## Project Structure

```
openapi-spec-generator/
├── openapi_generator/
│   ├── models/
│   │   └── schemas.py          # Pydantic models for OpenAPI entities
│   ├── extractors/
│   │   ├── discovery.py        # Documentation page discovery
│   │   ├── content.py          # HTML content extraction
│   │   ├── renderer.py         # Playwright JS rendering
│   │   ├── llm_extractor.py    # Claude-powered extraction
│   │   └── auth_detector.py    # Authentication detection
│   ├── generators/
│   │   └── openapi_builder.py  # OpenAPI spec assembly
│   ├── validators/
│   │   ├── spec_validator.py   # OpenAPI validation
│   │   └── coverage.py         # Quality metrics
│   ├── utils/
│   │   ├── cache.py            # Caching utilities
│   │   ├── query_filter.py     # NL query filtering
│   │   ├── robots.py           # robots.txt handling
│   │   └── logger.py           # Logging utilities
│   ├── config.py               # Configuration management
│   ├── orchestrator.py         # Main pipeline coordinator
│   └── cli.py                  # Command-line interface
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── mcp_server.py               # FastMCP server
├── output/                     # Generated specs
├── setup.sh                    # Setup script
└── README.md                   # This file
```

---

## Performance

### Benchmarks

Tested on a variety of real-world APIs:

| API | Documentation Pages | Endpoints Found | Quality Score | Time |
|-----|---------------------|-----------------|---------------|------|
| JSONPlaceholder | 3 | 2 | 33.3% | ~15s |
| PokéAPI | 9 | 8 | 26.9% | ~45s |
| Stripe (sample) | 23 | 127 | 76.3% | ~3min |

Performance varies based on:
- Documentation site size
- LLM concurrency settings
- Cache hit rate
- Network latency

### Optimization Tips

1. **Enable Caching**: Reduces repeat processing by 50-90%
2. **Increase Concurrency**: `MAX_CONCURRENT_LLM_CALLS=5` for faster processing
3. **Use Manual URLs**: Bypass discovery for 10-20% faster execution
4. **Limit Pages**: Set `MAX_PAGES_PER_SITE` for very large sites

For more performance optimization strategies, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Testing guidelines
- Pull request process
- Coding standards

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone <your-fork-url>
cd openapi-spec-generator

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
black openapi_generator/
mypy openapi_generator/
```

---

## Security

For security best practices and threat model, see [SECURITY.md](SECURITY.md).

**Key Security Considerations:**
- API key protection (never commit `.env`)
- Input validation on all URLs
- Rate limiting to prevent abuse
- Robots.txt compliance
- Secure HTTP (HTTPS enforcement)

To report security vulnerabilities, please email security@example.com (do not open public issues).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) for LLM-powered extraction
- Uses [FastMCP](https://github.com/jlowin/fastmcp) for Model Context Protocol integration
- Documentation parsing with [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- JavaScript rendering via [Playwright](https://playwright.dev/)
- Validation with [openapi-spec-validator](https://github.com/p1c2u/openapi-spec-validator)

---

## Support

- **Documentation**: See [Documentation Hub](#documentation-hub)
- **Issues**: [GitHub Issues](https://github.com/yourusername/openapi-spec-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/openapi-spec-generator/discussions)

---

**Built with care for the developer community**
