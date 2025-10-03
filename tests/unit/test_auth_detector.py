"""Unit tests for auth detector."""

import pytest

from openapi_generator.extractors.auth_detector import AuthDetector
from openapi_generator.models.schemas import SecurityScheme


def test_detect_api_key_header():
    """Test detection of API key in header."""
    detector = AuthDetector()

    text = """
    Authentication is done via API key in the header.
    Include your API key in the X-API-Key header with each request.
    """

    schemes = detector.detect_auth_schemes(text)

    assert len(schemes) > 0
    assert any(s.type == "apiKey" and s.location == "header" for s in schemes)


def test_detect_api_key_query():
    """Test detection of API key in query parameter."""
    detector = AuthDetector()

    text = """
    Pass your API key as a URL query parameter: ?api_key=your_key_here
    """

    schemes = detector.detect_auth_schemes(text)

    assert len(schemes) > 0
    assert any(s.type == "apiKey" and s.location == "query" for s in schemes)


def test_detect_bearer_token():
    """Test detection of Bearer token authentication."""
    detector = AuthDetector()

    text = """
    Use Bearer token authentication.
    Include the token in the Authorization header:
    Authorization: Bearer your_token_here
    """

    schemes = detector.detect_auth_schemes(text)

    assert len(schemes) > 0
    assert any(s.type == "http" and s.scheme == "bearer" for s in schemes)


def test_detect_jwt():
    """Test detection of JWT authentication."""
    detector = AuthDetector()

    text = """
    We use JWT (JSON Web Token) for authentication.
    Send your JWT as a Bearer token in the Authorization header.
    """

    schemes = detector.detect_auth_schemes(text)

    assert len(schemes) > 0
    bearer_scheme = next((s for s in schemes if s.type == "http" and s.scheme == "bearer"), None)
    assert bearer_scheme is not None
    assert bearer_scheme.bearer_format == "JWT"


def test_detect_basic_auth():
    """Test detection of Basic authentication."""
    detector = AuthDetector()

    text = """
    This API uses HTTP Basic Authentication.
    Encode your username and password in base64 and send in the Authorization header.
    """

    schemes = detector.detect_auth_schemes(text)

    assert len(schemes) > 0
    assert any(s.type == "http" and s.scheme == "basic" for s in schemes)


def test_detect_oauth2():
    """Test detection of OAuth2."""
    detector = AuthDetector()

    text = """
    We support OAuth 2.0 authentication.
    Use the authorization code flow to obtain an access token.
    """

    schemes = detector.detect_auth_schemes(text)

    assert len(schemes) > 0
    assert any(s.type == "oauth2" for s in schemes)


def test_extract_header_name():
    """Test extraction of header name."""
    detector = AuthDetector()

    text = 'Include your key in the "X-API-Key" header'
    header_name = detector._extract_header_name(text)

    assert header_name == "X-API-Key" or header_name == "x-API-Key"


def test_detect_oauth2_flows():
    """Test OAuth2 flow detection."""
    detector = AuthDetector()

    text_auth_code = "Use the authorization code flow"
    flows = detector._detect_oauth2_flows(text_auth_code)
    assert "authorization_code" in flows

    text_client_creds = "Client credentials flow for machine-to-machine"
    flows = detector._detect_oauth2_flows(text_client_creds)
    assert "client_credentials" in flows


def test_enhance_llm_schemes():
    """Test enhancing LLM schemes with pattern detection."""
    detector = AuthDetector()

    # LLM found Bearer token
    llm_schemes = [
        SecurityScheme(
            type="http",
            scheme="bearer",
            description="Bearer token",
        )
    ]

    text = """
    Authentication:
    1. API Key in X-API-Key header
    2. Bearer token (JWT)
    """

    enhanced = detector.enhance_llm_schemes(llm_schemes, text)

    # Should have both Bearer (from LLM) and API Key (from pattern)
    assert len(enhanced) >= 2
    assert any(s.type == "http" and s.scheme == "bearer" for s in enhanced)
    assert any(s.type == "apiKey" for s in enhanced)


def test_no_duplicate_schemes():
    """Test that duplicate schemes are not added."""
    detector = AuthDetector()

    # LLM already found API key
    llm_schemes = [
        SecurityScheme(
            type="apiKey",
            name="X-API-Key",
            location="header",
        )
    ]

    text = "Use API key in header"

    enhanced = detector.enhance_llm_schemes(llm_schemes, text)

    # Should not add duplicate
    api_key_schemes = [s for s in enhanced if s.type == "apiKey" and s.location == "header"]
    assert len(api_key_schemes) == 1


def test_multiple_auth_types():
    """Test detection of multiple authentication types."""
    detector = AuthDetector()

    text = """
    We support multiple authentication methods:
    1. API Key in query parameter
    2. Bearer token in Authorization header
    3. Basic Authentication
    4. OAuth 2.0
    """

    schemes = detector.detect_auth_schemes(text)

    # Should detect all types
    assert len(schemes) >= 4
    types = [s.type for s in schemes]
    assert "apiKey" in types
    assert "http" in types
    assert "oauth2" in types
