"""Content extraction from documentation pages."""

import re
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

from openapi_generator.config import get_settings
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentContent:
    """Represents extracted content from a documentation page."""

    def __init__(self, url: str, title: str, text: str, code_samples: List[str]):
        """Initialize document content.

        Args:
            url: Source URL
            title: Page title
            text: Extracted text content
            code_samples: List of code samples found
        """
        self.url = url
        self.title = title
        self.text = text
        self.code_samples = code_samples

    def __repr__(self) -> str:
        """String representation."""
        return f"DocumentContent(url={self.url}, title={self.title}, chars={len(self.text)})"

    @property
    def token_estimate(self) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
        return (len(self.text) + sum(len(code) for code in self.code_samples)) // 4


class ContentExtractor:
    """Extracts clean content from HTML documentation pages."""

    # Tags to remove (navigation, footers, ads, etc.)
    REMOVE_TAGS = ["nav", "footer", "header", "aside", "script", "style", "noscript"]

    # Tags that typically contain code
    CODE_TAGS = ["code", "pre"]

    def __init__(self):
        """Initialize content extractor."""
        self.settings = get_settings()

    async def extract_from_url(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a URL.

        Args:
            url: URL to extract from

        Returns:
            DocumentContent if successful, None otherwise
        """
        logger.info(f"Extracting content from {url}")

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout,
                headers={"User-Agent": self.settings.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Check Content-Type header
                content_type = response.headers.get("content-type", "").lower()

                if "application/json" in content_type:
                    # Don't use BeautifulSoup for JSON responses
                    logger.info(f"Detected JSON content-type for {url}, preserving raw JSON")
                    return DocumentContent(
                        url=url,
                        title="JSON API Spec",
                        text=response.text,  # Keep raw JSON
                        code_samples=[response.text]  # Also add to code samples
                    )
                else:
                    # Use BeautifulSoup for HTML
                    return self.extract_from_html(url, response.text)

        except Exception as e:
            logger.error(f"Failed to extract from {url}: {e}")
            return None

    def extract_from_html(self, url: str, html: str) -> DocumentContent:
        """Extract content from HTML.

        Args:
            url: Source URL
            html: HTML content

        Returns:
            Extracted document content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = self._extract_title(soup)

        # Extract code samples first (before we clean the HTML)
        code_samples = self._extract_code_samples(soup)

        # Clean up the HTML
        self._remove_unwanted_elements(soup)

        # Extract text content
        text = self._extract_text(soup)

        # Clean up text
        text = self._clean_text(text)

        logger.debug(
            f"Extracted {len(text)} chars, {len(code_samples)} code samples from {url}"
        )

        return DocumentContent(url=url, title=title, text=text, code_samples=code_samples)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title
        """
        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try <h1> tag
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        return "Untitled"

    def _extract_code_samples(self, soup: BeautifulSoup) -> List[str]:
        """Extract code samples from the page.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of code samples
        """
        code_samples = []

        for tag_name in self.CODE_TAGS:
            for tag in soup.find_all(tag_name):
                code = tag.get_text().strip()
                if code and len(code) > 10:  # Skip very short snippets
                    code_samples.append(code)

        return code_samples

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from soup (in-place).

        Args:
            soup: BeautifulSoup object to clean
        """
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, NavigableString)):
            if "<!--" in str(comment):
                comment.extract()

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract text content from cleaned soup.

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted text
        """
        # Focus on main content areas if they exist
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_=re.compile(r"content|documentation|docs"))
            or soup.find("body")
        )

        if main_content:
            return main_content.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    def _clean_text(self, text: str) -> str:
        """Clean extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple newlines to double newline
        text = re.sub(r" +", " ", text)  # Multiple spaces to single space

        # Remove very short lines (likely navigation artifacts)
        lines = text.split("\n")
        lines = [line for line in lines if len(line.strip()) > 3 or line.strip() == ""]

        return "\n".join(lines).strip()

    async def extract_batch(self, urls: List[str]) -> Dict[str, DocumentContent]:
        """Extract content from multiple URLs.

        Args:
            urls: List of URLs to extract from

        Returns:
            Dictionary mapping URL to DocumentContent
        """
        logger.info(f"Extracting content from {len(urls)} URLs")

        results = {}
        for url in urls:
            content = await self.extract_from_url(url)
            if content:
                results[url] = content

        logger.info(f"Successfully extracted {len(results)}/{len(urls)} pages")
        return results

    def detect_spa(self, html: str) -> bool:
        """Detect if a page is a Single Page Application that needs JavaScript rendering.

        Args:
            html: HTML content

        Returns:
            True if SPA detected
        """
        # Look for common SPA indicators
        spa_indicators = [
            r"<div\s+id=['\"]root['\"]",
            r"<div\s+id=['\"]app['\"]",
            r"React",
            r"Vue",
            r"Angular",
            r"ng-app",
            r"data-reactroot",
        ]

        for indicator in spa_indicators:
            if re.search(indicator, html, re.IGNORECASE):
                # Check if there's minimal content
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text().strip()
                if len(text) < 500:  # Very little static content
                    return True

        return False
