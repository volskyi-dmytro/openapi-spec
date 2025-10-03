"""Unit tests for OpenAPI builder."""

import json

import pytest

from openapi_generator.generators.openapi_builder import OpenAPIBuilder
from openapi_generator.models.schemas import (
    ConfidenceLevel,
    DataType,
    Endpoint,
    ExtractionResult,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    Response,
)


@pytest.fixture
def sample_endpoints():
    """Create sample endpoints for testing."""
    return [
        Endpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users",
            description="Get all users",
            parameters=[
                Parameter(
                    name="limit",
                    location=ParameterLocation.QUERY,
                    type=DataType.INTEGER,
                    description="Maximum number of results",
                )
            ],
            responses=[Response(status_code="200", description="Success")],
            confidence=ConfidenceLevel.HIGH,
        ),
        Endpoint(
            path="/users/{id}",
            method=HTTPMethod.GET,
            summary="Get user",
            description="Get user by ID",
            parameters=[
                Parameter(
                    name="id",
                    location=ParameterLocation.PATH,
                    type=DataType.INTEGER,
                    required=True,
                    description="User ID",
                )
            ],
            responses=[Response(status_code="200", description="User found")],
            confidence=ConfidenceLevel.HIGH,
        ),
    ]


@pytest.fixture
def extraction_result(sample_endpoints):
    """Create sample extraction result."""
    return ExtractionResult(
        endpoints=sample_endpoints,
        api_title="Test API",
        api_description="A test API",
        base_url="https://api.example.com",
        confidence=ConfidenceLevel.HIGH,
    )


def test_builder_initialization():
    """Test builder initialization."""
    builder = OpenAPIBuilder("https://api.example.com")
    assert builder.base_url == "https://api.example.com"
    assert builder.endpoints == []


def test_add_extraction_results(extraction_result):
    """Test adding extraction results."""
    builder = OpenAPIBuilder("https://api.example.com")
    builder.add_extraction_results([extraction_result])

    assert len(builder.endpoints) == 2
    assert builder.api_title == "Test API"
    assert builder.api_description == "A test API"


def test_build_spec(extraction_result):
    """Test building OpenAPI spec."""
    builder = OpenAPIBuilder("https://api.example.com")
    builder.add_extraction_results([extraction_result])
    spec = builder.build()

    assert spec.openapi == "3.0.3"
    assert spec.info.title == "Test API"
    assert spec.info.description == "A test API"
    assert len(spec.servers) > 0
    assert len(spec.paths) == 2


def test_spec_to_json(extraction_result):
    """Test converting spec to JSON."""
    builder = OpenAPIBuilder("https://api.example.com")
    builder.add_extraction_results([extraction_result])
    spec = builder.build()

    json_str = builder.to_json(spec)
    assert isinstance(json_str, str)

    # Parse to verify valid JSON
    spec_dict = json.loads(json_str)
    assert spec_dict["openapi"] == "3.0.3"
    assert "paths" in spec_dict
    assert "/users" in spec_dict["paths"]


def test_spec_to_yaml(extraction_result):
    """Test converting spec to YAML."""
    builder = OpenAPIBuilder("https://api.example.com")
    builder.add_extraction_results([extraction_result])
    spec = builder.build()

    yaml_str = builder.to_yaml(spec)
    assert isinstance(yaml_str, str)
    assert "openapi:" in yaml_str
    assert "paths:" in yaml_str


def test_deduplication():
    """Test endpoint deduplication."""
    builder = OpenAPIBuilder("https://api.example.com")

    # Add same endpoint twice with different confidence
    endpoints1 = [
        Endpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users - v1",
            confidence=ConfidenceLevel.MEDIUM,
        )
    ]
    endpoints2 = [
        Endpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users - v2",
            confidence=ConfidenceLevel.HIGH,  # Higher confidence
        )
    ]

    builder.endpoints = endpoints1 + endpoints2
    unique = builder._deduplicate_endpoints()

    # Should keep only one
    assert len(unique) == 1
    # Should keep the higher confidence one
    assert unique[0].summary == "List users - v2"


def test_operation_id_generation():
    """Test operation ID generation."""
    builder = OpenAPIBuilder("https://api.example.com")

    endpoint = Endpoint(
        path="/users/{id}/profile",
        method=HTTPMethod.GET,
        summary="Get user profile",
    )

    operation_id = builder._generate_operation_id(endpoint)
    assert operation_id == "get_users_by_id_profile"


def test_build_info_with_defaults():
    """Test building info section with defaults."""
    builder = OpenAPIBuilder("https://api.example.com")
    # Don't set api_title
    info = builder._build_info()

    assert "example.com" in info.title
    assert info.version == "1.0.0"
    assert "api.example.com" in info.description


def test_build_servers():
    """Test building servers section."""
    builder = OpenAPIBuilder("https://api.example.com")
    servers = builder._build_servers()

    assert len(servers) == 1
    assert servers[0].url == "https://api.example.com"


def test_build_servers_with_detected_url():
    """Test building servers with detected base URL."""
    builder = OpenAPIBuilder("https://api.example.com")
    builder.detected_base_url = "https://api.example.com/v2"

    servers = builder._build_servers()
    assert servers[0].url == "https://api.example.com/v2"


def test_paths_normalization():
    """Test path normalization."""
    builder = OpenAPIBuilder("https://api.example.com")

    endpoints = [
        Endpoint(
            path="users",  # Missing leading slash
            method=HTTPMethod.GET,
            summary="List users",
        )
    ]

    builder.endpoints = endpoints
    spec = builder.build()
    spec_dict = spec.model_dump(by_alias=True, exclude_none=True)

    # Should have leading slash
    assert "/users" in spec_dict["paths"]


def test_multiple_methods_same_path():
    """Test multiple methods on same path."""
    builder = OpenAPIBuilder("https://api.example.com")

    endpoints = [
        Endpoint(path="/users", method=HTTPMethod.GET, summary="List users"),
        Endpoint(path="/users", method=HTTPMethod.POST, summary="Create user"),
    ]

    builder.endpoints = endpoints
    spec = builder.build()
    spec_dict = spec.model_dump(by_alias=True, exclude_none=True)

    # Should have both methods
    assert "get" in spec_dict["paths"]["/users"]
    assert "post" in spec_dict["paths"]["/users"]


def test_tags_generation():
    """Test tags generation from endpoints."""
    builder = OpenAPIBuilder("https://api.example.com")

    endpoints = [
        Endpoint(path="/users", method=HTTPMethod.GET, summary="List", tags=["users"]),
        Endpoint(path="/posts", method=HTTPMethod.GET, summary="List", tags=["posts"]),
        Endpoint(path="/comments", method=HTTPMethod.GET, summary="List", tags=["posts", "users"]),
    ]

    builder.endpoints = endpoints
    spec = builder.build()

    # Should have unique tags
    assert spec.tags is not None
    tag_names = [t["name"] for t in spec.tags]
    assert "users" in tag_names
    assert "posts" in tag_names
    assert len(tag_names) == 2  # Only unique tags


def test_empty_endpoints():
    """Test building spec with no endpoints."""
    builder = OpenAPIBuilder("https://api.example.com")
    spec = builder.build()

    assert spec.openapi == "3.0.3"
    assert spec.info.title
    assert spec.paths == {}
