"""Enhanced authentication detection using patterns and heuristics."""

import re
from typing import List, Optional

from openapi_generator.models.schemas import SecurityScheme
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class AuthDetector:
    """Detects authentication schemes from documentation text using patterns."""

    # Common auth patterns
    AUTH_PATTERNS = {
        "api_key_header": [
            r"api[_\s-]?key.{0,50}header",
            r"x-api-key",
            r"authorization.{0,30}api[_\s-]?key",
            r"include.{0,30}api[_\s-]?key.{0,30}header",
        ],
        "api_key_query": [
            r"api[_\s-]?key.{0,50}query.{0,20}parameter",
            r"api[_\s-]?key.{0,50}url",
            r"\?api[_\s-]?key=",
        ],
        "bearer_token": [
            r"bearer\s+token",
            r"authorization:\s*bearer",
            r"bearer.{0,30}authentication",
            r"jwt.{0,30}bearer",
        ],
        "basic_auth": [
            r"basic\s+auth",
            r"authorization:\s*basic",
            r"username.{0,30}password.{0,30}base64",
        ],
        "oauth2": [
            r"oauth\s*2\.0",
            r"oauth2",
            r"authorization.{0,30}code.{0,30}flow",
            r"client.{0,30}credentials.{0,30}flow",
            r"access.{0,30}token.{0,30}endpoint",
        ],
    }

    # OAuth2 flow detection patterns
    OAUTH2_FLOW_PATTERNS = {
        "authorization_code": [
            r"authorization.{0,20}code",
            r"three.{0,10}legged",
            r"redirect.{0,20}uri",
        ],
        "client_credentials": [
            r"client.{0,20}credentials",
            r"machine.{0,20}to.{0,20}machine",
            r"two.{0,10}legged",
        ],
        "password": [
            r"resource.{0,20}owner.{0,20}password",
            r"password.{0,20}flow",
            r"username.{0,20}password.{0,20}grant",
        ],
        "implicit": [
            r"implicit.{0,20}flow",
            r"implicit.{0,20}grant",
        ],
    }

    def detect_auth_schemes(self, text: str) -> List[SecurityScheme]:
        """Detect authentication schemes from documentation text.

        Args:
            text: Documentation text to analyze

        Returns:
            List of detected SecurityScheme objects
        """
        text_lower = text.lower()
        detected_schemes = []

        # Check for API key in header
        if self._matches_any_pattern(text_lower, self.AUTH_PATTERNS["api_key_header"]):
            logger.info("Detected API Key (header) authentication")

            # Try to extract header name
            header_name = self._extract_header_name(text) or "X-API-Key"

            detected_schemes.append(
                SecurityScheme(
                    type="apiKey",
                    name=header_name,
                    location="header",
                    description="API key authentication via header",
                )
            )

        # Check for API key in query
        if self._matches_any_pattern(text_lower, self.AUTH_PATTERNS["api_key_query"]):
            logger.info("Detected API Key (query) authentication")

            detected_schemes.append(
                SecurityScheme(
                    type="apiKey",
                    name="api_key",
                    location="query",
                    description="API key authentication via query parameter",
                )
            )

        # Check for Bearer token
        if self._matches_any_pattern(text_lower, self.AUTH_PATTERNS["bearer_token"]):
            logger.info("Detected Bearer token authentication")

            # Check if it's JWT
            is_jwt = "jwt" in text_lower or "json web token" in text_lower
            bearer_format = "JWT" if is_jwt else None

            detected_schemes.append(
                SecurityScheme(
                    type="http",
                    scheme="bearer",
                    bearer_format=bearer_format,
                    description="Bearer token authentication" + (" (JWT)" if is_jwt else ""),
                )
            )

        # Check for Basic auth
        if self._matches_any_pattern(text_lower, self.AUTH_PATTERNS["basic_auth"]):
            logger.info("Detected Basic authentication")

            detected_schemes.append(
                SecurityScheme(
                    type="http",
                    scheme="basic",
                    description="HTTP Basic authentication",
                )
            )

        # Check for OAuth2
        if self._matches_any_pattern(text_lower, self.AUTH_PATTERNS["oauth2"]):
            logger.info("Detected OAuth2 authentication")

            # Try to detect OAuth2 flows
            flows = self._detect_oauth2_flows(text_lower)
            flow_desc = f"OAuth 2.0 ({', '.join(flows)})" if flows else "OAuth 2.0"

            detected_schemes.append(
                SecurityScheme(
                    type="oauth2",
                    description=flow_desc,
                )
            )

        return detected_schemes

    def _matches_any_pattern(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given patterns.

        Args:
            text: Text to check
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_header_name(self, text: str) -> Optional[str]:
        """Try to extract API key header name from text.

        Args:
            text: Text to extract from

        Returns:
            Header name or None
        """
        # Common patterns for header names
        patterns = [
            r"(?:header|include).{0,30}['\"`]([xX]-[aA][pP][iI]-[kK]ey)['\"`]",
            r"(?:header|include).{0,30}['\"`]([aA]uthorization)['\"`]",
            r"(?:header|include).{0,30}['\"`]([xX]-[aA][uU][tT][hH]-[tT]oken)['\"`]",
            r"['\"`]([xX]-[^'\"` ]+)['\"`].{0,30}header",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _detect_oauth2_flows(self, text: str) -> List[str]:
        """Detect OAuth2 flows mentioned in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected flow types
        """
        flows = []

        for flow_type, patterns in self.OAUTH2_FLOW_PATTERNS.items():
            if self._matches_any_pattern(text, patterns):
                flows.append(flow_type)

        return flows

    def enhance_llm_schemes(
        self, llm_schemes: List[SecurityScheme], text: str
    ) -> List[SecurityScheme]:
        """Enhance LLM-extracted schemes with pattern-based detection.

        Args:
            llm_schemes: SecuritySchemes extracted by LLM
            text: Documentation text

        Returns:
            Enhanced list of security schemes
        """
        # Get pattern-detected schemes
        pattern_schemes = self.detect_auth_schemes(text)

        # Merge schemes (prefer LLM schemes, add pattern-detected ones if not present)
        enhanced_schemes = list(llm_schemes)

        for pattern_scheme in pattern_schemes:
            # Check if similar scheme already exists
            if not self._scheme_exists(pattern_scheme, enhanced_schemes):
                logger.info(f"Adding pattern-detected auth: {pattern_scheme.type}")
                enhanced_schemes.append(pattern_scheme)

        return enhanced_schemes

    def _scheme_exists(
        self, scheme: SecurityScheme, schemes: List[SecurityScheme]
    ) -> bool:
        """Check if a similar scheme already exists in the list.

        Args:
            scheme: Scheme to check
            schemes: List of existing schemes

        Returns:
            True if similar scheme exists
        """
        for existing in schemes:
            # Same type
            if existing.type != scheme.type:
                continue

            # For apiKey, check location
            if scheme.type == "apiKey":
                if existing.location == scheme.location:
                    return True

            # For http, check scheme
            elif scheme.type == "http":
                if existing.scheme == scheme.scheme:
                    return True

            # For oauth2 or openIdConnect
            elif scheme.type in ["oauth2", "openIdConnect"]:
                return True

        return False
