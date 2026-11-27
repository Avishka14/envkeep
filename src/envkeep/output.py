from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from envkeep.models import CheckResult

console = Console()
err_console = Console(stderr=True)

_STYLES = {"missing": "red", "empty": "yellow", "extra": "blue"}


def print_check_result(result: CheckResult, env: Path, example: Path) -> None:
    """Print a check result as a colored table plus a one-line summary."""
    env_label = escape(str(env))
    example_label = escape(str(example))

    rows = (
        [("missing", key) for key in result.missing]
        + [("empty", key) for key in result.empty]
        + [("extra", key) for key in result.extra]
    )

    if not rows:
        console.print(f"[green]OK[/green] {env_label} matches {example_label}")
        return

    table = Table(title=f"{env_label} vs {example_label}")
    table.add_column("Status")
    table.add_column("Variable")
    for status, key in rows:
        style = _STYLES[status]
        table.add_row(f"[{style}]{status}[/{style}]", escape(key))
    console.print(table)

    summary = (
        f"{len(result.missing)} missing, "
        f"{len(result.empty)} empty, "
        f"{len(result.extra)} extra"
    )
    if result.ok:
        console.print(f"[green]OK[/green] {summary} (extra variables are only warnings)")
    else:
        console.print(f"[red]FAILED[/red] {summary}")


def print_error(message: str) -> None:
    """Print an error to stderr, so it doesn't mix with normal output."""
    err_console.print(f"[red]error:[/red] {escape(message)}")


def print_success(message: str) -> None:
    """Print a green OK line."""
    console.print(f"[green]OK[/green] {escape(message)}")
    

def print_sync_result(added: list[str], env: Path, dry_run: bool) -> None:
    """Print which variables were (or would be) added to the env file."""
    env_label = escape(str(env))
    if not added:
        console.print(f"[green]OK[/green] {env_label} already has every variable")
        return

    verb = "Would add" if dry_run else "Added"
    console.print(f"[green]{verb}[/green] {len(added)} variable(s) to {env_label}:")
    for key in added:
        console.print(f"  + {escape(key)}")