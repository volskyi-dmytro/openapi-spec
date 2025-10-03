"""Playwright-based renderer for JavaScript-heavy sites."""

from playwright.async_api import Browser, async_playwright

from openapi_generator.config import get_settings
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class JavaScriptRenderer:
    """Renders JavaScript-heavy pages using Playwright."""

    def __init__(self):
        """Initialize renderer."""
        self.settings = get_settings()
        self._browser: Browser | None = None

    async def __aenter__(self) -> "JavaScriptRenderer":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def render_page(self, url: str, wait_for_selector: str | None = None) -> str:
        """Render a page with JavaScript execution.

        Args:
            url: URL to render
            wait_for_selector: Optional CSS selector to wait for before extracting content

        Returns:
            Rendered HTML content
        """
        logger.info(f"Rendering JavaScript page: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent=self.settings.user_agent,
                )

                # Set timeout
                page.set_default_timeout(self.settings.request_timeout * 1000)  # Convert to ms

                # Navigate to page
                await page.goto(url, wait_until="networkidle")

                # Wait for specific selector if provided
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=10000)
                else:
                    # Wait a bit for dynamic content to load
                    await page.wait_for_timeout(2000)

                # Get rendered HTML
                html = await page.content()

                logger.debug(f"Successfully rendered {url} ({len(html)} chars)")
                return html

            finally:
                await browser.close()

    async def close(self) -> None:
        """Close browser if open."""
        if self._browser:
            await self._browser.close()
            self._browser = None
