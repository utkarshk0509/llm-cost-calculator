from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.pricing import PRICING_REGISTRY
from src.tokenizer import calculate_cost, count_tokens, load_text_from_path

app = typer.Typer(add_completion=False, help="Estimate LLM token counts and API costs across major providers.")
console = Console()


def run_estimate(prompt: str | None, path: Path | None, output_tokens: int, calls_per_day: int) -> None:
    if not prompt and not path:
        console.print("[bold red]Error:[/bold red] Provide either --prompt or --path.")
        raise typer.Exit(code=1)

    if path:
        if not path.exists():
            console.print(f"[bold red]Error:[/bold red] Path '{path}' does not exist.")
            raise typer.Exit(code=1)
        text, f_count = load_text_from_path(path)
        source_label = f"{path} ({f_count} files)"
    else:
        text = prompt or ""
        source_label = "Direct CLI Prompt"

    tok_count = count_tokens(text)

    console.print(
        Panel.fit(
            f"[bold cyan]Source:[/bold cyan] {source_label}\n"
            f"[bold cyan]Characters:[/bold cyan] {len(text):,}\n"
            f"[bold green]Estimated Input Tokens:[/bold green] {tok_count:,}\n"
            f"[bold yellow]Expected Output Tokens:[/bold yellow] {output_tokens:,}",
            title="Token Analysis Summary",
        )
    )

    table = Table(title=f"LLM API Cost Comparison ({calls_per_day:,} calls/day)")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="bold white")
    table.add_column("Context", justify="right")
    table.add_column("Cost / 1 Call", justify="right", style="green")
    table.add_column("Cost / 1K Calls", justify="right", style="yellow")
    table.add_column("Monthly Est. (30d)", justify="right", style="bold magenta")

    for model in sorted(PRICING_REGISTRY, key=lambda m: calculate_cost(tok_count, output_tokens, m)):
        single_cost = calculate_cost(tok_count, output_tokens, model)
        thousand_cost = single_cost * 1_000
        monthly_cost = single_cost * calls_per_day * 30

        table.add_row(
            model.provider,
            model.model,
            model.context_window,
            f"${single_cost:.6f}",
            f"${thousand_cost:.4f}",
            f"${monthly_cost:.2f}",
        )

    console.print(table)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="Direct text prompt to analyze."),
    path: Path | None = typer.Option(None, "--path", "-f", help="Path to a file or directory to scan."),
    output_tokens: int = typer.Option(500, "--output", "-o", help="Expected completion output tokens."),
    calls_per_day: int = typer.Option(100, "--calls", "-c", help="Number of daily API calls to project monthly cost."),
) -> None:
    if ctx.invoked_subcommand is None:
        run_estimate(prompt, path, output_tokens, calls_per_day)


@app.command()
def estimate(
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="Direct text prompt to analyze."),
    path: Path | None = typer.Option(None, "--path", "-f", help="Path to a file or directory to scan."),
    output_tokens: int = typer.Option(500, "--output", "-o", help="Expected completion output tokens."),
    calls_per_day: int = typer.Option(100, "--calls", "-c", help="Number of daily API calls to project monthly cost."),
) -> None:
    run_estimate(prompt, path, output_tokens, calls_per_day)


if __name__ == "__main__":
    app()