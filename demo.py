#!/usr/bin/env python3
"""Quick demo script for OpenAPI Generator."""

import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from openapi_generator.config import get_settings
from openapi_generator.generators.openapi_builder import OpenAPIBuilder
from openapi_generator.orchestrator import OpenAPIOrchestrator
from openapi_generator.validators.coverage import CoverageAnalyzer
from openapi_generator.validators.spec_validator import SpecValidator

console = Console()


async def demo(base_url: str):
    """Run a demo extraction for the given URL.

    Args:
        base_url: Base URL to extract from
    """
    console.print(
        Panel.fit(
            "[bold cyan]OpenAPI Generator Demo[/bold cyan]\n"
            f"[dim]Extracting from: {base_url}[/dim]",
            border_style="cyan",
        )
    )

    # Initialize
    orchestrator = OpenAPIOrchestrator(base_url)

    # Stage 1: Discovery
    console.print("\n[bold yellow]Stage 1:[/bold yellow] Discovering documentation pages...")
    doc_urls = await orchestrator.discovery.discover()
    console.print(f" Found [cyan]{len(doc_urls)}[/cyan] documentation URLs")

    if doc_urls:
        console.print("\n[dim]Sample URLs:[/dim]")
        for url in doc_urls[:5]:
            console.print(f"  - {url}")
        if len(doc_urls) > 5:
            console.print(f"  ... and {len(doc_urls) - 5} more")

    if not doc_urls:
        console.print("[red]No documentation found! Try a different URL.[/red]")
        return

    # Stage 2: Content Extraction
    console.print("\n[bold yellow]Stage 2:[/bold yellow] Extracting content...")
    extracted_content = await orchestrator._extract_content_from_urls(doc_urls)
    console.print(f" Extracted content from [cyan]{len(extracted_content)}[/cyan] pages")

    if extracted_content:
        sample = extracted_content[0]
        console.print(
            f"\n[dim]Sample page:[/dim] {sample.title} ({sample.token_estimate} tokens estimated)"
        )

    if not extracted_content:
        console.print("[red]No content extracted![/red]")
        return

    # Stage 3: LLM Extraction
    console.print("\n[bold yellow]Stage 3:[/bold yellow] Extracting API info with LLM...")
    console.print("[dim]This may take a minute...[/dim]")
    extraction_results = await orchestrator._extract_with_llm(extracted_content)
    console.print(f" Processed [cyan]{len(extraction_results)}[/cyan] pages")

    # Count total endpoints
    total_endpoints = sum(len(r.endpoints) for r in extraction_results)
    console.print(f" Extracted [cyan]{total_endpoints}[/cyan] endpoints")

    # Stage 4: Build OpenAPI Spec
    console.print("\n[bold yellow]Stage 4:[/bold yellow] Building OpenAPI specification...")
    builder = OpenAPIBuilder(base_url)
    builder.add_extraction_results(extraction_results)
    spec = builder.build()
    console.print(" OpenAPI 3.0 spec generated")

    # Stage 5: Validation & Analysis
    console.print("\n[bold yellow]Stage 5:[/bold yellow] Validating & analyzing...")

    # Convert to dict for validation
    spec_dict = spec.model_dump(by_alias=True, exclude_none=True)

    # Validate
    validator = SpecValidator()
    is_valid, errors, recommendations = validator.validate_with_recommendations(spec_dict)

    if is_valid:
        console.print(" [green]Specification is valid![/green]")
    else:
        console.print("[red]Validation errors found:[/red]")
        for error in errors[:3]:
            console.print(f"  - {error}")

    # Coverage analysis
    all_endpoints = []
    for result in extraction_results:
        all_endpoints.extend(result.endpoints)

    analyzer = CoverageAnalyzer()
    coverage_report = analyzer.analyze(all_endpoints)

    console.print(
        f"\n[bold]Quality Metrics:[/bold]\n"
        f"  - Total Endpoints: [cyan]{coverage_report.total_endpoints}[/cyan]\n"
        f"  - Parameter Coverage: [cyan]{coverage_report.parameter_coverage:.1f}%[/cyan]\n"
        f"  - Response Coverage: [cyan]{coverage_report.response_coverage:.1f}%[/cyan]\n"
        f"  - Quality Score: [cyan]{coverage_report.quality_score:.1f}%[/cyan]"
    )

    # Save output
    settings = get_settings()
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(exist_ok=True)

    domain = base_url.replace("https://", "").replace("http://", "").split("/")[0]
    domain = domain.replace(".", "_")
    output_path = output_dir / f"{domain}_demo.openapi.json"

    spec_json = builder.to_json(spec)
    output_path.write_text(spec_json)

    console.print(f"\n Saved to: [cyan]{output_path}[/cyan]")

    # Show a sample endpoint
    if all_endpoints:
        console.print("\n[bold]Sample Endpoint:[/bold]")
        sample_endpoint = all_endpoints[0]
        endpoint_info = {
            "path": sample_endpoint.path,
            "method": sample_endpoint.method.value,
            "summary": sample_endpoint.summary,
            "parameters": len(sample_endpoint.parameters),
            "confidence": sample_endpoint.confidence.value,
        }
        syntax = Syntax(
            json.dumps(endpoint_info, indent=2), "json", theme="monokai", line_numbers=False
        )
        console.print(syntax)

    console.print(
        Panel.fit(
            "[bold green]Demo Complete![/bold green]\n"
            f"Generated spec with {len(spec_dict.get('paths', {}))} paths",
            border_style="green",
        )
    )


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print(
            "[yellow]Usage:[/yellow] python demo.py <base_url>\n\n"
            "[bold]Suggested APIs for testing:[/bold]\n"
            "  1. [cyan]https://jsonplaceholder.typicode.com[/cyan] - Simple REST API\n"
            "  2. [cyan]https://pokeapi.co[/cyan] - Pokemon API (no auth)\n"
            "  3. [cyan]https://restcountries.com[/cyan] - Country data API\n"
            "  4. [cyan]https://api.github.com[/cyan] - GitHub REST API\n"
            "  5. [cyan]https://official-joke-api.appspot.com[/cyan] - Joke API\n\n"
            "[dim]Example:[/dim]\n"
            "  python demo.py https://jsonplaceholder.typicode.com"
        )
        sys.exit(1)

    base_url = sys.argv[1]
    asyncio.run(demo(base_url))


if __name__ == "__main__":
    main()
