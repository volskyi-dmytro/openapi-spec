#!/usr/bin/env python3
"""FastMCP server for OpenAPI specification generation.

This MCP server exposes the OpenAPI generator as tools that can be used
by Claude Desktop and other MCP clients.

Usage:
    python mcp_server.py

For Claude Desktop integration, add to claude_desktop_config.json:
    {
      "mcpServers": {
        "openapi-generator": {
          "command": "python",
          "args": ["/absolute/path/to/mcp_server.py"],
          "env": {
            "ANTHROPIC_API_KEY": "your-api-key-here"
          }
        }
      }
    }
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from openapi_generator.generators.openapi_builder import OpenAPIBuilder
from openapi_generator.orchestrator import OpenAPIOrchestrator
from openapi_generator.validators.coverage import CoverageAnalyzer
from openapi_generator.validators.spec_validator import SpecValidator

# Create MCP server
mcp = FastMCP("OpenAPI Generator")


@mcp.tool
async def generate_openapi_spec(
    base_url: str,
    output_format: str = "json",
    max_pages: Optional[int] = None,
    query_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an OpenAPI specification from API documentation.

    This tool automatically discovers API documentation pages, extracts endpoint
    information using Claude AI, and generates a valid OpenAPI 3.0.3 specification.

    Args:
        base_url: The base URL of the API to generate a spec for (e.g., "https://api.example.com")
        output_format: Output format, either "json" or "yaml" (default: "json")
        max_pages: Maximum number of documentation pages to process (default: 50)
        query_filter: Natural language query to filter endpoints (e.g., "payment endpoints only")

    Returns:
        A dictionary containing:
        - success: Whether the generation succeeded
        - spec: The generated OpenAPI specification (as dict)
        - endpoints_count: Number of endpoints extracted
        - quality_score: Quality score (0-100)
        - coverage_report: Coverage analysis
        - error: Error message if failed

    Example:
        generate_openapi_spec("https://api.stripe.com")
    """
    try:
        # Run orchestrator
        orchestrator = OpenAPIOrchestrator(base_url)

        # Override max_pages if specified
        if max_pages:
            orchestrator.settings.max_pages_per_site = max_pages

        # Execute the pipeline
        results = await orchestrator.run()

        if not results:
            return {
                "success": False,
                "error": "No endpoints extracted. The documentation may not be accessible or may not contain API information.",
                "endpoints_count": 0,
            }

        # Build OpenAPI spec
        builder = OpenAPIBuilder(base_url)
        builder.add_extraction_results(results)
        spec = builder.build()

        # Convert spec to dict for validation and output
        spec_dict = json.loads(builder.to_json(spec))

        # Validate with dict
        validator = SpecValidator()
        is_valid, validation_errors = validator.validate(spec_dict)

        # Get coverage metrics from extracted endpoints
        all_endpoints = []
        for result in results:
            all_endpoints.extend(result.endpoints)

        # Apply query filter if provided
        if query_filter:
            from openapi_generator.utils.query_filter import QueryFilter
            query_filter_obj = QueryFilter()
            filtered_endpoints = query_filter_obj.apply_filter(all_endpoints, query_filter, threshold=0.3)

            # Rebuild results with filtered endpoints
            from openapi_generator.models.schemas import ExtractionResult, ConfidenceLevel
            results = [ExtractionResult(
                endpoints=filtered_endpoints,
                confidence=ConfidenceLevel.HIGH,
            )]

            # Rebuild spec with filtered endpoints
            builder = OpenAPIBuilder(base_url)
            builder.add_extraction_results(results)
            spec = builder.build()
            spec_dict = json.loads(builder.to_json(spec))

            all_endpoints = filtered_endpoints

        analyzer = CoverageAnalyzer()
        coverage = analyzer.analyze(all_endpoints)

        return {
            "success": True,
            "spec": spec_dict,
            "endpoints_count": len(spec_dict.get("paths", {})),
            "quality_score": coverage.quality_score,
            "is_valid": is_valid,
            "validation_errors": validation_errors if not is_valid else [],
            "coverage_report": {
                "total_endpoints": coverage.total_endpoints,
                "endpoints_with_parameters": coverage.endpoints_with_parameters,
                "endpoints_with_request_body": coverage.endpoints_with_request_body,
                "endpoints_with_responses": coverage.endpoints_with_responses,
                "endpoints_with_examples": coverage.endpoints_with_examples,
                "confidence_distribution": coverage.confidence_distribution,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Generation failed: {str(e)}",
            "endpoints_count": 0,
        }


@mcp.tool
async def validate_openapi_spec(spec_content: str) -> Dict[str, Any]:
    """Validate an OpenAPI specification.

    Args:
        spec_content: The OpenAPI spec as JSON or YAML string

    Returns:
        A dictionary containing:
        - is_valid: Whether the spec is valid
        - errors: List of validation errors (if any)
        - version: OpenAPI version detected

    Example:
        validate_openapi_spec('{"openapi": "3.0.3", "info": {...}, "paths": {...}}')
    """
    try:
        # Try to parse as JSON first
        try:
            spec_dict = json.loads(spec_content)
        except json.JSONDecodeError:
            # Try YAML
            import yaml
            spec_dict = yaml.safe_load(spec_content)

        # Validate
        validator = SpecValidator()
        is_valid, errors = validator.validate(spec_dict)

        return {
            "is_valid": is_valid,
            "errors": errors,
            "version": spec_dict.get("openapi", "unknown"),
            "paths_count": len(spec_dict.get("paths", {})),
        }

    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Failed to parse spec: {str(e)}"],
            "version": "unknown",
        }


