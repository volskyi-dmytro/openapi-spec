"""Integration tests for the complete OpenAPI generation pipeline."""

import json

import pytest

from openapi_generator.generators.openapi_builder import OpenAPIBuilder
from openapi_generator.orchestrator import OpenAPIOrchestrator
from openapi_generator.validators.coverage import CoverageAnalyzer
from openapi_generator.validators.spec_validator import SpecValidator


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_catfact():
    """Test full pipeline with catfact.ninja API (has embedded OpenAPI spec)."""
    base_url = "https://catfact.ninja"

    # Run orchestrator
    orchestrator = OpenAPIOrchestrator(base_url)
    results = await orchestrator.run()

    # Should find at least one page
    assert len(results) > 0, "Should extract at least one page"

    # Should find endpoints
    total_endpoints = sum(len(r.endpoints) for r in results)
    assert total_endpoints > 0, "Should extract at least one endpoint"

    # Build OpenAPI spec
    builder = OpenAPIBuilder(base_url)
    builder.add_extraction_results(results)
    spec = builder.build()

    # Validate spec
    spec_dict = spec.model_dump(by_alias=True, exclude_none=True)
    validator = SpecValidator()
    is_valid, errors = validator.validate(spec_dict)

    assert is_valid, f"Spec should be valid. Errors: {errors}"
    assert len(spec_dict["paths"]) > 0, "Should have at least one path"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_with_caching():
    """Test that caching works for repeated runs."""
    base_url = "https://catfact.ninja"

    # First run
    orchestrator1 = OpenAPIOrchestrator(base_url)
    results1 = await orchestrator1.run()
    endpoint_count1 = sum(len(r.endpoints) for r in results1)

    # Second run (should use cache)
    orchestrator2 = OpenAPIOrchestrator(base_url)
    results2 = await orchestrator2.run()
    endpoint_count2 = sum(len(r.endpoints) for r in results2)

    # Should get same number of endpoints
    assert endpoint_count1 == endpoint_count2, "Cached results should match"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_coverage_analysis():
    """Test coverage analysis on generated spec."""
    base_url = "https://catfact.ninja"

    # Run orchestrator
    orchestrator = OpenAPIOrchestrator(base_url)
    results = await orchestrator.run()

    # Analyze coverage
    all_endpoints = []
    for result in results:
        all_endpoints.extend(result.endpoints)

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze(all_endpoints)

    # Basic checks
    assert report.total_endpoints > 0
    assert report.quality_score >= 0
    assert report.quality_score <= 100
    assert "high" in report.confidence_distribution
    assert "medium" in report.confidence_distribution
    assert "low" in report.confidence_distribution


@pytest.mark.integration
@pytest.mark.asyncio
async def test_parallel_processing():
    """Test that parallel processing works correctly."""
    base_url = "https://catfact.ninja"

    # Run with parallel processing
    orchestrator = OpenAPIOrchestrator(base_url)
    orchestrator.settings.max_concurrent_llm_calls = 3

    results = await orchestrator.run()

    # Should complete successfully
    assert len(results) > 0
    total_endpoints = sum(len(r.endpoints) for r in results)
    assert total_endpoints > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_spec_export_formats():
    """Test exporting spec in different formats."""
    base_url = "https://catfact.ninja"

    # Run orchestrator
    orchestrator = OpenAPIOrchestrator(base_url)
    results = await orchestrator.run()

    # Build spec
    builder = OpenAPIBuilder(base_url)
    builder.add_extraction_results(results)
    spec = builder.build()

    # Test JSON export
    json_output = builder.to_json(spec)
    assert isinstance(json_output, str)
    json_dict = json.loads(json_output)
    assert json_dict["openapi"] == "3.0.3"
    assert "paths" in json_dict

    # Test YAML export
    yaml_output = builder.to_yaml(spec)
    assert isinstance(yaml_output, str)
    assert "openapi:" in yaml_output
    assert "paths:" in yaml_output


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deduplication():
    """Test that duplicate endpoints are properly deduplicated."""
    base_url = "https://catfact.ninja"

    # Run orchestrator
    orchestrator = OpenAPIOrchestrator(base_url)
    results = await orchestrator.run()

    # Build spec
    builder = OpenAPIBuilder(base_url)
    builder.add_extraction_results(results)

    # Count total endpoints before deduplication
    total_before = len(builder.endpoints)

    # Build (which includes deduplication)
    spec = builder.build()
    spec_dict = spec.model_dump(by_alias=True, exclude_none=True)

    # Count paths after
    total_after = sum(len(methods) for methods in spec_dict["paths"].values())

    # Should have deduplicated if there were duplicates
    # (we don't assert less because catfact might not have duplicates)
    assert total_after <= total_before


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling with invalid URLs."""
    # Try with a URL that doesn't exist
    base_url = "https://this-domain-definitely-does-not-exist-12345.com"

    orchestrator = OpenAPIOrchestrator(base_url)

    # Should not crash, just return empty results
    results = await orchestrator.run()
    assert isinstance(results, list)
    # Might be empty or have failed results
    assert len(results) == 0 or all(len(r.endpoints) == 0 for r in results)


@pytest.mark.integration
def test_cache_manager():
    """Test cache manager functionality."""
    from openapi_generator.utils.cache import get_cache_manager

    cache_manager = get_cache_manager()

    # Test cache key generation
    key1 = cache_manager.get_content_hash("test content")
    key2 = cache_manager.get_content_hash("test content")
    key3 = cache_manager.get_content_hash("different content")

    assert key1 == key2, "Same content should have same hash"
    assert key1 != key3, "Different content should have different hash"

    # Test cache stats
    stats = cache_manager.get_cache_stats()
    assert "http_cache_enabled" in stats
    assert "llm_cache_enabled" in stats
    assert "total_size_mb" in stats
