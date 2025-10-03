# Testing Guide

## Quick Start Testing

### 1. Unit Tests (No API Key Required)

Run the unit tests to verify the core functionality:

```bash
# Activate virtual environment
source venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=openapi_generator --cov-report=html
```

Expected output:
```
tests/unit/test_models.py ...................... PASSED
tests/unit/test_openapi_builder.py ............. PASSED

======================== 15 passed in 0.5s ========================
```

### 2. Demo Script (Requires API Key)

Test the full pipeline with a simple API:

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run demo with a simple API
python demo.py https://jsonplaceholder.typicode.com
```

### 3. API Test Suite (Requires API Key)

Test against multiple real APIs:

```bash
# Test a single easy API (recommended first)
python test_api.py jsonplaceholder

# Test multiple APIs
python test_api.py jsonplaceholder restcountries

# Test all APIs (takes 10-15 minutes)
python test_api.py all
```

## Recommended Testing APIs

###  Easy - Great for First Tests

#### 1. JSONPlaceholder
```bash
python demo.py https://jsonplaceholder.typicode.com
```
- **Pros**: Very simple, well-documented, fast
- **Expected**: ~6-10 endpoints
- **Time**: ~1-2 minutes

#### 2. REST Countries
```bash
python demo.py https://restcountries.com
```
- **Pros**: Simple, clear structure
- **Expected**: ~5 endpoints
- **Time**: ~1 minute

#### 3. Official Joke API
```bash
python demo.py https://official-joke-api.appspot.com
```
- **Pros**: Minimal, quick to test
- **Expected**: ~3 endpoints
- **Time**: ~30 seconds

###  Medium - Good for Comprehensive Testing

#### 4. PokéAPI
```bash
python demo.py https://pokeapi.co
```
- **Pros**: Large, well-structured docs
- **Expected**: 30+ endpoints
- **Time**: ~3-5 minutes

#### 5. OpenWeatherMap
```bash
python demo.py https://openweathermap.org/api
```
- **Pros**: Real-world API, good documentation
- **Expected**: 10-15 endpoints
- **Time**: ~2-3 minutes

###  Hard - Stress Tests

#### 6. GitHub REST API
```bash
python demo.py https://docs.github.com/en/rest
```
- **Pros**: Complex, comprehensive documentation
- **Expected**: 100+ endpoints
- **Time**: ~10-15 minutes
- **Note**: May hit rate limits

## Expected Test Results

### Success Criteria

A successful test should show:

 **Discovery**: 3-50 documentation pages found
 **Extraction**: 80%+ of pages successfully extracted
 **LLM Processing**: No errors, all pages processed
 **Endpoints**: At least 50% of expected endpoints found
 **Validation**: Spec passes OpenAPI validation
 **Quality Score**: 60%+ overall quality

### Sample Output

```
OpenAPI Generator Demo
Extracting from: https://jsonplaceholder.typicode.com

Stage 1: Discovering documentation pages...
 Found 8 documentation URLs

Stage 2: Extracting content...
 Extracted content from 8 pages

Stage 3: Extracting API info with LLM...
 Processed 8 pages
 Extracted 10 endpoints

Stage 4: Building OpenAPI specification...
 OpenAPI 3.0 spec generated

Stage 5: Validating & analyzing...
 Specification is valid!

Quality Metrics:
  - Total Endpoints: 10
  - Parameter Coverage: 80.0%
  - Response Coverage: 100.0%
  - Quality Score: 78.5%

 Saved to: output/jsonplaceholder_typicode_com_demo.openapi.json

Demo Complete!
Generated spec with 10 paths
```

## Troubleshooting Common Issues

### Issue 1: "No documentation pages found"

**Possible Causes:**
- Site uses non-standard documentation paths
- Site blocks automated crawling
- Rate limiting

**Solutions:**
```bash
# Try with more depth
MAX_DEPTH=5 python demo.py <url>

# Check with debug logging
LOG_LEVEL=DEBUG python demo.py <url>