@mcp.tool
async def analyze_spec_coverage(spec_content: str) -> Dict[str, Any]:
    """Analyze the coverage and quality of an OpenAPI specification.

    Args:
        spec_content: The OpenAPI spec as JSON or YAML string

    Returns:
        A dictionary containing detailed coverage metrics:
        - total_endpoints: Number of endpoints
        - coverage_percentages: Breakdown of coverage by category
        - recommendations: List of suggestions to improve the spec

    Note: This function analyzes OpenAPI spec structure, not extraction confidence
    (use generate_openapi_spec for confidence metrics from extraction).

    Example:
        analyze_spec_coverage('{"openapi": "3.0.3", ...}')
    """
    try:
        # Parse spec
        try:
            spec_dict = json.loads(spec_content)
        except json.JSONDecodeError:
            import yaml
            spec_dict = yaml.safe_load(spec_content)

        # Manually analyze the spec structure
        paths = spec_dict.get("paths", {})
        total_endpoints = 0
        endpoints_with_params = 0
        endpoints_with_request_body = 0
        endpoints_with_responses = 0
        endpoints_with_examples = 0

        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                    total_endpoints += 1

                    # Check for parameters
                    if operation.get("parameters"):
                        endpoints_with_params += 1

                    # Check for request body
                    if operation.get("requestBody"):
                        endpoints_with_request_body += 1

                    # Check for responses
                    if operation.get("responses"):
                        endpoints_with_responses += 1

                    # Check for examples
                    has_example = False
                    # Check request body examples
                    if "requestBody" in operation:
                        content = operation["requestBody"].get("content", {})
                        for media_type in content.values():
                            if "example" in media_type or "examples" in media_type:
                                has_example = True
                                break
                    # Check response examples
                    if not has_example and "responses" in operation:
                        for response in operation["responses"].values():
                            content = response.get("content", {})
                            for media_type in content.values():
                                if "example" in media_type or "examples" in media_type:
                                    has_example = True
                                    break
                            if has_example:
                                break

                    if has_example:
                        endpoints_with_examples += 1

        # Generate recommendations
        recommendations = []
        if total_endpoints > 0:
            param_coverage = (endpoints_with_params / total_endpoints) * 100
            body_coverage = (endpoints_with_request_body / total_endpoints) * 100
            response_coverage = (endpoints_with_responses / total_endpoints) * 100
            example_coverage = (endpoints_with_examples / total_endpoints) * 100

            if param_coverage < 50:
                recommendations.append("Add parameter definitions to more endpoints")
            if body_coverage < 30:
                recommendations.append("Document request body schemas for POST/PUT/PATCH endpoints")
            if response_coverage < 70:
                recommendations.append("Add response schemas and status codes")
            if example_coverage < 40:
                recommendations.append("Include examples for requests and responses")

        # Check for security
        if "security" not in spec_dict and "components" not in spec_dict:
            recommendations.append("Consider adding security schemes if the API requires authentication")

        return {
            "total_endpoints": total_endpoints,
            "coverage_percentages": {
                "parameters": round((endpoints_with_params / total_endpoints * 100) if total_endpoints > 0 else 0, 1),
                "request_body": round((endpoints_with_request_body / total_endpoints * 100) if total_endpoints > 0 else 0, 1),
                "responses": round((endpoints_with_responses / total_endpoints * 100) if total_endpoints > 0 else 0, 1),
                "examples": round((endpoints_with_examples / total_endpoints * 100) if total_endpoints > 0 else 0, 1),
            },
            "recommendations": recommendations,
        }

    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}",
            "total_endpoints": 0,
        }


