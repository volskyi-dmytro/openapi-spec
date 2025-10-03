# Usage Examples

## Example 1: Generate Spec for a Public API

```bash
# Generate OpenAPI spec for JSONPlaceholder API
openapi-gen https://jsonplaceholder.typicode.com

# Output:
#  Found 6 documentation pages
#  Extracted 10 endpoints
#  Specification written to: output/jsonplaceholder_typicode_com.openapi.json
```

## Example 2: Custom Output Location

```bash
# Save to specific path
openapi-gen https://api.github.com -o github-api-spec.json

# Save as YAML
openapi-gen https://api.github.com -o github-api-spec.yaml -f yaml
```

## Example 3: Manual URL Override (NEW!)

```bash
# Bypass discovery by specifying documentation URL directly
openapi-gen https://jsonplaceholder.typicode.com \
  --doc-url https://jsonplaceholder.typicode.com/guide/

# Multiple documentation URLs
openapi-gen https://api.example.com \
  --doc-url https://api.example.com/guide/ \
  --doc-url https://api.example.com/reference/ \
  -o api-spec.json

# Using environment variable
export FORCE_DOC_URLS="https://api.example.com/docs/,https://api.example.com/api/"
openapi-gen https://api.example.com
```

**When to use:**
- Documentation is at a non-standard path
- You want faster execution (skips discovery)
- Auto-discovery is failing
- You need precise control over which pages to process

## Example 4: Natural Language Query Filtering (NEW!)

```bash
# Filter endpoints by natural language query
openapi-gen https://api.stripe.com \
  --filter "payment and checkout endpoints only"

# Filter for specific API sections
openapi-gen https://api.github.com \
  --filter "user authentication and repository management"

# Combine with manual URL
openapi-gen https://api.example.com \
  --doc-url https://api.example.com/docs/ \
  --filter "webhook endpoints" \
  -o webhooks-only.json
```

**Benefits:**
- Focus on specific API functionality
- Reduce spec size for targeted use cases
- Faster processing (fewer endpoints to analyze)

## Example 5: Testing Mode (No Validation)

```bash
# Skip validation for faster iteration
openapi-gen https://api.example.com --no-validate
```

## Example 6: Programmatic Usage

```python
import asyncio
from openapi_generator.orchestrator import OpenAPIOrchestrator
from openapi_generator.generators.openapi_builder import OpenAPIBuilder

async def generate_spec(base_url: str):
    # Initialize orchestrator
    orchestrator = OpenAPIOrchestrator(base_url)

    # Run extraction pipeline
    results = await orchestrator.run()

    # Build OpenAPI spec
    builder = OpenAPIBuilder(base_url)
    builder.add_extraction_results(results)
    spec = builder.build()

    # Save to file
    output_path = "my-api-spec.json"
    with open(output_path, "w") as f:
        f.write(builder.to_json(spec, indent=2))

    print(f"Spec generated: {output_path}")

# Run
asyncio.run(generate_spec("https://api.example.com"))
```

## Example 7: Advanced Configuration

```python
# config.py or environment variables
import os
os.environ["ANTHROPIC_MODEL"] = "claude-sonnet-4-20250514"
os.environ["MAX_PAGES_PER_SITE"] = "100"  # Crawl more pages
os.environ["RATE_LIMIT_DELAY"] = "2.0"    # Be more conservative
os.environ["LOG_LEVEL"] = "DEBUG"         # Verbose logging

# NEW: Force specific documentation URLs
os.environ["FORCE_DOC_URLS"] = "https://api.example.com/docs/,https://api.example.com/guide/"
```

## Example 8: Validating Generated Specs

```python
from openapi_generator.validators.spec_validator import SpecValidator
import json

# Load generated spec
with open("output/my-api-spec.json") as f:
    spec_dict = json.load(f)

# Validate
validator = SpecValidator()
is_valid, errors, recommendations = validator.validate_with_recommendations(spec_dict)

if is_valid:
    print(" Spec is valid!")
else:
    print(" Validation errors:")
    for error in errors:
        print(f"  - {error}")

print("\nRecommendations:")
for rec in recommendations:
    print(f"  - {rec}")
```

## Example 9: Coverage Analysis

```python
from openapi_generator.validators.coverage import CoverageAnalyzer
from openapi_generator.models.schemas import Endpoint, HTTPMethod

# Analyze extracted endpoints
endpoints = [...]  # List of Endpoint objects

analyzer = CoverageAnalyzer()
report = analyzer.analyze(endpoints)

print(f"Total endpoints: {report.total_endpoints}")
print(f"With parameters: {report.endpoints_with_parameters} ({report.parameter_coverage:.1f}%)")
print(f"With responses: {report.endpoints_with_responses} ({report.response_coverage:.1f}%)")
print(f"Quality score: {report.quality_score:.1f}%")
```

## Example 10: Testing with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application
COPY . .
RUN pip install -e .

# Set API key
ENV ANTHROPIC_API_KEY=your_key_here

# Run generator
ENTRYPOINT ["openapi-gen"]
```

```bash
# Build and run
docker build -t openapi-gen .
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY openapi-gen https://api.example.com
```

## Testing Different API Vendors

### Stripe API
```bash
openapi-gen https://stripe.com/docs/api
```

### GitHub API
```bash
openapi-gen https://docs.github.com/en/rest
```

### Twilio API
```bash
openapi-gen https://www.twilio.com/docs/usage/api
```

### ServiceNow API
```bash
openapi-gen https://developer.servicenow.com
```

## Troubleshooting

### Issue: No documentation pages found

**Solution 1: Use manual URL override (NEW!)**
```bash
# Bypass discovery completely
openapi-gen https://api.example.com \
  --doc-url https://api.example.com/guide/

# Or use environment variable
export FORCE_DOC_URLS="https://api.example.com/docs/"
openapi-gen https://api.example.com
```

**Solution 2: Enable debug logging**
```bash
# See detailed discovery decisions
LOG_LEVEL=DEBUG openapi-gen https://api.example.com 2>&1 | grep "documentation"

# You'll see logs like:
# DEBUG - URL pattern + keyword match for /guide (keywords: 10)
# DEBUG - Page /posts does not match API documentation heuristics
```

**Solution 3: Increase crawl depth**
```bash
# Try with more crawl depth
MAX_DEPTH=5 openapi-gen https://api.example.com
```

### Issue: Spec validation fails

```bash
# Generate without validation to see the output
openapi-gen https://api.example.com --no-validate

# Then inspect the generated spec
cat output/api_example_com.openapi.json | jq
```

### Issue: Missing endpoints

**Solution 1: Use manual URL to target comprehensive docs**
```bash
# Point directly to API reference page
openapi-gen https://api.example.com \
  --doc-url https://api.example.com/api-reference/
```

**Solution 2: Increase max pages**
```bash
# Crawl more pages for better coverage
MAX_PAGES_PER_SITE=100 openapi-gen https://api.example.com
```

**Solution 3: Check coverage report**
```bash
# Look for low confidence endpoints that might need manual review
openapi-gen https://api.example.com

# Review the coverage report in the output
# Quality score indicates completeness
```

### Issue: Documentation at non-standard path

```bash
# Example: JSONPlaceholder has docs at /guide instead of /docs
openapi-gen https://jsonplaceholder.typicode.com \
  --doc-url https://jsonplaceholder.typicode.com/guide/

# Example: Multiple documentation sections
openapi-gen https://api.example.com \
  --doc-url https://api.example.com/getting-started/ \
  --doc-url https://api.example.com/api-reference/ \
  --doc-url https://api.example.com/webhooks/
```
