"""CLI interface using Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from repo2ctx.pipeline import run

app = typer.Typer(
    name="repo2ctx",
    help="Intelligently prepare your codebase as LLM context.",
    no_args_is_help=True,
)
console = Console(stderr=True)


@app.command()
def main(
    path: Annotated[
        Path,
        typer.Argument(help="Root directory to analyze."),
    ],
    max_tokens: Annotated[
        int,
        typer.Option("--max-tokens", "-t", help="Token budget."),
    ] = 128_000,
    focus: Annotated[
        list[str] | None,
        typer.Option("--focus", "-f", help="Focus on specific file/directory."),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option("--format", help="Output format: markdown, xml, json."),
    ] = "markdown",
    include: Annotated[
        list[str] | None,
        typer.Option("--include", "-i", help="Include only matching files (glob)."),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", "-e", help="Exclude matching files (glob)."),
    ] = None,
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Token model: openai or claude."),
    ] = "openai",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write output to file."),
    ] = None,
) -> None:
    """Analyze a codebase and produce LLM-optimized context."""
    if not path.is_dir():
        console.print(f"[red]Error:[/red] {path} is not a directory.")
        raise typer.Exit(code=1)

    if fmt not in ("markdown", "xml", "json"):
        console.print(f"[red]Error:[/red] Unknown format '{fmt}'. Use markdown, xml, or json.")
        raise typer.Exit(code=1)

    console.print(f"[bold]repo2ctx[/bold] analyzing [cyan]{path}[/cyan]...")

    result = run(
        root=path,
        max_tokens=max_tokens,
        focus=focus,
        fmt=fmt,
        include=include,
        exclude=exclude,
        model=model,
    )

    if output:
        output.write_text(result, encoding="utf-8")
        console.print(f"[green]Output written to {output}[/green]")
    else:
        # Print to stdout (not stderr console)
        print(result)

    console.print("[green]Done![/green]")