@mcp.tool
async def save_openapi_spec(
    spec_content: str,
    output_path: str,
    format: str = "json",
) -> Dict[str, Any]:
    """Save an OpenAPI specification to a file.

    Args:
        spec_content: The OpenAPI spec as JSON or YAML string
        output_path: Path where to save the file
        format: Output format, either "json" or "yaml" (default: "json")

    Returns:
        A dictionary containing:
        - success: Whether the save succeeded
        - path: Absolute path to the saved file
        - size_bytes: File size in bytes
        - error: Error message if failed

    Example:
        save_openapi_spec(spec, "/path/to/output.json", "json")
    """
    try:
        # Parse spec
        try:
            spec_dict = json.loads(spec_content)
        except json.JSONDecodeError:
            import yaml
            spec_dict = yaml.safe_load(spec_content)

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        if format.lower() == "yaml":
            import yaml
            with open(output_file, "w") as f:
                yaml.dump(spec_dict, f, default_flow_style=False, sort_keys=False)
        else:
            with open(output_file, "w") as f:
                json.dump(spec_dict, f, indent=2)

        file_size = output_file.stat().st_size

        return {
            "success": True,
            "path": str(output_file.absolute()),
            "size_bytes": file_size,
            "format": format,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save spec: {str(e)}",
        }


@mcp.tool
def list_test_apis() -> Dict[str, Any]:
    """List available test APIs that can be used to try the generator.

    Returns:
        A dictionary containing a list of test APIs with their details.

    Example:
        list_test_apis()
    """
    return {
        "test_apis": [
            {
                "name": "JSONPlaceholder",
                "url": "https://jsonplaceholder.typicode.com",
                "description": "Simple REST API for testing",
                "difficulty": "easy",
                "expected_endpoints": "~10 endpoints (posts, users, comments)",
            },
            {
                "name": "Cat Facts",
                "url": "https://catfact.ninja",
                "description": "Cat facts API with embedded OpenAPI spec",
                "difficulty": "easy",
                "expected_endpoints": "~3 endpoints (facts, breeds)",
            },
            {
                "name": "PokéAPI",
                "url": "https://pokeapi.co",
                "description": "Pokemon data API",
                "difficulty": "medium",
                "expected_endpoints": "~30+ endpoints (pokemon, abilities, items)",
            },
            {
                "name": "REST Countries",
                "url": "https://restcountries.com",
                "description": "Country information API",
                "difficulty": "easy",
                "expected_endpoints": "~5 endpoints (all countries, by name, by code)",
            },
        ]
    }


# Resources
@mcp.resource("openapi://version")
def get_version() -> str:
    """Get the OpenAPI Generator version."""
    return "0.1.0"


@mcp.resource("openapi://status")
def get_status() -> Dict[str, Any]:
    """Get the current status of the OpenAPI Generator."""
    return {
        "status": "ready",
        "version": "0.1.0",
        "capabilities": [
            "generate_openapi_spec",
            "validate_openapi_spec",
            "analyze_spec_coverage",
            "save_openapi_spec",
            "list_test_apis",
        ],
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
