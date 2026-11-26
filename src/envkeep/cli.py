import typer

app = typer.Typer(
    help="Keep your .env files in sync with .env.example.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Keep your .env files in sync with .env.example."""


@app.command()
def check() -> None:
    """Compare a .env file against .env.example."""
    typer.echo("check: not implemented yet")