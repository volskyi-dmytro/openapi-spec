"""Core data models for OpenAPI specification generation."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    type: DataType = Field(default=DataType.STRING, description="Parameter data type")
    example: Optional[Any] = Field(None, description="Example value")
    schema_: Optional[Dict[str, Any]] = Field(
        None, alias="schema", description="JSON Schema for the parameter"
    )

    model_config = ConfigDict(populate_by_name=True)


class Schema(BaseModel):
    """JSON Schema model for request/response bodies."""

    type: DataType = Field(description="Schema type")
    properties: Optional[Dict[str, Any]] = Field(
        None, description="Properties for object types"
    )
    items: Optional[Dict[str, Any]] = Field(None, description="Items for array types")
    required: Optional[List[str]] = Field(None, description="Required properties")
    description: Optional[str] = Field(None, description="Schema description")
    example: Optional[Any] = Field(None, description="Example value")
    additional_properties: Optional[bool] = Field(
        None, alias="additionalProperties", description="Allow additional properties"
    )

    model_config = ConfigDict(populate_by_name=True)


class RequestBody(BaseModel):
    """Request body model."""

    description: Optional[str] = Field(None, description="Request body description")
    required: bool = Field(default=False, description="Whether body is required")
    content_type: str = Field(
        default="application/json", description="Content type (e.g., application/json)"
    )
    schema_: Optional[Schema] = Field(None, alias="schema", description="Body schema")
    example: Optional[Any] = Field(None, description="Example request body")

    model_config = ConfigDict(populate_by_name=True)


class Response(BaseModel):
    """API response model."""

    status_code: str = Field(description="HTTP status code (e.g., '200', '404')")
    description: str = Field(description="Response description")
    content_type: str = Field(
        default="application/json", description="Content type (e.g., application/json)"
    )
    schema_: Optional[Schema] = Field(None, alias="schema", description="Response schema")
    example: Optional[Any] = Field(None, description="Example response")

    model_config = ConfigDict(populate_by_name=True)


class Endpoint(BaseModel):
    """API endpoint model."""

    path: str = Field(description="Endpoint path (e.g., /users/{id})")
    method: HTTPMethod = Field(description="HTTP method")
    summary: Optional[str] = Field(None, description="Short summary")
    description: Optional[str] = Field(None, description="Detailed description")
    operation_id: Optional[str] = Field(None, description="Unique operation identifier")
    tags: Optional[List[str]] = Field(default_factory=list, description="Endpoint tags/categories")
    parameters: List[Parameter] = Field(
        default_factory=list, description="Endpoint parameters"
    )
    request_body: Optional[RequestBody] = Field(None, description="Request body")
    responses: List[Response] = Field(default_factory=list, description="Possible responses")
    deprecated: bool = Field(default=False, description="Whether endpoint is deprecated")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Confidence in extraction accuracy"
    )
    source_url: Optional[str] = Field(None, description="URL where this endpoint was found")


class SecurityScheme(BaseModel):
    """Security scheme model."""

    type: Literal["apiKey", "http", "oauth2", "openIdConnect"] = Field(
        description="Security scheme type"
    )
    description: Optional[str] = Field(None, description="Security scheme description")
    name: Optional[str] = Field(None, description="Parameter name (for apiKey)")
    location: Optional[Literal["query", "header", "cookie"]] = Field(
        None, alias="in", description="Parameter location (for apiKey)"
    )
    scheme: Optional[str] = Field(None, description="HTTP authorization scheme (for http)")
    bearer_format: Optional[str] = Field(
        None, alias="bearerFormat", description="Bearer token format (for http bearer)"
    )

    model_config = ConfigDict(populate_by_name=True)


class OpenAPIInfo(BaseModel):
    """OpenAPI info section."""

    title: str = Field(description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: Optional[str] = Field(None, description="API description")
    terms_of_service: Optional[HttpUrl] = Field(
        None, alias="termsOfService", description="Terms of service URL"
    )
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")
    license: Optional[Dict[str, str]] = Field(None, description="License information")

    model_config = ConfigDict(populate_by_name=True)


class Server(BaseModel):
    """API server model."""

    url: str = Field(description="Server URL")
    description: Optional[str] = Field(None, description="Server description")


class OpenAPISpec(BaseModel):
    """Complete OpenAPI specification model."""

    openapi: str = Field(default="3.0.3", description="OpenAPI version")
    info: OpenAPIInfo = Field(description="API metadata")
    servers: List[Server] = Field(default_factory=list, description="API servers")
    paths: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="API paths and operations"
    )
    components: Optional[Dict[str, Any]] = Field(
        None, description="Reusable components (schemas, security schemes, etc.)"
    )
    security: Optional[List[Dict[str, List[str]]]] = Field(
        None, description="Security requirements"
    )
    tags: Optional[List[Dict[str, str]]] = Field(None, description="Tag definitions")


class ExtractionResult(BaseModel):
    """Result from LLM extraction."""

    endpoints: List[Endpoint] = Field(default_factory=list, description="Extracted endpoints")
    security_schemes: List[SecurityScheme] = Field(
        default_factory=list, description="Detected security schemes"
    )
    base_url: Optional[str] = Field(None, description="Detected base URL")
    api_title: Optional[str] = Field(None, description="API title")
    api_description: Optional[str] = Field(None, description="API description")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Overall extraction confidence"
    )


class CoverageReport(BaseModel):
    """Coverage and quality metrics."""

    total_endpoints: int = Field(description="Total number of endpoints found")
    endpoints_with_parameters: int = Field(
        description="Number of endpoints with parameters defined"
    )
    endpoints_with_request_body: int = Field(
        description="Number of endpoints with request body"
    )
    endpoints_with_responses: int = Field(
        description="Number of endpoints with responses defined"
    )
    endpoints_with_examples: int = Field(
        description="Number of endpoints with examples"
    )
    confidence_distribution: Dict[str, int] = Field(
        description="Distribution of confidence levels"
    )
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
        score += (
            self.endpoints_with_request_body / self.total_endpoints
        ) * weights["request_body"]
        score += (self.endpoints_with_responses / self.total_endpoints) * weights["responses"]
        score += (self.endpoints_with_examples / self.total_endpoints) * weights["examples"]
        score += self.average_confidence * weights["confidence"]

        return score * 100
