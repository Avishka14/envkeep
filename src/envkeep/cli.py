from pathlib import Path

import typer

from envkeep.compare import compare
from envkeep.generator import generate_example
from envkeep.output import (
    print_check_result,
    print_error,
    print_success,
    print_sync_result,
)
from envkeep.parser import parse_env_file
from envkeep.syncer import sync_env

app = typer.Typer(
    help="Keep your .env files in sync with .env.example.",
    no_args_is_help=True,
)


def _require_files(*paths: Path) -> None:
    """Exit with code 2 if any of the given files doesn't exist."""
    for path in paths:
        if not path.is_file():
            print_error(f"file not found: {path}")
            raise typer.Exit(code=2)

def _is_same_file(a: Path, b: Path) -> bool:
    """True if both paths point at the same file, including hard links and symlinks."""
    if a.resolve() == b.resolve():
        return True  # same path after resolving symlinks (works even if b doesn't exist yet)
    return b.exists() and a.samefile(b)  # same file under different names, e.g. a hard link


@app.callback()
def main() -> None:
    """Keep your .env files in sync with .env.example."""


@app.command()
def check(
    env: Path = typer.Option(
        Path(".env"), "--env", "-e", help="The .env file to check."
    ),
    example: Path = typer.Option(
        Path(".env.example"),
        "--example",
        "-x",
        help="The file used as the source of truth.",
    ),
) -> None:
    """Compare a .env file against .env.example.

    Exits with code 1 if variables are missing or empty, so it works in CI.
    """
    _require_files(env, example)
    result = compare(parse_env_file(example), parse_env_file(env))
    print_check_result(result, env, example)
    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def generate(
    env: Path = typer.Option(
        Path(".env"), "--env", "-e", help="The .env file to read."
    ),
    output: Path = typer.Option(
        Path(".env.example"), "--output", "-o", help="Where to write the example file."
    ),
    placeholder: str = typer.Option(
        "", "--placeholder", "-p", help="Value to put after each key."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite the output file if it already exists."
    ),
) -> None:
    """Build .env.example from .env, stripping the values but keeping comments."""
    _require_files(env)
    if _is_same_file(env, output):
        print_error(
            "--env and --output are the same file; refusing to overwrite your values"
        )
        raise typer.Exit(code=2)
    if output.exists() and not force:
        print_error(f"{output} already exists (use --force to overwrite)")
        raise typer.Exit(code=2)

    text = env.read_text(encoding="utf-8")
    output.write_text(generate_example(text, placeholder), encoding="utf-8")
    print_success(f"wrote {len(parse_env_file(env))} variables to {output}")


@app.command()
def sync(
    env: Path = typer.Option(
        Path(".env"), "--env", "-e", help="The .env file to update."
    ),
    example: Path = typer.Option(
        Path(".env.example"),
        "--example",
        "-x",
        help="The file used as the source of truth.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be added without writing anything."
    ),
) -> None:
    """Add variables that are in .env.example but missing from .env.

    Existing variables and values are never changed.
    """
    _require_files(env, example)
    
    # newline="" turns off newline translation, so existing \r\n endings survive untouched
    with env.open(encoding="utf-8", newline="") as handle:
        env_text = handle.read()
    new_text, added = sync_env(parse_env_file(example), env_text, parse_env_file(env))

    if added and not dry_run:
        with env.open("w", encoding="utf-8", newline="") as handle:
            handle.write(new_text)
    print_sync_result(added, env, dry_run)
