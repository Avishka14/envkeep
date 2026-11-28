from pathlib import Path
from typing import Annotated, Optional

import typer

from envkeep.compare import compare
from envkeep.differ import diff_envs
from envkeep.fileio import atomic_write_text
from envkeep.generator import generate_example
from envkeep.output import (
    print_check_result,
    print_diff_result,
    print_error,
    print_success,
    print_sync_result,
)
from envkeep.parser import EnvSyntaxError, parse_env_file, parse_env_text
from envkeep.schema import SchemaError, VarRule, load_schema
from envkeep.syncer import sync_env
from envkeep.validate import validate_env

DEFAULT_ENV = Path(".env")
DEFAULT_EXAMPLE = Path(".env.example")

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
        return (
            True  # same path after resolving symlinks (works even if b doesn't exist)
        )
    return b.exists() and a.samefile(
        b
    )  # same file under different names, e.g. a hard link


def _read_env(path: Path) -> dict[str, str]:
    """Parse an env file, turning a syntax error into a clean message and exit code 2."""
    try:
        return parse_env_file(path)
    except EnvSyntaxError as exc:
        print_error(f"{path}: {exc}")
        raise typer.Exit(code=2) from exc
    

def _load_schema(path: Path) -> dict[str, VarRule]:
    """Load a schema, turning every problem into a clean message and exit code 2."""
    try:
        return load_schema(path)
    except SchemaError as exc:
        for problem in exc.problems:
            print_error(f"{path}: {problem}")
        raise typer.Exit(code=2) from exc


@app.callback()
def main() -> None:
    """Keep your .env files in sync with .env.example."""


@app.command()
def check(
    env: Annotated[
        Path, typer.Option("--env", "-e", help="The .env file to check.")
    ] = DEFAULT_ENV,
    example: Annotated[
        Path,
        typer.Option("--example", "-x", help="The file used as the source of truth."),
    ] = DEFAULT_EXAMPLE,
    schema: Annotated[
        Optional[Path],
        typer.Option(
            "--schema",
            "-s",
            help="An envkeep.yml schema to validate against. When given, it replaces --example.",
        ),
    ] = None,
) -> None:
    """Check a .env file against .env.example or an envkeep.yml schema.

    Exits with code 1 if variables are missing, empty, or invalid, so it works in CI.
    """
    if schema is not None:
        _require_files(env, schema)
        result = validate_env(_load_schema(schema), _read_env(env))
        print_check_result(result, env, schema)
    else:
        _require_files(env, example)
        result = compare(_read_env(example), _read_env(env))
        print_check_result(result, env, example)

    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def generate(
    env: Annotated[
        Path, typer.Option("--env", "-e", help="The .env file to read.")
    ] = DEFAULT_ENV,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Where to write the example file."),
    ] = DEFAULT_EXAMPLE,
    placeholder: Annotated[
        str, typer.Option("--placeholder", "-p", help="Value to put after each key.")
    ] = "",
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Overwrite the output file if it already exists."
        ),
    ] = False,
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
    try:
        content = generate_example(text, placeholder)
    except EnvSyntaxError as exc:
        print_error(f"{env}: {exc}")
        raise typer.Exit(code=2) from exc

    output.write_text(content, encoding="utf-8")
    print_success(f"wrote {len(parse_env_text(text))} variables to {output}")


@app.command()
def sync(
    env: Annotated[
        Path, typer.Option("--env", "-e", help="The .env file to update.")
    ] = DEFAULT_ENV,
    example: Annotated[
        Path,
        typer.Option("--example", "-x", help="The file used as the source of truth."),
    ] = DEFAULT_EXAMPLE,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Show what would be added without writing anything."
        ),
    ] = False,
) -> None:
    """Add variables that are in .env.example but missing from .env.

    Existing variables and values are never changed.
    """
    _require_files(env, example)

    # newline="" turns off newline translation, so existing \r\n endings survive untouched
    with env.open(encoding="utf-8", newline="") as handle:
        env_text = handle.read()
    new_text, added = sync_env(_read_env(example), env_text, _read_env(env))

    if added and not dry_run:
        try:
            atomic_write_text(env, new_text)
        except OSError as exc:
            print_error(f"could not write {env}: {exc}")
            raise typer.Exit(code=2) from exc
    print_sync_result(added, env, dry_run)


@app.command()
def diff(
    first: Annotated[Path, typer.Argument(help="The first env file (A).")],
    second: Annotated[Path, typer.Argument(help="The second env file (B).")],
    show_values: Annotated[
        bool,
        typer.Option(
            "--show-values",
            help="Show the values too. They may be secrets, so they are hidden by default.",
        ),
    ] = False,
    keys_only: Annotated[
        bool,
        typer.Option(
            "--keys-only",
            help="Compare only which variables exist, ignoring value differences.",
        ),
    ] = False,
) -> None:
    """Show the differences between two env files, for example dev vs staging.

    Values are hidden by default. Exits with code 1 if the files differ.
    """
    _require_files(first, second)
    first_values = _read_env(first)
    second_values = _read_env(second)

    result = diff_envs(first_values, second_values, keys_only=keys_only)
    print_diff_result(
        result,
        first,
        second,
        first_values,
        second_values,
        show_values=show_values,
        keys_only=keys_only,
    )
    if not result.identical:
        raise typer.Exit(code=1)
