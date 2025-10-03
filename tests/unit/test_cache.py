"""Unit tests for cache manager."""

import pytest

from openapi_generator.models.schemas import (
    ConfidenceLevel,
    Endpoint,
    ExtractionResult,
    HTTPMethod,
)
from openapi_generator.utils.cache import CacheManager


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    return tmp_path / "cache"


@pytest.fixture
def cache_manager(temp_cache_dir, monkeypatch):
    """Create cache manager with temp directory."""

    # Mock get_settings to avoid requiring API key
    class MockSettings:
        cache_dir = temp_cache_dir
        cache_ttl = 3600
        enable_http_cache = True
        enable_llm_cache = True

    def mock_get_settings():
        return MockSettings()

    monkeypatch.setattr("openapi_generator.utils.cache.get_settings", mock_get_settings)

    cache = CacheManager()
    cache.http_cache_dir.mkdir(parents=True, exist_ok=True)
    cache.llm_cache_dir.mkdir(parents=True, exist_ok=True)

    return cache


def test_cache_key_generation(cache_manager):
    """Test cache key generation."""
    key1 = cache_manager.get_content_hash("test content")
    key2 = cache_manager.get_content_hash("test content")
    key3 = cache_manager.get_content_hash("different content")

    assert key1 == key2
    assert key1 != key3
    assert len(key1) == 32  # MD5 hash length


def test_http_cache_set_get(cache_manager):
    """Test HTTP cache set and get."""
    url = "https://example.com/api"
    content = "<html>test content</html>"

    # Set cache
    cache_manager.set_http_cache(url, content)

    # Get cache
    cached = cache_manager.get_http_cache(url)
    assert cached == content


def test_http_cache_miss(cache_manager):
    """Test HTTP cache miss."""
    cached = cache_manager.get_http_cache("https://nonexistent.com")
    assert cached is None


def test_llm_cache_set_get(cache_manager):
    """Test LLM cache set and get."""
    content_hash = "test_hash_123"
    result = ExtractionResult(
        endpoints=[
            Endpoint(
                path="/test",
                method=HTTPMethod.GET,
                summary="Test endpoint",
            )
        ],
        confidence=ConfidenceLevel.HIGH,
    )

    # Set cache
    cache_manager.set_llm_cache(content_hash, result)

    # Get cache
    cached = cache_manager.get_llm_cache(content_hash)
    assert cached is not None
    assert len(cached.endpoints) == 1
    assert cached.endpoints[0].path == "/test"


def test_llm_cache_miss(cache_manager):
    """Test LLM cache miss."""
    cached = cache_manager.get_llm_cache("nonexistent_hash")
    assert cached is None


def test_cache_stats(cache_manager):
    """Test cache statistics."""
    # Add some cache entries
    cache_manager.set_http_cache("https://test1.com", "content1")
    cache_manager.set_http_cache("https://test2.com", "content2")

    result = ExtractionResult(confidence=ConfidenceLevel.HIGH)
    cache_manager.set_llm_cache("hash1", result)

    # Get stats
    stats = cache_manager.get_cache_stats()

    assert stats["http_cache_enabled"] is True
    assert stats["llm_cache_enabled"] is True
    assert stats["http_cache_count"] == 2
    assert stats["llm_cache_count"] == 1
    assert stats["total_size_mb"] > 0


def test_clear_cache(cache_manager):
    """Test cache clearing."""
    # Add some cache entries
    cache_manager.set_http_cache("https://test.com", "content")
    result = ExtractionResult(confidence=ConfidenceLevel.HIGH)
    cache_manager.set_llm_cache("hash", result)

    # Clear HTTP cache
    deleted = cache_manager.clear_cache("http")
    assert deleted >= 1

    # Check HTTP cache is cleared
    assert cache_manager.get_http_cache("https://test.com") is None

    # LLM cache should still exist
    assert cache_manager.get_llm_cache("hash") is not None

    # Clear all
    cache_manager.set_http_cache("https://test2.com", "content2")
    deleted = cache_manager.clear_cache()
    assert deleted >= 2
