"""OpenAPI specification builder."""

import json
import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

import yaml

from openapi_generator.models.schemas import (
    Endpoint,
    ExtractionResult,
    OpenAPIInfo,
    OpenAPISpec,
    Server,
)
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAPIBuilder:
    """Builds OpenAPI 3.0 specification from extraction results."""

    def __init__(self, base_url: str):
        """Initialize builder.

        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.endpoints: list[Endpoint] = []
        self.security_schemes: list[Any] = []
        self.api_title: str | None = None
        self.api_description: str | None = None
        self.detected_base_url: str | None = None

    def add_extraction_results(self, results: list[ExtractionResult]) -> None:
        """Add extraction results to the builder.

        Args:
            results: List of extraction results
        """
        for result in results:
            self.endpoints.extend(result.endpoints)
            self.security_schemes.extend(result.security_schemes)

            # Use first non-None metadata
            if not self.api_title and result.api_title:
                self.api_title = result.api_title
            if not self.api_description and result.api_description:
                self.api_description = result.api_description
            if not self.detected_base_url and result.base_url:
                self.detected_base_url = result.base_url

    def build(self) -> OpenAPISpec:
        """Build OpenAPI specification.

        Returns:
            Complete OpenAPI specification
        """
        logger.info(f"Building OpenAPI spec with {len(self.endpoints)} endpoints")

        # Deduplicate endpoints
        unique_endpoints = self._deduplicate_endpoints()
        logger.info(f"After deduplication: {len(unique_endpoints)} unique endpoints")

        # Generate info section
        info = self._build_info()

        # Generate servers section
        servers = self._build_servers()

        # Generate paths section
        paths = self._build_paths(unique_endpoints)

        # Generate components section
        components = self._build_components()

        # Generate tags
        tags = self._build_tags(unique_endpoints)

        spec = OpenAPISpec(
            openapi="3.0.3",
            info=info,
            servers=servers,
            paths=paths,
            components=components,
            tags=tags,
        )

        logger.info("OpenAPI spec built successfully")
        return spec

    def _deduplicate_endpoints(self) -> list[Endpoint]:
        """Remove duplicate endpoints based on path and method.

        Returns:
            List of unique endpoints
        """
        # Map confidence levels to numeric values for comparison
        confidence_scores = {
            "high": 3,
            "medium": 2,
            "low": 1,
        }

        seen = {}
        unique = []

        for endpoint in self.endpoints:
            key = (endpoint.path, endpoint.method.value)

            if key not in seen:
                seen[key] = endpoint
                unique.append(endpoint)
            else:
                # If we've seen this before, keep the one with higher confidence
                current_score = confidence_scores.get(endpoint.confidence.value, 0)
                existing_score = confidence_scores.get(seen[key].confidence.value, 0)

                if current_score > existing_score:
                    # Remove old one and add new one
                    unique.remove(seen[key])
                    seen[key] = endpoint
                    unique.append(endpoint)

        return unique

    def _build_info(self) -> OpenAPIInfo:
        """Build info section.

        Returns:
            OpenAPI info object
        """
        # Generate title from base URL if not provided
        if not self.api_title:
            domain = urlparse(self.base_url).netloc
            self.api_title = f"{domain} API"

        return OpenAPIInfo(
            title=self.api_title,
            version="1.0.0",
            description=self.api_description or f"API specification generated from {self.base_url}",
        )

    def _build_servers(self) -> list[Server]:
        """Build servers section.

        Returns:
            List of server objects
        """
        server_url = self.detected_base_url or self.base_url

        # Normalize server URL
        if not server_url.startswith(("http://", "https://")):
            server_url = f"https://{server_url}"

        return [Server(url=server_url, description="API server")]

    def _build_paths(self, endpoints: list[Endpoint]) -> dict[str, dict[str, Any]]:
        """Build paths section.

        Args:
            endpoints: List of unique endpoints

        Returns:
            Paths dictionary
        """
        paths: dict[str, dict[str, Any]] = defaultdict(dict)

        for endpoint in endpoints:
            # Normalize path
            path = endpoint.path
            if not path.startswith("/"):
                path = f"/{path}"

            # Build operation object
            operation = self._build_operation(endpoint)

            # Add to paths
            paths[path][endpoint.method.value] = operation

        return dict(paths)

    def _build_operation(self, endpoint: Endpoint) -> dict[str, Any]:
        """Build operation object for an endpoint.

        Args:
            endpoint: Endpoint data

        Returns:
            Operation dictionary
        """
        operation: dict[str, Any] = {}

        # Basic info
        if endpoint.summary:
            operation["summary"] = endpoint.summary
        if endpoint.description:
            operation["description"] = endpoint.description
        if endpoint.operation_id:
            operation["operationId"] = endpoint.operation_id
        else:
            # Generate operation ID
            operation["operationId"] = self._generate_operation_id(endpoint)

        # Tags
        if endpoint.tags:
            operation["tags"] = endpoint.tags

        # Parameters
        if endpoint.parameters:
            operation["parameters"] = [
                self._build_parameter(param) for param in endpoint.parameters
            ]

        # Request body
        if endpoint.request_body:
            operation["requestBody"] = {
                "description": endpoint.request_body.description or "",
                "required": endpoint.request_body.required,
                "content": {
                    endpoint.request_body.content_type: {
                        "schema": (
                            self._build_schema_dict(endpoint.request_body.schema_)
                            if endpoint.request_body.schema_
                            else {"type": "object"}
                        ),
                    }
                },
            }

            # Add example if available
            if endpoint.request_body.example:
                operation["requestBody"]["content"][endpoint.request_body.content_type][
                    "example"
                ] = endpoint.request_body.example

        # Responses
        operation["responses"] = {}
        if endpoint.responses:
            for response in endpoint.responses:
                operation["responses"][response.status_code] = {
                    "description": response.description,
                }

                if response.schema_:
                    operation["responses"][response.status_code]["content"] = {
                        response.content_type: {"schema": self._build_schema_dict(response.schema_)}
                    }

                    # Add example if available
                    if response.example:
                        operation["responses"][response.status_code]["content"][
                            response.content_type
                        ]["example"] = response.example
        else:
            # Default response
            operation["responses"]["200"] = {
                "description": "Successful response",
                "content": {"application/json": {"schema": {"type": "object"}}},
            }

        # Deprecated flag
        if endpoint.deprecated:
            operation["deprecated"] = True

        return operation

    def _build_parameter(self, param: Any) -> dict[str, Any]:
        """Build parameter object.

        Args:
            param: Parameter data

        Returns:
            Parameter dictionary
        """
        param_dict = {
            "name": param.name,
            "in": param.location.value,
            "required": param.required,
            "schema": {"type": param.type.value},
        }

        if param.description:
            param_dict["description"] = param.description

        if param.example:
            param_dict["example"] = param.example

        return param_dict

    def _build_schema_dict(self, schema: Any) -> dict[str, Any]:
        """Build schema dictionary.

        Args:
            schema: Schema object

        Returns:
            Schema dictionary
        """
        if not schema:
            return {"type": "object"}

        schema_dict = {"type": schema.type.value}

        if schema.description:
            schema_dict["description"] = schema.description

        if schema.properties:
            schema_dict["properties"] = schema.properties

        if schema.items:
            schema_dict["items"] = schema.items

        if schema.required:
            schema_dict["required"] = schema.required

        if schema.example:
            schema_dict["example"] = schema.example

        if schema.additional_properties is not None:
            schema_dict["additionalProperties"] = schema.additional_properties

        return schema_dict

    def _build_components(self) -> dict[str, Any] | None:
        """Build components section.

        Returns:
            Components dictionary
        """
        components: dict[str, Any] = {}

        # Add security schemes if any
        if self.security_schemes:
            components["securitySchemes"] = {}
            for i, scheme in enumerate(self.security_schemes, 1):
                scheme_name = f"security_{i}"
                scheme_dict = {"type": scheme.type}

                if scheme.description:
                    scheme_dict["description"] = scheme.description
                if scheme.name:
                    scheme_dict["name"] = scheme.name
                if scheme.location:
                    scheme_dict["in"] = scheme.location
                if scheme.scheme:
                    scheme_dict["scheme"] = scheme.scheme
                if scheme.bearer_format:
                    scheme_dict["bearerFormat"] = scheme.bearer_format

                components["securitySchemes"][scheme_name] = scheme_dict

        return components if components else None

    def _build_tags(self, endpoints: list[Endpoint]) -> list[dict[str, str]] | None:
        """Build tags section.

        Args:
            endpoints: List of endpoints

        Returns:
            List of tag dictionaries
        """
        tag_set = set()
        for endpoint in endpoints:
            tag_set.update(endpoint.tags or [])

        if not tag_set:
            return None

        return [{"name": tag, "description": f"{tag} endpoints"} for tag in sorted(tag_set)]

    def _generate_operation_id(self, endpoint: Endpoint) -> str:
        """Generate operation ID for an endpoint.

        Args:
            endpoint: Endpoint data

        Returns:
            Generated operation ID
        """
        # Clean path to create operation ID
        path = endpoint.path.strip("/")
        path = re.sub(r"\{.*?\}", "by_id", path)  # Replace path params
        path = re.sub(r"[^a-zA-Z0-9]+", "_", path)  # Replace special chars

        return f"{endpoint.method.value}_{path}".lower()

    def to_json(self, spec: OpenAPISpec, indent: int = 2) -> str:
        """Convert spec to JSON string.

        Args:
            spec: OpenAPI specification
            indent: Indentation level

        Returns:
            JSON string
        """
        return json.dumps(spec.model_dump(by_alias=True, exclude_none=True), indent=indent)

    def to_yaml(self, spec: OpenAPISpec) -> str:
        """Convert spec to YAML string.

        Args:
            spec: OpenAPI specification

        Returns:
            YAML string
        """
        return yaml.dump(
            spec.model_dump(by_alias=True, exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
        )
