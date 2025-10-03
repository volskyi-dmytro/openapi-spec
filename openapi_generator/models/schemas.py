"""Core data models for OpenAPI specification generation."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"
    TRACE = "trace"


class ParameterLocation(str, Enum):
    """Parameter locations in OpenAPI."""

    QUERY = "query"
    HEADER = "header"
    PATH = "path"
    COOKIE = "cookie"


class DataType(str, Enum):
    """OpenAPI data types."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ConfidenceLevel(str, Enum):
    """Confidence level for extracted information."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Parameter(BaseModel):
    """API parameter model."""

    name: str = Field(description="Parameter name")
    location: ParameterLocation = Field(description="Where the parameter is located")
    description: str | None = Field(None, description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    type: DataType = Field(default=DataType.STRING, description="Parameter data type")
    example: Any | None = Field(None, description="Example value")
    schema_: dict[str, Any] | None = Field(
        None, alias="schema", description="JSON Schema for the parameter"
    )

    model_config = ConfigDict(populate_by_name=True)


class Schema(BaseModel):
    """JSON Schema model for request/response bodies."""

    type: DataType = Field(description="Schema type")
    properties: dict[str, Any] | None = Field(None, description="Properties for object types")
    items: dict[str, Any] | None = Field(None, description="Items for array types")
    required: list[str] | None = Field(None, description="Required properties")
    description: str | None = Field(None, description="Schema description")
    example: Any | None = Field(None, description="Example value")
    additional_properties: bool | None = Field(
        None, alias="additionalProperties", description="Allow additional properties"
    )

    model_config = ConfigDict(populate_by_name=True)


class RequestBody(BaseModel):
    """Request body model."""

    description: str | None = Field(None, description="Request body description")
    required: bool = Field(default=False, description="Whether body is required")
    content_type: str = Field(
        default="application/json", description="Content type (e.g., application/json)"
    )
    schema_: Schema | None = Field(None, alias="schema", description="Body schema")
    example: Any | None = Field(None, description="Example request body")

    model_config = ConfigDict(populate_by_name=True)


class Response(BaseModel):
    """API response model."""

    status_code: str = Field(description="HTTP status code (e.g., '200', '404')")
    description: str = Field(description="Response description")
    content_type: str = Field(
        default="application/json", description="Content type (e.g., application/json)"
    )
    schema_: Schema | None = Field(None, alias="schema", description="Response schema")
    example: Any | None = Field(None, description="Example response")

    model_config = ConfigDict(populate_by_name=True)


class Endpoint(BaseModel):
    """API endpoint model."""

    path: str = Field(description="Endpoint path (e.g., /users/{id})")
    method: HTTPMethod = Field(description="HTTP method")
    summary: str | None = Field(None, description="Short summary")
    description: str | None = Field(None, description="Detailed description")
    operation_id: str | None = Field(None, description="Unique operation identifier")
    tags: list[str] | None = Field(default_factory=list, description="Endpoint tags/categories")
    parameters: list[Parameter] = Field(default_factory=list, description="Endpoint parameters")
    request_body: RequestBody | None = Field(None, description="Request body")
    responses: list[Response] = Field(default_factory=list, description="Possible responses")
    deprecated: bool = Field(default=False, description="Whether endpoint is deprecated")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Confidence in extraction accuracy"
    )
    source_url: str | None = Field(None, description="URL where this endpoint was found")


class SecurityScheme(BaseModel):
    """Security scheme model."""

    type: Literal["apiKey", "http", "oauth2", "openIdConnect"] = Field(
        description="Security scheme type"
    )
    description: str | None = Field(None, description="Security scheme description")
    name: str | None = Field(None, description="Parameter name (for apiKey)")
    location: Literal["query", "header", "cookie"] | None = Field(
        None, alias="in", description="Parameter location (for apiKey)"
    )
    scheme: str | None = Field(None, description="HTTP authorization scheme (for http)")
    bearer_format: str | None = Field(
        None, alias="bearerFormat", description="Bearer token format (for http bearer)"
    )

    model_config = ConfigDict(populate_by_name=True)


class OpenAPIInfo(BaseModel):
    """OpenAPI info section."""

    title: str = Field(description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: str | None = Field(None, description="API description")
    terms_of_service: HttpUrl | None = Field(
        None, alias="termsOfService", description="Terms of service URL"
    )
    contact: dict[str, str] | None = Field(None, description="Contact information")
    license: dict[str, str] | None = Field(None, description="License information")

    model_config = ConfigDict(populate_by_name=True)


class Server(BaseModel):
    """API server model."""

    url: str = Field(description="Server URL")
    description: str | None = Field(None, description="Server description")


class OpenAPISpec(BaseModel):
    """Complete OpenAPI specification model."""

    openapi: str = Field(default="3.0.3", description="OpenAPI version")
    info: OpenAPIInfo = Field(description="API metadata")
    servers: list[Server] = Field(default_factory=list, description="API servers")
    paths: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="API paths and operations"
    )
    components: dict[str, Any] | None = Field(
        None, description="Reusable components (schemas, security schemes, etc.)"
    )
    security: list[dict[str, list[str]]] | None = Field(None, description="Security requirements")
    tags: list[dict[str, str]] | None = Field(None, description="Tag definitions")


class ExtractionResult(BaseModel):
    """Result from LLM extraction."""

    endpoints: list[Endpoint] = Field(default_factory=list, description="Extracted endpoints")
    security_schemes: list[SecurityScheme] = Field(
        default_factory=list, description="Detected security schemes"
    )
    base_url: str | None = Field(None, description="Detected base URL")
    api_title: str | None = Field(None, description="API title")
    api_description: str | None = Field(None, description="API description")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Overall extraction confidence"
    )


class CoverageReport(BaseModel):
    """Coverage and quality metrics."""

    total_endpoints: int = Field(description="Total number of endpoints found")
    endpoints_with_parameters: int = Field(
        description="Number of endpoints with parameters defined"
    )
    endpoints_with_request_body: int = Field(description="Number of endpoints with request body")
    endpoints_with_responses: int = Field(description="Number of endpoints with responses defined")
    endpoints_with_examples: int = Field(description="Number of endpoints with examples")
    confidence_distribution: dict[str, int] = Field(description="Distribution of confidence levels")
    average_confidence: float = Field(description="Average confidence score (0-1)")

    @property
    def parameter_coverage(self) -> float:
        """Calculate parameter coverage percentage."""
        if self.total_endpoints == 0:
            return 0.0
        return (self.endpoints_with_parameters / self.total_endpoints) * 100

    @property
    def response_coverage(self) -> float:
        """Calculate response coverage percentage."""
        if self.total_endpoints == 0:
            return 0.0
        return (self.endpoints_with_responses / self.total_endpoints) * 100

    @property
    def quality_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        if self.total_endpoints == 0:
            return 0.0

        weights = {
            "parameters": 0.25,
            "request_body": 0.20,
            "responses": 0.30,
            "examples": 0.15,
            "confidence": 0.10,
        }

        score = 0.0
        score += (self.endpoints_with_parameters / self.total_endpoints) * weights["parameters"]
        score += (self.endpoints_with_request_body / self.total_endpoints) * weights["request_body"]
        score += (self.endpoints_with_responses / self.total_endpoints) * weights["responses"]
        score += (self.endpoints_with_examples / self.total_endpoints) * weights["examples"]
        score += self.average_confidence * weights["confidence"]

        return score * 100
