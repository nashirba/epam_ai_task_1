"""CLI entry: uv run python -m pia.cli ask "your question"."""

from __future__ import annotations

import typer
from rich import print

from pia.agents.planner import advise

app = typer.Typer(help="Personal Investment-Planning Assistant CLI")


@app.command()
def ask(question: str) -> None:
    rec = advise(question)
    print(f"[bold]{rec.summary}[/]\n")
    print(f"[dim]{rec.disclaimer}[/]")


if __name__ == "__main__":
    app()
