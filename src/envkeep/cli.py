from pathlib import Path

import typer

from envkeep.compare import compare
from envkeep.output import print_check_result, print_error
from envkeep.parser import parse_env_file

app = typer.Typer(
    help="Keep your .env files in sync with .env.example.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Keep your .env files in sync with .env.example."""


@app.command()
def check(
    env: Path = typer.Option(
        Path(".env"), "--env", "-e", help="The .env file to check."
    ),
    example: Path = typer.Option(
        Path(".env.example"), "--example", "-x", help="The file used as the source of truth."
    ),
) -> None:
    """Compare a .env file against .env.example.

    Exits with code 1 if variables are missing or empty, so it works in CI.
    """
    for path in (env, example):
        if not path.is_file():
            print_error(f"file not found: {path}")
            raise typer.Exit(code=2)

    result = compare(parse_env_file(example), parse_env_file(env))
    print_check_result(result, env, example)
    if not result.ok:
        raise typer.Exit(code=1)