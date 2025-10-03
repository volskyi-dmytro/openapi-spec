"""Caching utilities for HTTP responses and LLM results."""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Optional

from openapi_generator.config import get_settings
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages caching for HTTP responses and LLM results."""

    def __init__(self):
        """Initialize cache manager."""
        self.settings = get_settings()
        self.cache_dir = self.settings.cache_dir
        self.ttl = self.settings.cache_ttl

        # Create cache directories
        self.http_cache_dir = self.cache_dir / "http"
        self.llm_cache_dir = self.cache_dir / "llm"

        if self.settings.enable_http_cache:
            self.http_cache_dir.mkdir(parents=True, exist_ok=True)
        if self.settings.enable_llm_cache:
            self.llm_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, data: str) -> str:
        """Generate cache key from data.

        Args:
            data: Data to generate key for

        Returns:
            MD5 hash of data
        """
        return hashlib.md5(data.encode()).hexdigest()

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid.

        Args:
            cache_file: Path to cache file

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_file.exists():
            return False

        # Check if cache is expired
        age = time.time() - cache_file.stat().st_mtime
        if age > self.ttl:
            logger.debug(f"Cache expired: {cache_file.name} (age: {age:.0f}s)")
            return False

        return True

    def get_http_cache(self, url: str) -> Optional[str]:
        """Get cached HTTP response.

        Args:
            url: URL to get cache for

        Returns:
            Cached response content or None
        """
        if not self.settings.enable_http_cache:
            return None

        cache_key = self._get_cache_key(url)
        cache_file = self.http_cache_dir / f"{cache_key}.txt"

        if self._is_cache_valid(cache_file):
            logger.debug(f"HTTP cache hit: {url}")
            return cache_file.read_text(encoding="utf-8")

        return None

    def set_http_cache(self, url: str, content: str) -> None:
        """Cache HTTP response.

        Args:
            url: URL to cache
            content: Response content to cache
        """
        if not self.settings.enable_http_cache:
            return

        cache_key = self._get_cache_key(url)
        cache_file = self.http_cache_dir / f"{cache_key}.txt"

        cache_file.write_text(content, encoding="utf-8")
        logger.debug(f"HTTP cache set: {url}")

    def get_llm_cache(self, content_hash: str) -> Optional[Any]:
        """Get cached LLM extraction result.

        Args:
            content_hash: Hash of content that was extracted

        Returns:
            Cached ExtractionResult or None
        """
        if not self.settings.enable_llm_cache:
            return None

        cache_file = self.llm_cache_dir / f"{content_hash}.pkl"

        if self._is_cache_valid(cache_file):
            logger.debug(f"LLM cache hit: {content_hash[:8]}")
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load LLM cache: {e}")
                return None

        return None

    def set_llm_cache(self, content_hash: str, result: Any) -> None:
        """Cache LLM extraction result.

        Args:
            content_hash: Hash of content that was extracted
            result: ExtractionResult to cache
        """
        if not self.settings.enable_llm_cache:
            return

        cache_file = self.llm_cache_dir / f"{content_hash}.pkl"

        try:
            with open(cache_file, "wb") as f:
                pickle.dump(result, f)
            logger.debug(f"LLM cache set: {content_hash[:8]}")
        except Exception as e:
            logger.warning(f"Failed to save LLM cache: {e}")

    def get_content_hash(self, content: str) -> str:
        """Get hash of content for cache key.

        Args:
            content: Content to hash

        Returns:
            MD5 hash of content
        """
        return self._get_cache_key(content)

    def clear_cache(self, cache_type: Optional[str] = None) -> int:
        """Clear cache.

        Args:
            cache_type: Type of cache to clear ('http', 'llm', or None for all)

        Returns:
            Number of files deleted
        """
        deleted = 0

        if cache_type in (None, "http"):
            for cache_file in self.http_cache_dir.glob("*.txt"):
                cache_file.unlink()
                deleted += 1
            logger.info(f"Cleared {deleted} HTTP cache files")

        if cache_type in (None, "llm"):
            llm_deleted = 0
            for cache_file in self.llm_cache_dir.glob("*.pkl"):
                cache_file.unlink()
                llm_deleted += 1
            deleted += llm_deleted
            logger.info(f"Cleared {llm_deleted} LLM cache files")

        return deleted

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        http_count = (
            len(list(self.http_cache_dir.glob("*.txt"))) if self.http_cache_dir.exists() else 0
        )
        llm_count = (
            len(list(self.llm_cache_dir.glob("*.pkl"))) if self.llm_cache_dir.exists() else 0
        )

        # Calculate total size
        http_size = (
            sum(f.stat().st_size for f in self.http_cache_dir.glob("*.txt"))
            if self.http_cache_dir.exists()
            else 0
        )
        llm_size = (
            sum(f.stat().st_size for f in self.llm_cache_dir.glob("*.pkl"))
            if self.llm_cache_dir.exists()
            else 0
        )

        return {
            "http_cache_enabled": self.settings.enable_http_cache,
            "llm_cache_enabled": self.settings.enable_llm_cache,
            "http_cache_count": http_count,
            "llm_cache_count": llm_count,
            "http_cache_size_mb": http_size / (1024 * 1024),
            "llm_cache_size_mb": llm_size / (1024 * 1024),
            "total_size_mb": (http_size + llm_size) / (1024 * 1024),
            "cache_ttl_hours": self.ttl / 3600,
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance (singleton pattern)."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
