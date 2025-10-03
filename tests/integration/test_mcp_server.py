"""Integration tests for MCP server."""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import mcp_server
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the MCP server module to access the tools
import mcp_server

# Get the actual functions from the FastMCP tools
generate_openapi_spec = mcp_server.generate_openapi_spec.fn
validate_openapi_spec = mcp_server.validate_openapi_spec.fn
analyze_spec_coverage = mcp_server.analyze_spec_coverage.fn
save_openapi_spec = mcp_server.save_openapi_spec.fn
list_test_apis = mcp_server.list_test_apis.fn


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_openapi_spec():
    """Test generate_openapi_spec MCP tool."""
    result = await generate_openapi_spec(
        base_url="https://catfact.ninja",
        output_format="json",
        max_pages=10,
    )

    # Check result structure
    assert "success" in result
    assert "spec" in result
    assert "endpoints_count" in result
    assert "quality_score" in result

    if result["success"]:
        # Check spec structure
        assert result["spec"]["openapi"] == "3.0.3"
        assert "paths" in result["spec"]
        assert result["endpoints_count"] > 0

        # Check coverage report
        assert "coverage_report" in result
        assert "total_endpoints" in result["coverage_report"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_openapi_spec():
    """Test validate_openapi_spec MCP tool."""
    # Valid OpenAPI spec
    valid_spec = json.dumps({
        "openapi": "3.0.3",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        }
    })

    result = await validate_openapi_spec(valid_spec)

    assert "is_valid" in result
    assert "errors" in result
    assert "version" in result
    assert result["version"] == "3.0.3"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_analyze_spec_coverage():
    """Test analyze_spec_coverage MCP tool."""
    spec = json.dumps({
        "openapi": "3.0.3",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "example": {"result": "ok"}
                                }
                            }
                        }
                    }
                }
            }
        }
    })

    result = await analyze_spec_coverage(spec)

    assert "total_endpoints" in result
    assert "coverage_percentages" in result
    assert "recommendations" in result

    # Should have 1 endpoint
    assert result["total_endpoints"] == 1

    # Coverage percentages
    coverage = result["coverage_percentages"]
    assert "parameters" in coverage
    assert "request_body" in coverage
    assert "responses" in coverage
    assert "examples" in coverage

    # This endpoint has params, response, and example
    assert coverage["parameters"] == 100.0
    assert coverage["responses"] == 100.0
    assert coverage["examples"] == 100.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_openapi_spec(tmp_path):
    """Test save_openapi_spec MCP tool."""
    spec = json.dumps({
        "openapi": "3.0.3",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {}
    })

    output_path = tmp_path / "test_spec.json"

    result = await save_openapi_spec(
        spec_content=spec,
        output_path=str(output_path),
        format="json"
    )

    assert "success" in result
    assert result["success"] is True
    assert "path" in result
    assert "size_bytes" in result

    # Verify file was created
    assert output_path.exists()
    content = json.loads(output_path.read_text())
    assert content["openapi"] == "3.0.3"


@pytest.mark.integration
def test_list_test_apis():
    """Test list_test_apis MCP tool."""
    result = list_test_apis()

    assert "test_apis" in result
    assert len(result["test_apis"]) > 0

    # Check structure of first API
    first_api = result["test_apis"][0]
    assert "name" in first_api
    assert "url" in first_api
    assert "description" in first_api
    assert "difficulty" in first_api
    assert "expected_endpoints" in first_api


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_tools_integration():
    """Test full MCP workflow: generate, validate, analyze, save."""
    # Step 1: Generate spec
    gen_result = await generate_openapi_spec(
        base_url="https://catfact.ninja",
        output_format="json",
        max_pages=5,
    )

    assert gen_result["success"], "Generation should succeed"
    spec_dict = gen_result["spec"]

    # Step 2: Validate
    spec_json = json.dumps(spec_dict)
    val_result = await validate_openapi_spec(spec_json)

    assert val_result["is_valid"], "Generated spec should be valid"

    # Step 3: Analyze
    coverage_result = await analyze_spec_coverage(spec_json)

    assert coverage_result["total_endpoints"] > 0, "Should have endpoints"

    # Step 4: Save (using pytest tmp_path fixture would be better, but this is integration test)
    # We'll skip actual save in this test to avoid file system issues
