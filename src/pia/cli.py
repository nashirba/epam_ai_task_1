"""CLI entry: uv run python -m pia.cli ask "your question"."""

from __future__ import annotations

import typer
from rich import print

from pia.agents.planner import advise
from pia.config import get_settings

app = typer.Typer(
    help="Personal Investment-Planning Assistant CLI",
    no_args_is_help=True,
)


@app.command()
def ask(question: str) -> None:
    """Ask the planner a question; prints the recommendation and the disclaimer."""
    rec = advise(question)
    print(f"[bold]{rec.summary}[/]\n")
    print(f"[dim]{rec.disclaimer}[/]")


@app.command()
def info() -> None:
    """Show the active configuration (model, embeddings, Weaviate host)."""
    s = get_settings()
    print(f"LLM model:      {s.llm_model}")
    print(f"Embedding:      {s.embedding_provider} / {s.embedding_model}")
    print(f"Weaviate:       {s.weaviate_host}:{s.weaviate_http_port}")


if __name__ == "__main__":
    app()
