"""
Modern CLI for docs-pipeline (2025)
Built with Typer + Rich for professional UX

Usage:
    python -m tools.pdf.cli.app convert input.md output.pdf
    python -m tools.pdf.cli.app batch docs/**/*.md --format pdf
    python -m tools.pdf.cli.app diag env
    python -m tools.pdf.cli.app diag phase-b
"""

import sys
from pathlib import Path
from typing import Optional, List
from enum import Enum
import json
import time

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.box import ROUNDED
except ImportError:
    print("ERROR: Modern CLI requires: pip install typer rich")
    sys.exit(2)

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.converter import markdown_to_pdf, markdown_to_docx, markdown_to_html
from core import check_dependencies, validate_markdown

__version__ = "4.0.0"
app = typer.Typer(
    name="docs-pipeline",
    help="Professional document conversion: Markdown → PDF/DOCX/HTML",
    no_args_is_help=True,
    pretty_exceptions_enable=True,
)

console = Console()


class OutputFormat(str, Enum):
    """Supported output formats"""
    pdf = "pdf"
    docx = "docx"
    html = "html"


class Verbosity(str, Enum):
    """Logging levels"""
    quiet = "quiet"
    normal = "normal"
    verbose = "verbose"
    debug = "debug"


def setup_logging(verbosity: Verbosity):
    """Configure logging based on verbosity level"""
    levels = {
        Verbosity.quiet: 50,  # CRITICAL
        Verbosity.normal: 20,  # INFO
        Verbosity.verbose: 10,  # DEBUG
        Verbosity.debug: 5,  # NOTSET
    }
    import logging
    logging.basicConfig(
        level=levels[verbosity],
        format="%(levelname)s: %(message)s" if verbosity == Verbosity.debug else None
    )


def error_hint(title: str, message: str, hint: str = None):
    """Display an error with helpful hint"""
    console.print(f"\n[red]✗ {title}[/red]")
    console.print(f"  {message}")
    if hint:
        console.print(f"\n[yellow]→ {hint}[/yellow]")
    console.print()


