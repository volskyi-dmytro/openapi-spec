"""Command-line interface for OpenAPI generator."""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from openapi_generator.config import get_settings
from openapi_generator.generators.openapi_builder import OpenAPIBuilder
from openapi_generator.orchestrator import OpenAPIOrchestrator
from openapi_generator.validators.coverage import CoverageAnalyzer
from openapi_generator.validators.spec_validator import SpecValidator

console = Console()


@click.command()
@click.argument("base_url")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: output/<domain>.openapi.json)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json or yaml)",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate generated spec (default: True)",
)
@click.option(
    "--filter",
    "-q",
    type=str,
    help="Natural language query to filter endpoints (e.g., 'payment endpoints only')",
)
@click.option(
    "--doc-url",
    "-d",
    type=str,
    multiple=True,
    help=(
        "Direct URL(s) to API documentation (bypasses discovery). "
        "Can be specified multiple times."
    ),
)
def main(
    base_url: str,
    output: str | None,
    format: str,
    validate: bool,
    filter: str | None,
    doc_url: tuple,
) -> None:
    """Generate OpenAPI specification from API documentation.

    BASE_URL: Base URL of the API documentation (e.g., https://api.example.com)
    """
    console.print(
        Panel.fit(
            "[bold cyan]OpenAPI Specification Generator[/bold cyan]\n"
            "[dim]Automated API spec extraction using LLM[/dim]",
            border_style="cyan",
        )
    )

    # Run async pipeline
    try:
        asyncio.run(run_pipeline(base_url, output, format, validate, filter, doc_url))
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


async def run_pipeline(
    base_url: str,
    output: str | None,
    format: str,
    validate: bool,
    filter: str | None = None,
    doc_urls: tuple = (),
) -> None:
    """Run the complete generation pipeline.

    Args:
        base_url: Base URL to generate from
        output: Output file path
        format: Output format (json or yaml)
        validate: Whether to validate the spec
        filter: Natural language query to filter endpoints
        doc_urls: Manual documentation URLs to use (bypasses discovery)
    """
    settings = get_settings()

    # Normalize base URL
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"

    console.print(f"\n[bold]Target:[/bold] {base_url}\n")

    # Initialize orchestrator
    orchestrator = OpenAPIOrchestrator(base_url)

    # Run pipeline with progress indicators
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Discovery (or use manual URLs)
        if doc_urls:
            console.print(
                f"[yellow]Using {len(doc_urls)} manually specified documentation URL(s)[/yellow]"
            )
            doc_urls = list(doc_urls)
        elif settings.force_doc_urls:
            # Check environment variable override
            doc_urls = [url.strip() for url in settings.force_doc_urls.split(",")]
            console.print(
                f"[yellow]Using {len(doc_urls)} documentation URL(s) from "
                f"FORCE_DOC_URLS environment variable[/yellow]"
            )
        else:
            task = progress.add_task("Discovering documentation pages...", total=None)
            doc_urls = await orchestrator.discovery.discover()
            progress.update(task, completed=True)
            console.print(f"Found {len(doc_urls)} documentation pages")

        if not doc_urls:
            console.print("[red]No documentation pages found! Exiting.[/red]")
            return

        # Content extraction
        task = progress.add_task("Extracting content from pages...", total=None)
        extracted_content = await orchestrator._extract_content_from_urls(doc_urls)
        progress.update(task, completed=True)
        console.print(f"Extracted content from {len(extracted_content)} pages")

        if not extracted_content:
            console.print("[red]No content extracted! Exiting.[/red]")
            return

        # LLM extraction
        task = progress.add_task("Extracting API info with LLM...", total=None)
        extraction_results = await orchestrator._extract_with_llm(extracted_content)
        progress.update(task, completed=True)
        console.print(f"Processed {len(extraction_results)} pages with LLM")

        # Apply query filter if provided
        if filter:
            from openapi_generator.utils.query_filter import QueryFilter

            query_filter = QueryFilter()

            # Collect all endpoints
            all_endpoints_before = []
            for result in extraction_results:
                all_endpoints_before.extend(result.endpoints)

            # Filter endpoints
            filtered_endpoints = query_filter.apply_filter(
                all_endpoints_before, filter, threshold=0.3
            )

            # Create new extraction result with filtered endpoints
            from openapi_generator.models.schemas import ConfidenceLevel, ExtractionResult

            extraction_results = [
                ExtractionResult(
                    endpoints=filtered_endpoints,
                    confidence=ConfidenceLevel.HIGH,
                )
            ]

            console.print(
                f"Filtered {len(all_endpoints_before)} to {len(filtered_endpoints)} "
                f"endpoints (query: '{filter}')"
            )

        # Build OpenAPI spec
        task = progress.add_task("Building OpenAPI specification...", total=None)
        builder = OpenAPIBuilder(base_url)
        builder.add_extraction_results(extraction_results)
        spec = builder.build()
        progress.update(task, completed=True)
        console.print("OpenAPI specification built")

    # Convert spec to dict for validation and output
    spec_dict = spec.model_dump(by_alias=True, exclude_none=True)

    # Generate coverage report
    console.print("\n[bold]Coverage Report:[/bold]")
    all_endpoints = []
    for result in extraction_results:
        all_endpoints.extend(result.endpoints)

    coverage_analyzer = CoverageAnalyzer()
    coverage_report = coverage_analyzer.analyze(all_endpoints)
    display_coverage_report(coverage_report)

    # Validation
    if validate:
        console.print("\n[bold]Validation:[/bold]")
        validator = SpecValidator()
        is_valid, errors, recommendations = validator.validate_with_recommendations(spec_dict)

        if is_valid:
            console.print("[green]Specification is valid![/green]")
        else:
            console.print("[red]Validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]- {error}[/red]")

        if recommendations:
            console.print("\n[bold]Recommendations:[/bold]")
            for rec in recommendations:
                console.print(f"  [yellow]- {rec}[/yellow]")

    # Output
    console.print("\n[bold]Output:[/bold]")

    # Determine output path
    if not output:
        domain = base_url.replace("https://", "").replace("http://", "").split("/")[0]
        domain = domain.replace(".", "_")
        output = str(settings.output_dir / f"{domain}.openapi.{format}")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    if format == "json":
        output_text = builder.to_json(spec)
    else:
        output_text = builder.to_yaml(spec)

    output_path.write_text(output_text)

    console.print(f"Specification written to: [cyan]{output_path}[/cyan]")
    console.print(f"  Format: {format.upper()}")
    console.print(f"  Size: {len(output_text):,} bytes")

    # Summary
    console.print(
        Panel.fit(
            f"[bold green]Success![/bold green]\n"
            f"Generated OpenAPI spec with {len(spec_dict.get('paths', {}))} paths",
            border_style="green",
        )
    )


