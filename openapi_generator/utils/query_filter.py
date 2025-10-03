"""Natural language query filtering for endpoints."""

import re
from typing import List, Tuple

from openapi_generator.models.schemas import Endpoint
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class QueryFilter:
    """Filters endpoints based on natural language queries using keyword matching."""

    # Common keyword mappings
    KEYWORD_MAPPINGS = {
        "payment": ["payment", "pay", "charge", "invoice", "billing", "transaction"],
        "user": ["user", "account", "profile", "customer", "member"],
        "auth": ["auth", "login", "signin", "signup", "register", "token", "session"],
        "product": ["product", "item", "catalog", "inventory", "sku"],
        "order": ["order", "purchase", "cart", "checkout", "basket"],
        "search": ["search", "query", "find", "lookup", "filter"],
        "analytics": ["analytics", "stats", "metrics", "report", "dashboard"],
        "notification": ["notification", "alert", "message", "email", "sms"],
        "file": ["file", "upload", "download", "document", "attachment"],
        "admin": ["admin", "management", "config", "settings", "control"],
    }

    def __init__(self):
        """Initialize query filter."""
        pass

    def filter_endpoints(
        self, endpoints: List[Endpoint], query: str, threshold: float = 0.3
    ) -> List[Tuple[Endpoint, float]]:
        """Filter endpoints based on natural language query.

        Args:
            endpoints: List of endpoints to filter
            query: Natural language query (e.g., "payment endpoints only")
            threshold: Minimum relevance score (0-1) to include endpoint

        Returns:
            List of (endpoint, score) tuples, sorted by relevance
        """
        logger.info(f"Filtering {len(endpoints)} endpoints with query: '{query}'")

        # Extract keywords from query
        keywords = self._extract_keywords(query)
        logger.debug(f"Extracted keywords: {keywords}")

        # Score each endpoint
        scored_endpoints = []
        for endpoint in endpoints:
            score = self._calculate_relevance(endpoint, keywords)
            if score >= threshold:
                scored_endpoints.append((endpoint, score))

        # Sort by score (descending)
        scored_endpoints.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Filtered to {len(scored_endpoints)} endpoints (threshold: {threshold})")

        return scored_endpoints

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from natural language query.

        Args:
            query: Natural language query

        Returns:
            List of extracted keywords
        """
        query_lower = query.lower()

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "only",
            "just",
            "all",
            "show",
            "get",
            "find",
            "list",
            "return",
            "give",
            "me",
            "i",
            "want",
            "need",
            "endpoints",
            "api",
            "spec",
            "specification",
            "generate",
            "create",
        }

        # Split into words
        words = re.findall(r"\b\w+\b", query_lower)

        # Filter stop words and expand with mappings
        keywords = set()
        for word in words:
            if word not in stop_words:
                keywords.add(word)

                # Add related keywords from mappings
                for category, related in self.KEYWORD_MAPPINGS.items():
                    if word in related or word == category:
                        keywords.update(related)

        return list(keywords)

    def _calculate_relevance(self, endpoint: Endpoint, keywords: List[str]) -> float:
        """Calculate relevance score for an endpoint.

        Args:
            endpoint: Endpoint to score
            keywords: List of keywords to match

        Returns:
            Relevance score between 0 and 1
        """
        if not keywords:
            return 1.0  # No filtering, all endpoints relevant

        # Combine endpoint text fields
        text_fields = [
            endpoint.path or "",
            endpoint.summary or "",
            endpoint.description or "",
            " ".join(endpoint.tags or []),
        ]

        combined_text = " ".join(text_fields).lower()

        # Count keyword matches
        matches = 0
        total_keywords = len(keywords)

        for keyword in keywords:
            # Use word boundary for better matching
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                matches += 1

        # Calculate score
        score = matches / total_keywords if total_keywords > 0 else 0.0

        # Boost score if path contains keywords
        path_matches = sum(1 for kw in keywords if kw in (endpoint.path or "").lower())
        if path_matches > 0:
            score = min(1.0, score + 0.2)  # Boost by 20% for path matches

        return score

    def apply_filter(
        self, endpoints: List[Endpoint], query: str, threshold: float = 0.3
    ) -> List[Endpoint]:
        """Apply filter and return only matching endpoints.

        Args:
            endpoints: List of endpoints to filter
            query: Natural language query
            threshold: Minimum relevance score

        Returns:
            List of matching endpoints (without scores)
        """
        scored_endpoints = self.filter_endpoints(endpoints, query, threshold)
        return [endpoint for endpoint, score in scored_endpoints]

    def get_filter_summary(
        self, endpoints: List[Endpoint], query: str, threshold: float = 0.3
    ) -> dict:
        """Get summary of filtering results.

        Args:
            endpoints: List of endpoints to filter
            query: Natural language query
            threshold: Minimum relevance score

        Returns:
            Dictionary with filtering statistics
        """
        scored_endpoints = self.filter_endpoints(endpoints, query, threshold)

        # Calculate statistics
        if scored_endpoints:
            scores = [score for _, score in scored_endpoints]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
        else:
            avg_score = max_score = min_score = 0.0

        return {
            "original_count": len(endpoints),
            "filtered_count": len(scored_endpoints),
            "query": query,
            "threshold": threshold,
            "average_score": avg_score,
            "max_score": max_score,
            "min_score": min_score,
            "top_matches": [
                {
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                    "summary": endpoint.summary,
                    "score": score,
                }
                for endpoint, score in scored_endpoints[:5]
            ],
        }
