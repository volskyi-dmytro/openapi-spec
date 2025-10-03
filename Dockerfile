# Dockerfile for OpenAPI Generator MCP Server
# This allows running the MCP server in a containerized environment

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY openapi_generator/ ./openapi_generator/
COPY mcp_server.py ./
COPY setup.py ./

# Install the package
RUN pip install --no-cache-dir -e .

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps

# Create output directory
RUN mkdir -p /app/output

# Expose port for potential future HTTP transport
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from fastmcp import FastMCP; print('OK')" || exit 1

# Default command (STDIO transport for MCP)
CMD ["python", "mcp_server.py"]
