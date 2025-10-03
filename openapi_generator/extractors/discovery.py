"""Documentation discovery system for finding API documentation pages."""

import asyncio
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from openapi_generator.config import get_settings
from openapi_generator.utils.logger import get_logger
from openapi_generator.utils.robots import RobotsChecker

logger = get_logger(__name__)


class DocumentationDiscovery:
    """Discovers API documentation pages from a base URL."""

    # Common documentation paths to try
    COMMON_PATHS = [
        "/api/docs",
        "/api-docs",
        "/api/documentation",
        "/docs",
        "/docs/api",
        "/documentation",
        "/documentation/api",
        "/developers",
        "/developer",
        "/dev/docs",
        "/reference",
        "/api-reference",
        "/api/reference",
        "/guides/api",
        "/v1/docs",
        "/v2/docs",
        "/api/v1/docs",
        "/api/v2/docs",
        # NEW: Guide/tutorial paths
        "/guide",
        "/guides",
        "/tutorial",
        "/tutorials",
        "/getting-started",
        "/quickstart",
        "/quick-start",
        "/how-to",
        "/api-guide",
        "/rest-api",
        "/graphql",
        "/resources",
        "/help",
        "/support/api",
    ]

    # Patterns that suggest a URL is API documentation
    API_DOC_PATTERNS = [
        # Standard documentation paths
        r"/api",
        r"/docs?",  # Matches /doc and /docs
        r"/documentation",
        r"/reference",
        r"/api.?reference",  # Matches /api-reference, /apireference, /api_reference
        # Developer-focused paths
        r"/developer",
        r"/developers",
        # Guide/tutorial paths
        r"/guides?",  # Matches /guide and /guides
        r"/tutorials?",  # Matches /tutorial and /tutorials
        r"/getting.?started",  # Matches /getting-started, /gettingstarted
        r"/quick.?start",  # Matches /quickstart, /quick-start
        r"/how.?to",  # Matches /how-to, /howto
        # Resource paths
        r"/resources",
        r"/help",
        r"/support/api",
        r"/knowledge.?base",
        # Technical keywords
        r"endpoint",
        r"authentication",
        r"authorization",
        r"/rest",
        r"/graphql",
        r"/webhook",
    ]

    def __init__(self, base_url: str):
        """Initialize discovery system.

        Args:
            base_url: Base URL to start discovery from (e.g., "https://api.example.com")
        """
        self.base_url = base_url.rstrip("/")
        self.settings = get_settings()
        self.visited_urls: set[str] = set()
        self.doc_urls: set[str] = set()
        self.robots_checker = RobotsChecker(base_url)

    async def discover(self) -> list[str]:
        """Discover API documentation URLs.

        Returns:
            List of discovered documentation URLs
        """
        logger.info(f"Starting documentation discovery for {self.base_url}")

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            headers={"User-Agent": self.settings.user_agent},
            follow_redirects=True,
        ) as client:
            # Step 1: Try common documentation paths
            await self._try_common_paths(client)

            # Step 2: Parse sitemap if available
            await self._parse_sitemap(client)

            # Step 3: Crawl from base URL if we didn't find much
            if len(self.doc_urls) < 3:
                await self._crawl_from_base(client)

        logger.info(f"Discovery complete. Found {len(self.doc_urls)} documentation URLs")
        return list(self.doc_urls)

    async def _try_common_paths(self, client: httpx.AsyncClient) -> None:
        """Try common documentation paths.

        Args:
            client: HTTP client
        """
        logger.info("Trying common documentation paths...")

        # Check if we should respect robots.txt crawl delay
        crawl_delay = self.robots_checker.get_crawl_delay(self.settings.user_agent)
        if crawl_delay:
            logger.info(f"Respecting robots.txt crawl delay: {crawl_delay}s")

        tasks = []
        for path in self.COMMON_PATHS:
            url = urljoin(self.base_url, path)
            tasks.append(self._check_url(client, url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, str):  # Successfully found a doc URL
                self.doc_urls.add(result)

    async def _check_url(self, client: httpx.AsyncClient, url: str) -> str | None:
        """Check if a URL exists and looks like documentation.

        Args:
            client: HTTP client
            url: URL to check

        Returns:
            URL if valid, None otherwise
        """
        try:
            response = await client.get(url)
            if response.status_code == 200:
                # Check if it looks like API documentation
                if self._is_api_documentation(url, response.text):
                    logger.debug(f"Found documentation at: {url}")
                    return url
        except Exception as e:
            logger.debug(f"Failed to check {url}: {e}")
        return None

    def _is_api_documentation(self, url: str, html: str) -> bool:
        """Heuristic to determine if a page is API documentation.

        Args:
            url: Page URL
            html: Page HTML content

        Returns:
            True if page appears to be API documentation
        """
        url_lower = url.lower()
        html_lower = html.lower()

        # Strategy 1: Strong URL match (high confidence)
        strong_url_patterns = [
            r"/api.*docs?",
            r"/api.*reference",
            r"/rest.*api",
            r"/graphql",
        ]
        if any(re.search(pattern, url_lower) for pattern in strong_url_patterns):
            logger.debug(f"Strong URL match for {url}")
            return True

        # Strategy 2: Moderate URL match + minimal content check
        if any(re.search(pattern, url_lower) for pattern in self.API_DOC_PATTERNS):
            # CHANGED: Lower threshold from 3 to 2, expanded keyword list
            api_keywords = [
                "endpoint",
                "api",
                "request",
                "response",
                "authentication",
                "get",
                "post",
                "put",
                "delete",
                "parameter",
                "header",
                "body",
                "json",
            ]
            keyword_count = sum(1 for keyword in api_keywords if keyword in html_lower)

            if keyword_count >= 2:  # CHANGED: Was 3
                logger.debug(f"URL pattern + keyword match for {url} (keywords: {keyword_count})")
                return True
            else:
                logger.debug(
                    f"URL pattern match but insufficient keywords for {url} "
                    f"(keywords: {keyword_count}, threshold: 2)"
                )

        # Strategy 3: Strong content match (even without URL match)
        # Check for OpenAPI/Swagger indicators
        if '"openapi"' in html_lower or '"swagger"' in html_lower:
            logger.debug(f"OpenAPI/Swagger spec detected in {url}")
            return True

        # Check for high density of API keywords
        api_keywords_extended = [
            "endpoint",
            "api",
            "request",
            "response",
            "authentication",
            "get",
            "post",
            "put",
            "delete",
            "parameter",
            "header",
            "body",
            "json",
        ]
        api_keyword_density = sum(1 for kw in api_keywords_extended if kw in html_lower)
        if api_keyword_density >= 5:  # 5+ keywords = probably API docs
            logger.debug(f"High API keyword density in {url} ({api_keyword_density} keywords)")
            return True

        # Check for code examples with HTTP methods
        http_methods = ["GET ", "POST ", "PUT ", "DELETE ", "PATCH "]
        method_count = sum(1 for method in http_methods if method in html_lower)
        if method_count >= 2:
            logger.debug(f"HTTP method examples detected in {url} ({method_count} methods)")
            return True

        logger.debug(f"Page {url} does not match API documentation heuristics")
        return False

    async def _parse_sitemap(self, client: httpx.AsyncClient) -> None:
        """Parse sitemap.xml to find documentation URLs.

        Args:
            client: HTTP client
        """
        logger.info("Checking for sitemap.xml...")

        sitemap_urls = [
            urljoin(self.base_url, "/sitemap.xml"),
            urljoin(self.base_url, "/sitemap_index.xml"),
        ]

        for sitemap_url in sitemap_urls:
            try:
                response = await client.get(sitemap_url)
                if response.status_code == 200:
                    logger.info(f"Found sitemap at {sitemap_url}")
                    await self._extract_urls_from_sitemap(response.text)
                    return
            except Exception as e:
                logger.debug(f"No sitemap at {sitemap_url}: {e}")

    async def _extract_urls_from_sitemap(self, sitemap_xml: str) -> None:
        """Extract documentation URLs from sitemap XML.

        Args:
            sitemap_xml: Sitemap XML content
        """
        soup = BeautifulSoup(sitemap_xml, "xml")
        urls = soup.find_all("loc")

        for url_tag in urls:
            url = url_tag.text.strip()
            if self._is_likely_api_doc_url(url):
                self.doc_urls.add(url)
                logger.debug(f"Found doc URL in sitemap: {url}")

    def _is_likely_api_doc_url(self, url: str) -> bool:
        """Check if a URL is likely API documentation.

        Args:
            url: URL to check

        Returns:
            True if URL matches API documentation patterns
        """
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in self.API_DOC_PATTERNS)

    async def _crawl_from_base(self, client: httpx.AsyncClient) -> None:
        """Crawl from base URL to find documentation.

        Args:
            client: HTTP client
        """
        logger.info("Starting breadth-first crawl from base URL...")

        queue = [self.base_url]
        depth = 0

        while queue and depth < self.settings.max_depth:
            current_batch = queue[: self.settings.max_concurrent_requests]
            queue = queue[self.settings.max_concurrent_requests :]

            tasks = [self._crawl_page(client, url) for url in current_batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    queue.extend(result)

            depth += 1

        logger.info(f"Crawl complete at depth {depth}")

    async def _crawl_page(self, client: httpx.AsyncClient, url: str) -> list[str]:
        """Crawl a single page and extract links.

        Args:
            client: HTTP client
            url: URL to crawl

        Returns:
            List of new URLs to visit
        """
        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

        if len(self.visited_urls) > self.settings.max_pages_per_site:
            return []

        try:
            response = await client.get(url)
            if response.status_code != 200:
                return []

            # Check if this is a documentation page
            if self._is_api_documentation(url, response.text):
                self.doc_urls.add(url)

            # Extract links to continue crawling
            soup = BeautifulSoup(response.text, "html.parser")
            new_urls = []

            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)

                # Only follow links on the same domain
                if self._is_same_domain(absolute_url):
                    # Prioritize links that look like documentation
                    if self._is_likely_api_doc_url(absolute_url):
                        new_urls.insert(0, absolute_url)  # Add to front of queue
                    else:
                        new_urls.append(absolute_url)

            # Rate limiting
            await asyncio.sleep(self.settings.rate_limit_delay)

            return new_urls[:10]  # Limit breadth

        except Exception as e:
            logger.debug(f"Failed to crawl {url}: {e}")
            return []

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is on the same domain as base URL.

        Args:
            url: URL to check

        Returns:
            True if same domain
        """
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain or url_domain == ""
