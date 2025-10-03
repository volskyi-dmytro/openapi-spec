"""Main orchestrator for OpenAPI generation pipeline."""

import asyncio
from typing import List

from openapi_generator.config import get_settings
from openapi_generator.extractors.content import ContentExtractor, DocumentContent
from openapi_generator.extractors.discovery import DocumentationDiscovery
from openapi_generator.extractors.llm_extractor import LLMExtractor
from openapi_generator.extractors.renderer import JavaScriptRenderer
from openapi_generator.models.schemas import ExtractionResult
from openapi_generator.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAPIOrchestrator:
    """Orchestrates the OpenAPI generation pipeline."""

    def __init__(self, base_url: str):
        """Initialize orchestrator.

        Args:
            base_url: Base URL to generate spec from
        """
        self.base_url = base_url
        self.settings = get_settings()

        # Initialize components
        self.discovery = DocumentationDiscovery(base_url)
        self.content_extractor = ContentExtractor()
        self.llm_extractor = LLMExtractor()
        self.js_renderer = JavaScriptRenderer()

        # Results
        self.doc_urls: List[str] = []
        self.extracted_content: List[DocumentContent] = []
        self.extraction_results: List[ExtractionResult] = []

    async def run(self) -> List[ExtractionResult]:
        """Run the complete pipeline.

        Returns:
            List of extraction results from all pages
        """
        logger.info(f"Starting OpenAPI generation pipeline for {self.base_url}")

        # Stage 1: Discover documentation pages
        logger.info("Stage 1: Discovering documentation pages...")
        self.doc_urls = await self.discovery.discover()

        if not self.doc_urls:
            logger.error("No documentation URLs found!")
            return []

        logger.info(f"Found {len(self.doc_urls)} documentation URLs")

        # Stage 2: Extract content from pages
        logger.info("Stage 2: Extracting content from documentation pages...")
        self.extracted_content = await self._extract_content_from_urls(self.doc_urls)

        if not self.extracted_content:
            logger.error("No content extracted!")
            return []

        logger.info(f"Extracted content from {len(self.extracted_content)} pages")

        # Stage 3: LLM-powered extraction (map-reduce pattern)
        logger.info("Stage 3: Extracting API information with LLM...")
        self.extraction_results = await self._extract_with_llm(self.extracted_content)

        logger.info(f"Extraction complete! Processed {len(self.extraction_results)} pages")

        return self.extraction_results

    async def _extract_content_from_urls(self, urls: List[str]) -> List[DocumentContent]:
        """Extract content from URLs with SPA detection.

        Args:
            urls: List of URLs to extract from

        Returns:
            List of extracted document content
        """
        contents = []

        for url in urls:
            try:
                # Try regular extraction first
                content = await self.content_extractor.extract_from_url(url)

                if not content:
                    continue

                # Check if it's a SPA and needs JavaScript rendering
                if self.content_extractor.detect_spa(content.text):
                    logger.info(f"SPA detected at {url}, using JavaScript renderer")
                    html = await self.js_renderer.render_page(url)
                    content = self.content_extractor.extract_from_html(url, html)

                contents.append(content)

                # Rate limiting
                await asyncio.sleep(self.settings.rate_limit_delay)

            except Exception as e:
                logger.error(f"Failed to extract content from {url}: {e}")
                continue

        return contents

    async def _extract_with_llm(self, contents: List[DocumentContent]) -> List[ExtractionResult]:
        """Extract API information using LLM (map-reduce pattern with parallel processing).

        Args:
            contents: List of document contents

        Returns:
            List of extraction results
        """
        logger.info(f"Starting parallel LLM extraction for {len(contents)} documents")

        # Map phase: Process documents in parallel with concurrency control
        max_concurrent = getattr(self.settings, "max_concurrent_llm_calls", 3)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_semaphore(content: DocumentContent, index: int) -> ExtractionResult:
            """Extract with concurrency control."""
            async with semaphore:
                logger.info(f"Processing document {index + 1}/{len(contents)}: {content.url}")
                try:
                    result = await self.llm_extractor.extract(content)
                    logger.info(
                        f"Completed {index + 1}/{len(contents)}: {len(result.endpoints)} endpoints"
                    )
                    return result
                except Exception as e:
                    logger.error(f"LLM extraction failed for {content.url}: {e}")
                    # Return empty result on failure
                    from openapi_generator.models.schemas import ExtractionResult, ConfidenceLevel

                    return ExtractionResult(confidence=ConfidenceLevel.LOW)

        # Process all documents in parallel (respecting concurrency limit)
        tasks = [extract_with_semaphore(content, i) for i, content in enumerate(contents)]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Filter out empty results
        valid_results = [r for r in results if r.endpoints]
        logger.info(
            f"Parallel extraction complete: {len(valid_results)}/{len(contents)} documents successful"
        )

        # Reduce phase is handled in the generator (merging all results)
        return valid_results