# Check if site is accessible
curl -I <url>
```

### Issue 2: "No content extracted"

**Possible Causes:**
- JavaScript-heavy site (SPA)
- Content behind authentication
- Unusual HTML structure

**Solutions:**
- Check if SPA detection is working
- Verify the site doesn't require login
- Try with a different API

### Issue 3: API key errors

```
Error: ANTHROPIC_API_KEY not set
```

**Solution:**
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Or create .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### Issue 4: Validation failures

**Possible Causes:**
- LLM extraction errors
- Schema inference issues
- Missing required fields

**Check:**
```bash
# Generate without validation
python demo.py <url> --no-validate

# Inspect generated spec
cat output/*.json | jq '.paths | keys'
```

## Performance Benchmarks

Expected timing for different API sizes:

| API Size | Pages | Endpoints | Time | Cost |
|----------|-------|-----------|------|------|
| Small | 5-10 | 5-15 | 1-2 min | $0.10-0.30 |
| Medium | 10-30 | 15-50 | 3-5 min | $0.30-0.80 |
| Large | 30-100 | 50-200 | 10-20 min | $0.80-2.00 |

*Cost based on Claude Sonnet 4 pricing as of 2025*

## Manual Verification

After generating a spec, verify quality:

### 1. Check Endpoint Coverage
```bash
# Count endpoints in generated spec
jq '.paths | length' output/your-api.openapi.json

# List all endpoints
jq '.paths | keys[]' output/your-api.openapi.json
```

### 2. Validate with External Tool
```bash
# Using openapi-spec-validator
openapi-spec-validator output/your-api.openapi.json

# Using Swagger Editor (online)
# Upload to: https://editor.swagger.io/
```

### 3. Compare with Official Spec
```bash
# If the API has an official spec
diff <(jq -S '.paths | keys' official.json) \
     <(jq -S '.paths | keys' generated.json)
```

### 4. Check Quality Metrics

Look for:
-  High confidence endpoints (>70%)
-  Parameter coverage >70%
-  Response definitions >80%
-  Examples included

## CI/CD Testing

### GitHub Actions Example

```yaml
name: Test OpenAPI Generator

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .
          playwright install chromium

      - name: Run unit tests
        run: pytest tests/unit/ -v

      - name: Test with JSONPlaceholder
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python test_api.py jsonplaceholder

      - name: Upload generated specs
        uses: actions/upload-artifact@v3
        with:
          name: generated-specs
          path: output/*.json
```

## Regression Testing

### Creating Test Fixtures

Save known-good specs for regression testing:

```bash
# Generate and save as fixture
python demo.py https://jsonplaceholder.typicode.com
cp output/jsonplaceholder_typicode_com_demo.openapi.json \
   tests/fixtures/jsonplaceholder_expected.json

# Compare in tests
pytest tests/integration/test_regression.py
```

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with debug output
python demo.py https://api.example.com 2>&1 | tee debug.log

# Check what URLs were tried
grep "Trying.*path" debug.log

# Check LLM prompts
grep "Extracting API info" debug.log
```

## Performance Profiling

Profile the system to find bottlenecks:

```python
import cProfile
import pstats

# Profile the demo
cProfile.run('asyncio.run(demo("https://api.example.com"))', 'stats.prof')

# Analyze results
p = pstats.Stats('stats.prof')
p.sort_stats('cumulative')
p.print_stats(20)  # Top 20 slowest functions
```

Expected bottlenecks:
1. LLM API calls (80% of time)
2. Playwright rendering (10% if used)
3. HTTP fetching (5%)

## Contributing Tests

When adding new features, include:

1. **Unit tests** for new functions
2. **Integration tests** if adding new extractors
3. **Example API** that demonstrates the feature
4. **Documentation** in this file

Example test structure:
```python
def test_new_feature():
    """Test new feature X."""
    # Setup
    input_data = ...

    # Execute
    result = new_feature(input_data)

    # Verify
    assert result.is_valid()
    assert result.meets_expectations()
```

## Getting Help

If tests fail unexpectedly:

1. Check this troubleshooting guide
2. Enable DEBUG logging
3. Try with a simpler API (JSONPlaceholder)
4. Check API documentation is accessible
5. Open an issue with:
   - API URL tested
   - Error message
   - Debug logs
   - Generated spec (if any)
