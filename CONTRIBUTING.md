# Contributing Guide

Thank you for your interest in contributing to the OpenAPI Specification Generator! This guide will help you get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Areas for Contribution](#areas-for-contribution)

---

## Code of Conduct

This project follows a simple code of conduct:

1. **Be respectful** - Treat everyone with respect and kindness
2. **Be constructive** - Provide helpful feedback
3. **Be collaborative** - Work together toward better solutions
4. **Be patient** - Everyone is learning

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- Basic understanding of Python and asyncio

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/openapi-spec-generator.git
   cd openapi-spec-generator
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/openapi-spec-generator.git
   ```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all dependencies including dev tools
pip install -r requirements.txt
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### 3. Set Up Environment

```bash
# Copy example env file
cp .env.example .env

# Add your Anthropic API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

### 4. Verify Setup

```bash
# Run tests
pytest tests/unit/ -v

# Check code style
black --check openapi_generator/
ruff check openapi_generator/

# Verify installation
openapi-gen --help
```

---

## Making Changes

### Branch Strategy

- `main` - Production-ready code
- `develop` - Development branch
- Feature branches: `feature/your-feature-name`
- Bug fixes: `fix/issue-description`

### Creating a Feature Branch

```bash
# Update your local repository
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/your-feature-name
```

### Development Workflow

1. **Make your changes** in the feature branch
2. **Write tests** for new functionality
3. **Update documentation** if needed
4. **Run tests** to ensure nothing breaks
5. **Format code** with black and ruff
6. **Commit changes** with clear messages

---

## Testing

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=openapi_generator --cov-report=html

# Run integration tests (requires API key)
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_models.py -v

# Run specific test
pytest tests/unit/test_models.py::test_parameter_creation -v
```

### Writing Tests

**Unit Test Example**:
```python
# tests/unit/test_your_module.py
import pytest
from openapi_generator.your_module import YourClass


def test_your_function():
    """Test that your function works correctly."""
    # Arrange
    input_data = {"key": "value"}

    # Act
    result = your_function(input_data)

    # Assert
    assert result == expected_output
```

**Async Test Example**:
```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

### Test Requirements

- **Coverage**: Aim for 80%+ coverage
- **All test types**:
  - Unit tests (fast, isolated)
  - Integration tests (end-to-end)
  - Edge cases
  - Error handling

---

## Code Style

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Line length: 100 characters (not 79)
# Use black for formatting
# Use type hints

# Good example
async def extract_content(url: str, timeout: int = 60) -> DocumentContent:
    """Extract content from a URL.

    Args:
        url: The URL to extract from
        timeout: Request timeout in seconds

    Returns:
        Extracted document content

    Raises:
        HTTPError: If request fails
    """
    ...
```

### Formatting Tools

```bash
# Format code with black
black openapi_generator/ tests/

# Check formatting
black --check openapi_generator/

# Lint with ruff
ruff check openapi_generator/ --fix

# Type checking (optional but recommended)
mypy openapi_generator/
```

### Documentation Standards

**Docstrings**: Use Google style

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed. Explain what the function does,
    not how it does it.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
        HTTPError: When request fails

    Example:
        >>> function_name("test", 42)
        True
    """
    ...
```

**Code Comments**:
- Explain **why**, not **what**
- Complex algorithms need explanations
- Keep comments up-to-date

---

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```
feat(llm): add support for GPT-4 extraction

Implement alternative LLM provider using OpenAI's GPT-4.
Includes fallback logic and configuration options.

Closes #42
```

```
fix(cache): resolve cache key collision issue

Cache keys were colliding for similar URLs. Now using
MD5 hash of full URL + timestamp.

Fixes #38
```

```
docs(readme): update installation instructions

Added troubleshooting section and clarified Python version requirements.
```

### Commit Best Practices

-  **One logical change per commit**
-  **Clear, descriptive messages**
-  **Present tense** ("add feature" not "added feature")
-  **Reference issues** when applicable
-  Avoid "WIP" or "fix typo" commits (squash before PR)

---

## Pull Request Process

### Before Creating PR

1. **Update your branch**:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout your-branch
   git rebase develop
   ```

2. **Run full test suite**:
   ```bash
   pytest tests/ -v
   black --check openapi_generator/
   ruff check openapi_generator/
   ```

3. **Update documentation** if needed

4. **Squash commits** if necessary:
   ```bash
   git rebase -i develop
   ```

### Creating the Pull Request

1. **Push to your fork**:
   ```bash
   git push origin your-branch
   ```

2. **Create PR** on GitHub

3. **Fill out PR template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

### PR Review Process

1. **Automated checks** run (CI/CD pipeline)
2. **Code review** by maintainers
3. **Address feedback** if requested
4. **Approval** and merge

### After Merge

```bash
# Update your local repository
git checkout develop
git pull upstream develop

# Delete feature branch
git branch -d your-branch
git push origin --delete your-branch
```

---

## Areas for Contribution

###  High-Priority Areas

1. **Multi-Model Support**
   - Add support for OpenAI GPT-4
   - Add support for Google Gemini
   - Implement model fallback logic

2. **Enhanced Schema Inference**
   - Better type detection from examples
   - JSON Schema generation improvements
   - Union type support

3. **Performance Optimization**
   - Improve caching strategies
   - Reduce token usage
   - Faster content extraction

4. **Documentation Sites Support**
   - Add support for Swagger UI parsing
   - Add support for Redoc parsing
   - Add support for GraphQL schemas

###  Bug Fixes

Check [GitHub Issues](https://github.com/YOUR_USERNAME/openapi-spec-generator/issues) for open bugs.

###  Documentation

- Improve examples
- Add tutorials
- Create video guides
- Translate documentation

###  Testing

- Increase test coverage
- Add more integration tests
- Test with real-world APIs
- Performance benchmarks

###  Quality Improvements

- Improve error messages
- Add progress indicators
- Better logging
- UX enhancements

---

## Getting Help

**Questions?**
-  Read the [README](README.md)
- ️ Check [ARCHITECTURE](ARCHITECTURE.md)
-  See [TROUBLESHOOTING](TROUBLESHOOTING.md)
-  Open a [Discussion](https://github.com/YOUR_USERNAME/openapi-spec-generator/discussions)
-  Ask on [Twitter](https://twitter.com/...)

**Found a bug?**
-  Open an [Issue](https://github.com/YOUR_USERNAME/openapi-spec-generator/issues)

---

## Recognition

Contributors will be:
-  Listed in README
-  Mentioned in release notes
-  Credited in documentation

Thank you for contributing! 

---

**Last Updated**: 2025-10-01
