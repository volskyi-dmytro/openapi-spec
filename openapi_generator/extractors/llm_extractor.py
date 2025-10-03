"""LLM-powered extraction of API information from documentation."""

import json
from typing import List, Optional

import anthropic

from openapi_generator.config import get_settings
from openapi_generator.extractors.content import DocumentContent
from openapi_generator.extractors.auth_detector import AuthDetector
from openapi_generator.utils.cache import get_cache_manager
from openapi_generator.models.schemas import (
    ConfidenceLevel,
    DataType,
    Endpoint,
    ExtractionResult,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    Schema,
    SecurityScheme,
)
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class LLMExtractor:
    """Extracts API information using Claude with structured outputs."""

    EXTRACTION_PROMPT = """You are an API documentation analyzer. Your task is to extract ALL API endpoints from the documentation.

TASK: For EVERY endpoint you find, call the record_endpoint tool.

What is an endpoint?
- A URL path that accepts HTTP requests (GET, POST, PUT, DELETE, PATCH, etc.)
- Examples: /users, /api/v1/data, /facts, /breeds/{id}

How to find endpoints:
1. Look for HTTP methods (GET, POST, PUT, DELETE, PATCH) followed by paths
2. Look for URL paths in code examples (curl commands, request examples)
3. In OpenAPI/Swagger JSON: look for the "paths" object - each key is an endpoint
4. Look for endpoint tables or lists in the documentation

Example extractions:
- See "GET /fact" → call record_endpoint(path="/fact", method="get", summary="...")
- See '"paths": {"/breeds": {"get": ...}}' → call record_endpoint(path="/breeds", method="get", ...)
- See "curl https://api.example.com/users" → call record_endpoint(path="/users", method="get", ...)

For each endpoint, extract:
- path: The URL path (required)
- method: The HTTP method (required)
- summary: Brief description of what it does (required)
- parameters: Query params, path params, headers (optional)
- responses: Status codes and descriptions (optional)
- confidence: "high" if you're certain, "medium" if some info missing, "low" if unclear

Documentation:
{documentation}

Now extract ALL endpoints by calling record_endpoint for each one."""

    def __init__(self):
        """Initialize LLM extractor."""
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.cache_manager = get_cache_manager()
        self.auth_detector = AuthDetector()

    def _create_extraction_tools(self) -> List[dict]:
        """Create tools definition for structured output.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "record_endpoint",
                "description": "Record an API endpoint with its complete information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Endpoint path (e.g., /users/{id})",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["get", "post", "put", "delete", "patch", "head", "options"],
                            "description": "HTTP method",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Short summary of what the endpoint does",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description",
                        },
                        "parameters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "location": {
                                        "type": "string",
                                        "enum": ["query", "header", "path", "cookie"],
                                    },
                                    "description": {"type": "string"},
                                    "required": {"type": "boolean"},
                                    "type": {
                                        "type": "string",
                                        "enum": [
                                            "string",
                                            "number",
                                            "integer",
                                            "boolean",
                                            "array",
                                            "object",
                                        ],
                                    },
                                    "example": {"type": "string"},
                                },
                                "required": ["name", "location", "type"],
                            },
                        },
                        "request_body": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "required": {"type": "boolean"},
                                "content_type": {"type": "string"},
                                "example": {"type": "string"},
                                "schema_properties": {
                                    "type": "object",
                                    "description": "JSON object describing the schema properties",
                                },
                            },
                        },
                        "responses": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "status_code": {"type": "string"},
                                    "description": {"type": "string"},
                                    "content_type": {"type": "string"},
                                    "example": {"type": "string"},
                                    "schema_properties": {
                                        "type": "object",
                                        "description": "JSON object describing the schema properties",
                                    },
                                },
                                "required": ["status_code", "description"],
                            },
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Categories or tags for this endpoint",
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Confidence level in the extracted information",
                        },
                    },
                    "required": ["path", "method", "summary"],
                },
            },
            {
                "name": "record_security_scheme",
                "description": "Record an authentication/security scheme used by the API",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["apiKey", "http", "oauth2", "openIdConnect"],
                        },
                        "description": {"type": "string"},
                        "name": {"type": "string"},
                        "location": {
                            "type": "string",
                            "enum": ["query", "header", "cookie"],
                        },
                        "scheme": {"type": "string"},
                        "bearer_format": {"type": "string"},
                    },
                    "required": ["type"],
                },
            },
            {
                "name": "record_api_metadata",
                "description": "Record general API metadata",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "base_url": {"type": "string"},
                        "version": {"type": "string"},
                    },
                },
            },
        ]

    def _try_extract_embedded_openapi(self, content: DocumentContent) -> Optional[ExtractionResult]:
        """Try to extract embedded OpenAPI spec from HTML/JS.

        Args:
            content: Documentation content

        Returns:
            ExtractionResult if successful, None otherwise
        """
        # FIRST: Try parsing the entire content as JSON (for pure JSON spec files)
        if '"openapi"' in content.text and '"paths"' in content.text:
            try:
                spec = json.loads(content.text.strip())
                if isinstance(spec, dict) and "paths" in spec:
                    logger.info(f"Found pure OpenAPI JSON spec in {content.url}")
                    return self._convert_openapi_to_result(spec, content.url)
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse as pure JSON: {e}")
            except Exception as e:
                logger.error(f"Error converting embedded OpenAPI: {e}", exc_info=True)
                return None

        # Look for OpenAPI spec patterns in code samples
        for sample in content.code_samples:
            if '"paths"' in sample and ('"openapi"' in sample or '"swagger"' in sample):
                try:
                    # Try to parse as JSON
                    spec = json.loads(sample)
                    if isinstance(spec, dict) and "paths" in spec:
                        logger.info(
                            f"Found embedded OpenAPI spec in code sample from {content.url}"
                        )
                        return self._convert_openapi_to_result(spec, content.url)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(
                        f"Error converting embedded OpenAPI from sample: {e}", exc_info=True
                    )
                    continue

        return None

    def _convert_openapi_to_result(self, spec: dict, source_url: str) -> ExtractionResult:
        """Convert an embedded OpenAPI spec to ExtractionResult.

        Args:
            spec: OpenAPI spec dictionary
            source_url: Source URL

        Returns:
            ExtractionResult with extracted endpoints
        """
        endpoints = []
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                logger.warning(f"Skipping invalid path entry: {path}")
                continue

            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    # Skip non-dict entries (e.g., $ref, parameters, etc.)
                    continue

                if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                    try:
                        # Extract parameters with error handling
                        parameters = []
                        for param in operation.get("parameters", []):
                            try:
                                if not isinstance(param, dict):
                                    continue

                                # Get parameter type from schema
                                param_type = "string"  # default
                                if "schema" in param and isinstance(param["schema"], dict):
                                    param_type = param["schema"].get("type", "string")
                                elif "type" in param:
                                    param_type = param.get("type", "string")

                                parameters.append(
                                    Parameter(
                                        name=param.get("name", "unknown"),
                                        location=ParameterLocation(param.get("in", "query")),
                                        description=param.get("description"),
                                        required=param.get("required", False),
                                        type=DataType(param_type),
                                    )
                                )
                            except (KeyError, ValueError) as e:
                                logger.warning(
                                    f"Skipping invalid parameter in {method} {path}: {e}"
                                )
                                continue

                        # Extract responses with error handling
                        responses = []
                        for status_code, response_info in operation.get("responses", {}).items():
                            try:
                                if not isinstance(response_info, dict):
                                    continue

                                responses.append(
                                    Response(
                                        status_code=str(status_code),
                                        description=response_info.get("description", ""),
                                    )
                                )
                            except (KeyError, ValueError) as e:
                                logger.warning(
                                    f"Skipping invalid response {status_code} in {method} {path}: {e}"
                                )
                                continue

                        endpoint = Endpoint(
                            path=path,
                            method=HTTPMethod(method.lower()),
                            summary=operation.get("summary", ""),
                            description=operation.get("description"),
                            tags=operation.get("tags", []),
                            parameters=parameters,
                            responses=responses,
                            confidence=ConfidenceLevel.HIGH,
                            source_url=source_url,
                        )
                        endpoints.append(endpoint)
                    except Exception as e:
                        logger.error(
                            f"Failed to parse endpoint {method} {path}: {e}", exc_info=True
                        )
                        continue

        logger.info(f"Converted embedded OpenAPI spec: {len(endpoints)} endpoints")
        return ExtractionResult(
            endpoints=endpoints,
            confidence=ConfidenceLevel.HIGH,
        )

    async def extract(self, content: DocumentContent) -> ExtractionResult:
        """Extract API information from documentation content.

        Args:
            content: Documentation content

        Returns:
            Extraction result
        """
        logger.info(f"Extracting API info from {content.url}")

        # FIRST: Try to detect and parse embedded OpenAPI specs directly
        embedded_result = self._try_extract_embedded_openapi(content)
        if embedded_result and len(embedded_result.endpoints) > 0:
            logger.info(f"Using embedded OpenAPI spec ({len(embedded_result.endpoints)} endpoints)")
            return embedded_result

        # Check cache before LLM extraction
        content_hash = self.cache_manager.get_content_hash(
            content.text[:50000]
        )  # Use first 50K chars for hash
        cached_result = self.cache_manager.get_llm_cache(content_hash)
        if cached_result:
            logger.info(f" Using cached LLM result for {content.url}")
            return cached_result

        # FALLBACK: Use LLM extraction
        logger.info("No embedded OpenAPI found, using LLM extraction...")

        # Prepare documentation text
        doc_text = f"URL: {content.url}\nTitle: {content.title}\n\n{content.text}"

        # Add code samples
        if content.code_samples:
            doc_text += "\n\nCode Samples:\n"
            for i, sample in enumerate(content.code_samples[:10], 1):  # Limit to 10 samples
                doc_text += f"\nSample {i}:\n```\n{sample}\n```\n"

        # Truncate if too long (roughly 150K tokens for safety)
        max_chars = 600000
        if len(doc_text) > max_chars:
            logger.warning(f"Documentation too long ({len(doc_text)} chars), truncating")
            doc_text = doc_text[:max_chars] + "\n\n[... truncated ...]"

        # Call Claude with tools
        try:
            # Use replace instead of format to avoid issues with curly braces in documentation
            prompt = self.EXTRACTION_PROMPT.replace("{documentation}", doc_text)

            response = self.client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=4096,
                tools=self._create_extraction_tools(),
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Parse tool uses into structured data
            result = self._parse_response(response, content.url)

            # Enhance security schemes with pattern-based detection
            result.security_schemes = self.auth_detector.enhance_llm_schemes(
                result.security_schemes, doc_text
            )

            # Cache the result
            self.cache_manager.set_llm_cache(content_hash, result)

            logger.info(
                f"Extracted {len(result.endpoints)} endpoints and {len(result.security_schemes)} auth schemes from {content.url}"
            )
            return result

        except Exception as e:
            logger.error(f"LLM extraction failed for {content.url}: {e}", exc_info=True)
            return ExtractionResult(confidence=ConfidenceLevel.LOW)

    def _parse_response(
        self, response: anthropic.types.Message, source_url: str
    ) -> ExtractionResult:
        """Parse Claude's response into ExtractionResult.

        Args:
            response: Claude's response
            source_url: Source URL

        Returns:
            Parsed extraction result
        """
        endpoints: List[Endpoint] = []
        security_schemes: List[SecurityScheme] = []
        api_title: Optional[str] = None
        api_description: Optional[str] = None
        base_url: Optional[str] = None

        for content_block in response.content:
            if content_block.type == "tool_use":
                if content_block.name == "record_endpoint":
                    endpoint = self._parse_endpoint(content_block.input, source_url)
                    endpoints.append(endpoint)

                elif content_block.name == "record_security_scheme":
                    security_scheme = self._parse_security_scheme(content_block.input)
                    security_schemes.append(security_scheme)

                elif content_block.name == "record_api_metadata":
                    api_title = content_block.input.get("title")
                    api_description = content_block.input.get("description")
                    base_url = content_block.input.get("base_url")

        # Determine overall confidence
        if endpoints:
            confidences = [e.confidence for e in endpoints]
            avg_confidence = confidences.count(ConfidenceLevel.HIGH) / len(confidences)
            if avg_confidence > 0.7:
                overall_confidence = ConfidenceLevel.HIGH
            elif avg_confidence > 0.3:
                overall_confidence = ConfidenceLevel.MEDIUM
            else:
                overall_confidence = ConfidenceLevel.LOW
        else:
            overall_confidence = ConfidenceLevel.LOW

        return ExtractionResult(
            endpoints=endpoints,
            security_schemes=security_schemes,
            base_url=base_url,
            api_title=api_title,
            api_description=api_description,
            confidence=overall_confidence,
        )

    def _parse_endpoint(self, data: dict, source_url: str) -> Endpoint:
        """Parse endpoint data from tool use.

        Args:
            data: Tool use input
            source_url: Source URL

        Returns:
            Endpoint object
        """
        # Parse parameters
        parameters = []
        for param_data in data.get("parameters", []):
            param = Parameter(
                name=param_data["name"],
                location=ParameterLocation(param_data["location"]),
                description=param_data.get("description"),
                required=param_data.get("required", False),
                type=DataType(param_data.get("type", "string")),
                example=param_data.get("example"),
            )
            parameters.append(param)

        # Parse request body
        request_body = None
        if "request_body" in data and data["request_body"]:
            rb_data = data["request_body"]
            schema = None
            if "schema_properties" in rb_data:
                schema = Schema(
                    type=DataType.OBJECT,
                    properties=rb_data["schema_properties"],
                    description=rb_data.get("description"),
                )
            request_body = RequestBody(
                description=rb_data.get("description"),
                required=rb_data.get("required", False),
                content_type=rb_data.get("content_type", "application/json"),
                schema=schema,
                example=rb_data.get("example"),
            )

        # Parse responses
        responses = []
        for resp_data in data.get("responses", []):
            schema = None
            if "schema_properties" in resp_data:
                schema = Schema(
                    type=DataType.OBJECT,
                    properties=resp_data["schema_properties"],
                    description=resp_data.get("description"),
                )
            response = Response(
                status_code=resp_data["status_code"],
                description=resp_data["description"],
                content_type=resp_data.get("content_type", "application/json"),
                schema=schema,
                example=resp_data.get("example"),
            )
            responses.append(response)

        return Endpoint(
            path=data["path"],
            method=HTTPMethod(data["method"]),
            summary=data.get("summary"),
            description=data.get("description"),
            tags=data.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            confidence=ConfidenceLevel(data.get("confidence", "medium")),
            source_url=source_url,
        )

    def _parse_security_scheme(self, data: dict) -> SecurityScheme:
        """Parse security scheme from tool use.

        Args:
            data: Tool use input

        Returns:
            SecurityScheme object
        """
        return SecurityScheme(
            type=data["type"],
            description=data.get("description"),
            name=data.get("name"),
            location=data.get("location"),
            scheme=data.get("scheme"),
            bearer_format=data.get("bearer_format"),
        )
