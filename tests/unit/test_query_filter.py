"""Unit tests for query filter."""

import pytest

from openapi_generator.models.schemas import Endpoint, HTTPMethod
from openapi_generator.utils.query_filter import QueryFilter


@pytest.fixture
def sample_endpoints():
    """Create sample endpoints for testing."""
    return [
        Endpoint(
            path="/payments",
            method=HTTPMethod.POST,
            summary="Create payment",
            description="Creates a new payment transaction",
            tags=["Payments"],
        ),
        Endpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users",
            description="Get all users",
            tags=["Users"],
        ),
        Endpoint(
            path="/auth/login",
            method=HTTPMethod.POST,
            summary="User login",
            description="Authenticate user and return token",
            tags=["Authentication"],
        ),
        Endpoint(
            path="/products",
            method=HTTPMethod.GET,
            summary="List products",
            description="Get product catalog",
            tags=["Products"],
        ),
    ]


def test_keyword_extraction():
    """Test keyword extraction from query."""
    filter = QueryFilter()

    keywords = filter._extract_keywords("payment endpoints only")
    assert "payment" in keywords

    keywords = filter._extract_keywords("user authentication and login")
    assert "user" in keywords or "authentication" in keywords


def test_filter_payment_endpoints(sample_endpoints):
    """Test filtering for payment endpoints."""
    filter = QueryFilter()

    filtered = filter.apply_filter(sample_endpoints, "payment endpoints", threshold=0.3)

    assert len(filtered) >= 1
    assert any(e.path == "/payments" for e in filtered)


def test_filter_user_endpoints(sample_endpoints):
    """Test filtering for user endpoints."""
    filter = QueryFilter()

    # Use lower threshold since "management" might not match well
    filtered = filter.apply_filter(sample_endpoints, "user", threshold=0.2)

    assert len(filtered) >= 1
    assert any(e.path == "/users" for e in filtered)


def test_filter_auth_endpoints(sample_endpoints):
    """Test filtering for authentication endpoints."""
    filter = QueryFilter()

    filtered = filter.apply_filter(sample_endpoints, "authentication login", threshold=0.3)

    assert len(filtered) >= 1
    assert any(e.path == "/auth/login" for e in filtered)


def test_no_filter_returns_all(sample_endpoints):
    """Test that empty query returns all endpoints."""
    filter = QueryFilter()

    filtered = filter.apply_filter(sample_endpoints, "", threshold=0.3)

    assert len(filtered) == len(sample_endpoints)


def test_relevance_scoring(sample_endpoints):
    """Test relevance scoring."""
    filter = QueryFilter()

    scored = filter.filter_endpoints(sample_endpoints, "payment", threshold=0.0)

    # Payment endpoint should have highest score
    payment_score = next((score for ep, score in scored if ep.path == "/payments"), 0)
    other_scores = [score for ep, score in scored if ep.path != "/payments"]

    assert payment_score > 0
    if other_scores:
        assert payment_score >= max(other_scores)


def test_filter_summary(sample_endpoints):
    """Test filter summary generation."""
    filter = QueryFilter()

    summary = filter.get_filter_summary(sample_endpoints, "payment", threshold=0.3)

    assert "original_count" in summary
    assert "filtered_count" in summary
    assert "query" in summary
    assert summary["original_count"] == len(sample_endpoints)
    assert summary["filtered_count"] <= len(sample_endpoints)


def test_path_matching_boost(sample_endpoints):
    """Test that path matches get boosted."""
    filter = QueryFilter()

    # Create endpoint with keyword in path
    payment_in_path = Endpoint(
        path="/api/payment/new",
        method=HTTPMethod.POST,
        summary="Something else",
        description="No payment keyword here",
    )

    payment_in_description = Endpoint(
        path="/api/create",
        method=HTTPMethod.POST,
        summary="Create payment",
        description="Creates a payment",
    )

    endpoints = [payment_in_path, payment_in_description]
    scored = filter.filter_endpoints(endpoints, "payment", threshold=0.0)

    # Path match should have higher or equal score
    path_score = next((score for ep, score in scored if ep.path == "/api/payment/new"), 0)
    desc_score = next((score for ep, score in scored if ep.path == "/api/create"), 0)

    assert path_score >= desc_score


def test_high_threshold_filters_more(sample_endpoints):
    """Test that higher threshold filters more endpoints."""
    filter = QueryFilter()

    low_threshold = filter.apply_filter(sample_endpoints, "user", threshold=0.1)
    high_threshold = filter.apply_filter(sample_endpoints, "user", threshold=0.8)

    assert len(low_threshold) >= len(high_threshold)