def display_coverage_report(report) -> None:
    """Display coverage report in a formatted table.

    Args:
        report: Coverage report
    """
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", justify="right", style="cyan")
    table.add_column("Percentage", justify="right", style="yellow")

    # Add rows
    table.add_row(
        "Total Endpoints",
        str(report.total_endpoints),
        "100%",
    )
    table.add_row(
        "With Parameters",
        str(report.endpoints_with_parameters),
        f"{report.parameter_coverage:.1f}%",
    )
    body_pct = (
        (report.endpoints_with_request_body / report.total_endpoints * 100)
        if report.total_endpoints > 0
        else 0
    )
    table.add_row(
        "With Request Body",
        str(report.endpoints_with_request_body),
        f"{body_pct:.1f}%",
    )
    table.add_row(
        "With Responses",
        str(report.endpoints_with_responses),
        f"{report.response_coverage:.1f}%",
    )
    examples_pct = (
        (report.endpoints_with_examples / report.total_endpoints * 100)
        if report.total_endpoints > 0
        else 0
    )
    table.add_row(
        "With Examples",
        str(report.endpoints_with_examples),
        f"{examples_pct:.1f}%",
    )

    console.print(table)

    # Confidence distribution
    console.print("\n[bold]Confidence Distribution:[/bold]")
    conf_table = Table(show_header=False)
    conf_table.add_column("Level", style="white")
    conf_table.add_column("Count", justify="right")

    for level, count in report.confidence_distribution.items():
        color = "green" if level == "high" else "yellow" if level == "medium" else "red"
        conf_table.add_row(f"[{color}]{level.title()}[/{color}]", str(count))

    console.print(conf_table)

    # Quality score
    score = report.quality_score
    score_color = "green" if score >= 70 else "yellow" if score >= 50 else "red"
    console.print(
        f"\n[bold]Overall Quality Score:[/bold] [{score_color}]{score:.1f}%[/{score_color}]"
    )


if __name__ == "__main__":
    main()
