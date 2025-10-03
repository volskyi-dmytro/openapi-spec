"""OpenAPI specification validator."""

from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class SpecValidator:
    """Validates OpenAPI specifications."""

    def validate(self, spec_dict: dict) -> tuple[bool, list[str]]:
        """Validate OpenAPI specification.

        Args:
            spec_dict: OpenAPI specification as dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        logger.info("Validating OpenAPI specification...")

        errors = []

        try:
            # Validate against OpenAPI schema
            validate(spec_dict)
            logger.info(" Specification is valid!")
            return True, []

        except OpenAPIValidationError as e:
            logger.error(f" Validation failed: {e}")
            errors.append(str(e))

            # Try to extract more detailed errors
            if hasattr(e, "schema_errors"):
                for error in e.schema_errors:
                    errors.append(f"  - {error}")

            return False, errors

        except Exception as e:
            logger.error(f" Unexpected validation error: {e}")
            errors.append(f"Unexpected error: {e}")
            return False, errors

    def validate_with_recommendations(self, spec_dict: dict) -> tuple[bool, list[str], list[str]]:
        """Validate spec and provide recommendations.

        Args:
            spec_dict: OpenAPI specification as dictionary

        Returns:
            Tuple of (is_valid, errors, recommendations)
        """
        is_valid, errors = self.validate(spec_dict)

        recommendations = []

        # Check for common quality issues
        if "paths" in spec_dict:
            paths = spec_dict["paths"]

            # Check if all operations have descriptions
            missing_descriptions = 0
            missing_examples = 0
            total_operations = 0

            for path, methods in paths.items():
                for method, operation in methods.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        total_operations += 1

                        if not operation.get("description"):
                            missing_descriptions += 1

                        # Check for examples in responses
                        responses = operation.get("responses", {})
                        has_example = False
                        for response in responses.values():
                            content = response.get("content", {})
                            for media_type in content.values():
                                if "example" in media_type or "examples" in media_type:
                                    has_example = True
                                    break
                        if not has_example:
                            missing_examples += 1

            if missing_descriptions > 0:
                recommendations.append(
                    f"Consider adding descriptions to "
                    f"{missing_descriptions}/{total_operations} operations"
                )

            if missing_examples > 0:
                recommendations.append(
                    f"Consider adding examples to {missing_examples}/{total_operations} operations"
                )

            # Check for security
            if "security" not in spec_dict and "components" not in spec_dict:
                recommendations.append(
                    "Consider adding security schemes if the API requires authentication"
                )

        return is_valid, errors, recommendations
