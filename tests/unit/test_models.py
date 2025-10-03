"""Unit tests for data models."""

import pytest
from pydantic import ValidationError

from openapi_generator.models.schemas import (
    ConfidenceLevel,
    CoverageReport,
    DataType,
    Endpoint,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    Response,
    Schema,
)


def test_parameter_creation():
    """Test Parameter model creation."""
    param = Parameter(
        name="user_id",
        location=ParameterLocation.PATH,
        description="User ID",
        required=True,
        type=DataType.INTEGER,
        example=123,
    )

    assert param.name == "user_id"
    assert param.location == ParameterLocation.PATH
    assert param.required is True
    assert param.type == DataType.INTEGER


def test_parameter_validation():
    """Test Parameter validation."""
    # Missing required field
    with pytest.raises(ValidationError):
        Parameter(location=ParameterLocation.QUERY)

    # Invalid location
    with pytest.raises(ValidationError):
        Parameter(name="test", location="invalid")


def test_schema_creation():
    """Test Schema model creation."""
    schema = Schema(
        type=DataType.OBJECT,
        properties={"id": {"type": "integer"}, "name": {"type": "string"}},
        required=["id"],
        description="User schema",
    )

    assert schema.type == DataType.OBJECT
    assert "id" in schema.properties
    assert "name" in schema.properties
    assert schema.required == ["id"]


def test_response_creation():
    """Test Response model creation."""
    response = Response(
        status_code="200",
        description="Successful response",
        content_type="application/json",
        schema_=Schema(type=DataType.OBJECT, properties={"success": {"type": "boolean"}}),
    )

    assert response.status_code == "200"
    assert response.description == "Successful response"
    assert response.schema_.type == DataType.OBJECT


def test_endpoint_creation():
    """Test Endpoint model creation."""
    endpoint = Endpoint(
        path="/users/{id}",
        method=HTTPMethod.GET,
        summary="Get user by ID",
        description="Retrieve a user by their unique identifier",
        parameters=[
            Parameter(
                name="id",
                location=ParameterLocation.PATH,
                required=True,
                type=DataType.INTEGER,
            )
        ],
        responses=[Response(status_code="200", description="User found")],
        confidence=ConfidenceLevel.HIGH,
    )

    assert endpoint.path == "/users/{id}"
    assert endpoint.method == HTTPMethod.GET
    assert len(endpoint.parameters) == 1
    assert endpoint.parameters[0].name == "id"
    assert endpoint.confidence == ConfidenceLevel.HIGH


def test_endpoint_defaults():
    """Test Endpoint default values."""
    endpoint = Endpoint(path="/test", method=HTTPMethod.GET, summary="Test endpoint")

    assert endpoint.parameters == []
    assert endpoint.responses == []
    assert endpoint.tags == []
    assert endpoint.deprecated is False
    assert endpoint.confidence == ConfidenceLevel.MEDIUM


def test_coverage_report_calculations():
    """Test CoverageReport calculations."""
    report = CoverageReport(
        total_endpoints=100,
        endpoints_with_parameters=80,
        endpoints_with_request_body=30,
        endpoints_with_responses=90,
        endpoints_with_examples=50,
        confidence_distribution={"high": 70, "medium": 25, "low": 5},
        average_confidence=0.8,
    )

    assert report.parameter_coverage == 80.0
    assert report.response_coverage == 90.0
    assert report.quality_score > 0  # Should be calculated


def test_coverage_report_empty():
    """Test CoverageReport with no endpoints."""
    report = CoverageReport(
        total_endpoints=0,
        endpoints_with_parameters=0,
        endpoints_with_request_body=0,
        endpoints_with_responses=0,
        endpoints_with_examples=0,
        confidence_distribution={},
        average_confidence=0.0,
    )

    assert report.parameter_coverage == 0.0
    assert report.response_coverage == 0.0
    assert report.quality_score == 0.0


def test_http_method_enum():
    """Test HTTPMethod enum values."""
    assert HTTPMethod.GET.value == "get"
    assert HTTPMethod.POST.value == "post"
    assert HTTPMethod.PUT.value == "put"
    assert HTTPMethod.DELETE.value == "delete"


def test_confidence_level_enum():
    """Test ConfidenceLevel enum values."""
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.MEDIUM.value == "medium"
    assert ConfidenceLevel.LOW.value == "low"


def test_endpoint_with_all_fields():
    """Test Endpoint with all fields populated."""
    endpoint = Endpoint(
        path="/users",
        method=HTTPMethod.POST,
        summary="Create user",
        description="Create a new user account",
        operation_id="create_user",
        tags=["users", "authentication"],
        parameters=[
            Parameter(
                name="api_key",
                location=ParameterLocation.HEADER,
                required=True,
                type=DataType.STRING,
            )
        ],
        request_body={
            "description": "User data",
            "required": True,
            "content_type": "application/json",
        },
        responses=[
            Response(status_code="201", description="User created"),
            Response(status_code="400", description="Invalid input"),
        ],
        deprecated=False,
        confidence=ConfidenceLevel.HIGH,
        source_url="https://api.example.com/docs/users",
    )

    assert endpoint.operation_id == "create_user"
    assert len(endpoint.tags) == 2
    assert "users" in endpoint.tags
    assert len(endpoint.responses) == 2
    assert endpoint.source_url == "https://api.example.com/docs/users"