@app.command()
def convert(
    input_file: str = typer.Argument(..., help="Input Markdown file"),
    output_file: Optional[str] = typer.Argument(None, help="Output file (auto-detected if omitted)"),
    format: OutputFormat = typer.Option(OutputFormat.pdf, "--format", "-f", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Style profile (tech-whitepaper, dark-pro, etc.)"),
    use_native_renderer: bool = typer.Option(True, "--native/--no-native", help="Use Phase B native Playwright renderer"),
    enable_diagrams: bool = typer.Option(True, "--diagrams/--no-diagrams", help="Render Mermaid diagrams"),
    generate_cover: bool = typer.Option(False, "--cover", help="Generate cover page (PDF only)"),
    generate_toc: bool = typer.Option(False, "--toc", help="Generate table of contents"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Cache diagram renders"),
    verbose: Verbosity = typer.Option(Verbosity.normal, "--verbose", "-v", help="Logging level"),
):
    """
    Convert Markdown to PDF/DOCX/HTML
    
    Examples:
        # Convert to PDF (default)
        docs-pipeline convert input.md output.pdf
        
        # Use Phase B native renderer (40-60% faster diagrams)
        docs-pipeline convert input.md output.pdf --native
        
        # Generate cover + TOC
        docs-pipeline convert input.md output.pdf --cover --toc --profile tech-whitepaper
        
        # Convert to DOCX
        docs-pipeline convert input.md output.docx --format docx
        
        # Show detailed rendering info
        docs-pipeline convert input.md output.pdf --verbose
    """
    setup_logging(verbose)
    
    # Validate input
    input_path = Path(input_file)
    if not input_path.exists():
        error_hint(
            "Input file not found",
            f"Could not open: {input_file}",
            f"Check the path: {input_path.resolve()}"
        )
        raise typer.Exit(1)
    
    # Determine output file
    if not output_file:
        output_file = str(input_path.with_suffix(f".{format.value}"))
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build config
    config = {
        "use_native_renderer": use_native_renderer,
        "enable_diagrams": enable_diagrams,
        "use_cache": use_cache,
        "verbose": verbose == Verbosity.verbose,
    }
    
    if profile:
        config["profile"] = profile
    
    if format == OutputFormat.pdf:
        config["generate_cover"] = generate_cover
        config["generate_toc"] = generate_toc
    
    # Display conversion info
    table = Table(show_header=False, box=ROUNDED, padding=(0, 2))
    table.add_row("[cyan]Input[/cyan]", str(input_path.resolve()))
    table.add_row("[cyan]Output[/cyan]", str(output_path.resolve()))
    table.add_row("[cyan]Format[/cyan]", format.value.upper())
    if profile:
        table.add_row("[cyan]Profile[/cyan]", profile)
    table.add_row("[cyan]Phase B[/cyan]", "✓ Enabled" if use_native_renderer else "✗ Disabled")
    console.print(table)
    
    # Convert
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}[/cyan]"),
            console=console,
        ) as progress:
            task = progress.add_task("Converting...", total=None)
            
            start_time = time.time()
            
            if format == OutputFormat.pdf:
                success = markdown_to_pdf(str(input_path), str(output_path), **config)
            elif format == OutputFormat.docx:
                success = markdown_to_docx(str(input_path), str(output_path), **config)
            else:  # html
                success = markdown_to_html(str(input_path), str(output_path), **config)
            
            elapsed = time.time() - start_time
            progress.stop()
        
        if success:
            file_size = output_path.stat().st_size
            console.print(
                Panel(
                    f"✓ [green]Success![/green]\n"
                    f"Output: [cyan]{output_path.resolve()}[/cyan]\n"
                    f"Size: [yellow]{file_size / 1024:.1f}KB[/yellow] | "
                    f"Time: [yellow]{elapsed:.1f}s[/yellow]",
                    border_style="green",
                )
            )
        else:
            error_hint("Conversion failed", "Unknown error during processing", "Use --verbose for details")
            raise typer.Exit(1)
    
    except Exception as e:
        error_hint(
            "Conversion failed",
            str(e),
            "Use --verbose for stack trace"
        )
        if verbose == Verbosity.debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def batch(
    input_files: List[str] = typer.Argument(..., help="Input Markdown files (glob patterns supported)"),
    format: OutputFormat = typer.Option(OutputFormat.pdf, "--format", "-f", help="Output format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Style profile"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    use_native_renderer: bool = typer.Option(True, "--native/--no-native", help="Use Phase B native renderer"),
    verbose: Verbosity = typer.Option(Verbosity.normal, "--verbose", "-v", help="Logging level"),
):
    """
    Batch convert multiple Markdown files
    
    Examples:
        # Convert all .md files in docs/
        docs-pipeline batch docs/**/*.md --format pdf
        
        # Output to specific directory
        docs-pipeline batch docs/**/*.md --output-dir output/
        
        # Use Phase B for faster rendering
        docs-pipeline batch docs/**/*.md --native
    """
    setup_logging(verbose)
    
    # Resolve files (support glob)
    import glob
    resolved_files = []
    for pattern in input_files:
        if "*" in pattern or "?" in pattern:
            resolved_files.extend(glob.glob(pattern, recursive=True))
        else:
            resolved_files.append(pattern)
    
    # Validate files
    valid_files = []
    for file in resolved_files:
        path = Path(file)
        if path.exists():
            valid_files.append(path)
        else:
            console.print(f"[yellow]⚠ Skipped (not found): {file}[/yellow]")
    
    if not valid_files:
        error_hint("No valid input files", "Could not find any matching files", "Check glob patterns and paths")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Processing {len(valid_files)} file(s)...[/cyan]\n")
    
    config = {
        "use_native_renderer": use_native_renderer,
        "verbose": verbose == Verbosity.verbose,
    }
    if profile:
        config["profile"] = profile
    
    # Process files
    success_count = 0
    failed_files = []
    
    with Progress(console=console) as progress:
        task = progress.add_task("Converting...", total=len(valid_files))
        
        for input_path in valid_files:
            output_path = Path(output_dir or ".") / input_path.with_suffix(f".{format.value}").name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                if format == OutputFormat.pdf:
                    success = markdown_to_pdf(str(input_path), str(output_path), **config)
                elif format == OutputFormat.docx:
                    success = markdown_to_docx(str(input_path), str(output_path), **config)
                else:
                    success = markdown_to_html(str(input_path), str(output_path), **config)
                
                if success:
                    success_count += 1
                    progress.console.print(f"[green]✓[/green] {input_path.name} → {output_path.name}")
                else:
                    failed_files.append(str(input_path))
                    progress.console.print(f"[red]✗[/red] {input_path.name}")
            
            except Exception as e:
                failed_files.append(str(input_path))
                progress.console.print(f"[red]✗[/red] {input_path.name}: {e}")
            
            progress.advance(task)
    
    # Summary
    console.print()
    if failed_files:
        console.print(
            Panel(
                f"[yellow]Completed with issues[/yellow]\n"
                f"Success: [green]{success_count}[/green] | "
                f"Failed: [red]{len(failed_files)}[/red]",
                border_style="yellow",
            )
        )
        if verbose in [Verbosity.verbose, Verbosity.debug]:
            console.print("\nFailed files:")
            for f in failed_files:
                console.print(f"  • {f}")
        raise typer.Exit(1)
    else:
        console.print(
            Panel(
                f"[green]All {success_count} files converted successfully![/green]",
                border_style="green",
            )
        )


diag_app = typer.Typer(help="Diagnostics & troubleshooting")
app.add_typer(diag_app, name="diag")


@diag_app.command()
def env(
    show_paths: bool = typer.Option(False, "--paths", help="Show full file paths"),
):
    """
    Show environment info: Python, Playwright, Node, etc.
    
    Use this to verify your installation is complete.
    """
    console.print("\n[cyan bold]Environment Check[/cyan bold]\n")
    
    # Check Python
    import platform
    console.print(f"[cyan]Python:[/cyan] {platform.python_version()}")
    console.print(f"[cyan]Platform:[/cyan] {platform.system()} {platform.release()}")
    
    # Check dependencies
    console.print("\n[cyan bold]Dependencies[/cyan bold]\n")
    
    deps = [
        ("playwright", "Playwright (browser automation)"),
        ("pandoc", "Pandoc (markdown conversion)"),
        ("node", "Node.js (Mermaid rendering)"),
    ]
    
    for module, label in deps:
        try:
            if module == "pandoc":
                import subprocess
                subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
                console.print(f"[green]✓[/green] {label}")
            elif module == "node":
                import subprocess
                result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
                console.print(f"[green]✓[/green] {label}: {result.stdout.strip()}")
            else:
                __import__(module)
                console.print(f"[green]✓[/green] {label}")
        except (ImportError, FileNotFoundError, Exception):
            console.print(f"[red]✗[/red] {label} [yellow](not found or not working)[/yellow]")
    
    # Check Phase B
    console.print("\n[cyan bold]Phase B Status[/cyan bold]\n")
    try:
        from diagram_rendering import MermaidNativeRenderer
        console.print("[green]✓[/green] MermaidNativeRenderer available")
        console.print("  [green]Phase B will be used by default (40-60% faster)[/green]")
    except ImportError:
        console.print("[yellow]⚠[/yellow] MermaidNativeRenderer not available")
        console.print("  [yellow]Will fall back to subprocess mmdc CLI[/yellow]")
    
    console.print()


@diag_app.command()
def phase_b():
    """
    Test Phase B native Playwright renderer
    
    Renders a simple diagram and reports timing.
    """
    console.print("\n[cyan bold]Phase B Renderer Test[/cyan bold]\n")
    
    try:
        from diagram_rendering import MermaidNativeRenderer, DiagramFormat
        import tempfile
    except ImportError:
        error_hint(
            "Phase B not available",
            "MermaidNativeRenderer module not found",
            "Ensure diagram_rendering module is properly installed"
        )
        raise typer.Exit(1)
    
    # Test diagram
    test_diagram = """graph LR
    A[Start] --> B{Test Phase B}
    B --> C[Success]
    B --> D[Failed]
    C --> E[✓ Rendered]
    D --> E"""
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = MermaidNativeRenderer(
                theme="neutral",
                background="transparent"
            )
            
            svg_file = Path(tmpdir) / "test.svg"
            
            console.print("[cyan]Rendering test diagram...[/cyan]")
            start = time.time()
            result = renderer.render(
                test_diagram,
                svg_file,
                format=DiagramFormat.SVG
            )
            elapsed = time.time() - start
            
            if result.success:
                svg_size = svg_file.stat().st_size
                console.print(
                    Panel(
                        f"[green]✓ Phase B Working![/green]\n"
                        f"Render time: [yellow]{elapsed*1000:.1f}ms[/yellow]\n"
                        f"SVG size: [yellow]{svg_size} bytes[/yellow]",
                        border_style="green",
                    )
                )
            else:
                error_hint(
                    "Phase B test failed",
                    result.error_message or "Unknown error",
                    "Check Playwright installation: python -m playwright install chromium"
                )
                raise typer.Exit(1)
    
    except Exception as e:
        error_hint(
            "Phase B test failed",
            str(e),
            "Install Phase B dependencies: pip install playwright"
        )
        raise typer.Exit(1)
    
    console.print()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show version and exit",
        is_eager=True,
        callback=lambda v: None if not v else (console.print(f"docs-pipeline v{__version__}"), sys.exit(0)),
    ),
):
    """Professional document conversion pipeline"""
    pass


if __name__ == "__main__":
    app()
