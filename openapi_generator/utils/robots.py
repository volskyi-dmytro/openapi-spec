"""Robots.txt parser and checker for ethical crawling."""

from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class RobotsChecker:
    """Checks robots.txt for crawling permissions."""

    def __init__(self, base_url: str):
        """Initialize robots checker.

        Args:
            base_url: Base URL of the site
        """
        self.base_url = base_url
        self.robots_url = urljoin(base_url, "/robots.txt")
        self.parser = RobotFileParser()
        self.parser.set_url(self.robots_url)

        # Try to read robots.txt
        try:
            self.parser.read()
            logger.info(f"Successfully loaded robots.txt from {self.robots_url}")
            self.loaded = True
        except Exception as e:
            logger.warning(f"Could not load robots.txt from {self.robots_url}: {e}")
            self.loaded = False

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check
            user_agent: User agent string to check for

        Returns:
            True if URL can be fetched, False otherwise
        """
        if not self.loaded:
            # If robots.txt couldn't be loaded, allow by default
            return True

        try:
            return self.parser.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow by default on error

    def get_crawl_delay(self, user_agent: str = "*") -> float | None:
        """Get crawl delay from robots.txt.

        Args:
            user_agent: User agent string to check for

        Returns:
            Crawl delay in seconds, or None if not specified
        """
        if not self.loaded:
            return None

        try:
            return self.parser.crawl_delay(user_agent)
        except Exception as e:
            logger.warning(f"Error getting crawl delay: {e}")
            return None

    def is_sitemaps_allowed(self) -> bool:
        """Check if sitemaps are mentioned in robots.txt.

        Returns:
            True if sitemaps are explicitly mentioned
        """
        if not self.loaded:
            return True

        try:
            sitemaps = self.parser.site_maps()
            return sitemaps is not None and len(sitemaps) > 0
        except Exception as e:
            logger.warning(f"Error checking sitemaps: {e}")
            return True
