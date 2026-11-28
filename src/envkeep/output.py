from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from envkeep.differ import DiffResult
from envkeep.models import CheckResult

console = Console()
err_console = Console(stderr=True)

_STYLES = {"missing": "red", "empty": "yellow", "invalid": "magenta", "extra": "blue"}


def print_check_result(result: CheckResult, env: Path, source: Path) -> None:
    """Print a check result as a colored table plus a one-line summary."""
    env_label = escape(str(env))
    source_label = escape(str(source))

    rows = (
        [("missing", key, "") for key in result.missing]
        + [("empty", key, "") for key in result.empty]
        + [("invalid", key, problem) for key, problem in result.invalid.items()]
        + [("extra", key, "") for key in result.extra]
    )

    if not rows:
        console.print(f"[green]OK[/green] {env_label} matches {source_label}")
        return

    table = Table(title=f"{env_label} vs {source_label}")
    table.add_column("Status")
    table.add_column("Variable")
    if result.invalid:
        table.add_column("Problem")
    for status, key, problem in rows:
        style = _STYLES[status]
        cells = [f"[{style}]{status}[/{style}]", escape(key)]
        if result.invalid:
            cells.append(escape(problem))
        table.add_row(*cells)
    console.print(table)

    summary = f"{len(result.missing)} missing, {len(result.empty)} empty, "
    if result.invalid:
        summary += f"{len(result.invalid)} invalid, "
    summary += f"{len(result.extra)} extra"

    if result.ok:
        console.print(
            f"[green]OK[/green] {summary} (extra variables are only warnings)"
        )
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


def _show(value: str | None) -> str:
    """Render one value cell. Escaped, because values come from the user's files."""
    if value is None:
        return "[dim]-[/dim]"
    if value == "":
        return "[dim](empty)[/dim]"
    return escape(value)


def print_diff_result(
    result: DiffResult,
    first: Path,
    second: Path,
    first_values: dict[str, str],
    second_values: dict[str, str],
    *,
    show_values: bool = False,
    keys_only: bool = False,
) -> None:
    """Print the differences between two env files. Values are hidden unless asked for."""
    first_label = escape(str(first))
    second_label = escape(str(second))

    if result.identical:
        what = "have the same variables" if keys_only else "are identical"
        console.print(f"[green]OK[/green] {first_label} and {second_label} {what}")
        return

    rows = (
        [(key, "only in A", "red") for key in result.only_in_a]
        + [(key, "only in B", "blue") for key in result.only_in_b]
        + [(key, "changed", "yellow") for key in result.changed]
    )

    table = Table(title=f"A: {first_label}\nB: {second_label}")
    table.add_column("Variable")
    table.add_column("Status")
    if show_values:
        table.add_column("A value")
        table.add_column("B value")

    for key, status, style in sorted(rows):
        cells = [escape(key), f"[{style}]{status}[/{style}]"]
        if show_values:
            cells.append(_show(first_values.get(key)))
            cells.append(_show(second_values.get(key)))
        table.add_row(*cells)
    console.print(table)

    console.print(
        f"[yellow]DIFFERENT[/yellow] {len(result.only_in_a)} only in A, "
        f"{len(result.only_in_b)} only in B, {len(result.changed)} changed"
    )
