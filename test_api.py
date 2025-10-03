#!/usr/bin/env python3
"""Test script for trying different APIs."""

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from openapi_generator.config import get_settings
from openapi_generator.generators.openapi_builder import OpenAPIBuilder
from openapi_generator.orchestrator import OpenAPIOrchestrator
from openapi_generator.validators.coverage import CoverageAnalyzer

console = Console()


# Test APIs (sorted by likelihood of success)
TEST_APIS = {
    "jsonplaceholder": {
        "url": "https://jsonplaceholder.typicode.com",
        "description": "Simple REST API for testing - Very easy",
        "expected_endpoints": "~10 endpoints (posts, users, comments)",
        "difficulty": "",
    },
    "restcountries": {
        "url": "https://restcountries.com",
        "description": "Country information API - Easy",
        "expected_endpoints": "~5 endpoints (all countries, by name, by code)",
        "difficulty": "",
    },
    "pokeapi": {
        "url": "https://pokeapi.co",
        "description": "Pokemon data API - Medium (large docs)",
        "expected_endpoints": "~30+ endpoints (pokemon, abilities, items)",
        "difficulty": "",
    },
    "github": {
        "url": "https://docs.github.com/en/rest",
        "description": "GitHub REST API - Hard (complex docs)",
        "expected_endpoints": "100+ endpoints (repos, issues, users)",
        "difficulty": "",
    },
    "joke": {
        "url": "https://official-joke-api.appspot.com",
        "description": "Random joke API - Very easy",
        "expected_endpoints": "~3 endpoints (random, by type)",
        "difficulty": "",
    },
}


async def test_api(api_name: str, api_info: dict) -> dict:
    """Test a single API.

    Args:
        api_name: API name
        api_info: API information

    Returns:
        Test results dictionary
    """
    console.print(f"\n[bold cyan]Testing: {api_name}[/bold cyan]")
    console.print(f"[dim]{api_info['description']}[/dim]")
    console.print(f"URL: {api_info['url']}\n")

    try:
        # Run orchestrator
        orchestrator = OpenAPIOrchestrator(api_info["url"])

        # Discovery
        console.print("→ Discovering documentation...")
        doc_urls = await orchestrator.discovery.discover()

        if not doc_urls:
            return {
                "success": False,
                "error": "No documentation pages found",
                "doc_urls": 0,
                "endpoints": 0,
            }

        console.print(f"   Found {len(doc_urls)} pages")

        # Content extraction
        console.print("→ Extracting content...")
        extracted_content = await orchestrator._extract_content_from_urls(doc_urls[:5])  # Limit to 5 for testing

        if not extracted_content:
            return {
                "success": False,
                "error": "No content extracted",
                "doc_urls": len(doc_urls),
                "endpoints": 0,
            }

        console.print(f"   Extracted {len(extracted_content)} pages")

        # LLM extraction
        console.print("→ Extracting API info with LLM...")
        extraction_results = await orchestrator._extract_with_llm(extracted_content)

        total_endpoints = sum(len(r.endpoints) for r in extraction_results)
        console.print(f"   Found {total_endpoints} endpoints")

        # Build spec
        builder = OpenAPIBuilder(api_info["url"])
        builder.add_extraction_results(extraction_results)
        spec = builder.build()

        # Analyze coverage
        all_endpoints = []
        for result in extraction_results:
            all_endpoints.extend(result.endpoints)

        analyzer = CoverageAnalyzer()
        coverage = analyzer.analyze(all_endpoints)

        console.print(f"   Quality score: {coverage.quality_score:.1f}%")

        # Save
        settings = get_settings()
        output_dir = Path(settings.output_dir)
        output_path = output_dir / f"test_{api_name}.openapi.json"
        output_path.write_text(builder.to_json(spec))
        console.print(f"   Saved to {output_path}")

        return {
            "success": True,
            "doc_urls": len(doc_urls),
            "endpoints": total_endpoints,
            "quality": coverage.quality_score,
            "output": str(output_path),
        }

    except Exception as e:
        console.print(f"  [red] Error: {e}[/red]")
        return {
            "success": False,
            "error": str(e),
            "doc_urls": 0,
            "endpoints": 0,
        }


async def run_tests(selected_apis: list):
    """Run tests for selected APIs.

    Args:
        selected_apis: List of API names to test
    """
    console.print(
        "[bold cyan]OpenAPI Generator Test Suite[/bold cyan]\n"
        f"Testing {len(selected_apis)} API(s)...\n"
    )

    results = {}
    for api_name in selected_apis:
        if api_name not in TEST_APIS:
            console.print(f"[red]Unknown API: {api_name}[/red]")
            continue

        result = await test_api(api_name, TEST_APIS[api_name])
        results[api_name] = result

        # Rate limiting between tests
        await asyncio.sleep(2)

    # Summary table
    console.print("\n[bold]Test Results Summary:[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("API", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Docs", justify="right")
    table.add_column("Endpoints", justify="right")
    table.add_column("Quality", justify="right")

    for api_name, result in results.items():
        if result["success"]:
            status = "[green] Pass[/green]"
            quality = f"{result['quality']:.1f}%" if "quality" in result else "N/A"
        else:
            status = "[red] Fail[/red]"
            quality = "N/A"

        table.add_row(
            api_name,
            status,
            str(result["doc_urls"]),
            str(result["endpoints"]),
            quality,
        )

    console.print(table)

    # Success rate
    successes = sum(1 for r in results.values() if r["success"])
    total = len(results)
    console.print(f"\n[bold]Success Rate:[/bold] {successes}/{total} ({successes/total*100:.1f}%)")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print(
            "[bold cyan]OpenAPI Generator Test Suite[/bold cyan]\n\n"
            "[yellow]Usage:[/yellow]\n"
            "  python test_api.py <api_name> [api_name2 ...]\n"
            "  python test_api.py all\n\n"
            "[bold]Available APIs:[/bold]\n"
        )

        # Show available APIs
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Difficulty", justify="center")
        table.add_column("Description")

        for name, info in TEST_APIS.items():
            table.add_row(name, info["difficulty"], info["description"])

        console.print(table)

        console.print(
            "\n[bold]Examples:[/bold]\n"
            "  # Test a single API\n"
            "  python test_api.py jsonplaceholder\n\n"
            "  # Test multiple APIs\n"
            "  python test_api.py jsonplaceholder restcountries\n\n"
            "  # Test all APIs (takes a while!)\n"
            "  python test_api.py all\n"
        )
        sys.exit(1)

    # Parse arguments
    if sys.argv[1] == "all":
        selected_apis = list(TEST_APIS.keys())
    else:
        selected_apis = sys.argv[1:]

    # Run tests
    asyncio.run(run_tests(selected_apis))


if __name__ == "__main__":
    main()
