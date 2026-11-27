from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


class EnvSyntaxError(ValueError):
    """Raised when an env file can't be read safely (e.g. an unterminated quote)."""

    def __init__(self, message: str, line_number: int) -> None:
        super().__init__(f"line {line_number}: {message}")
        self.line_number = line_number


@dataclass(frozen=True)
class Entry:
    """One logical item in an env file."""

    kind: Literal["raw", "ignored", "assignment"]
    line: str = ""  # raw: the original line (blank lines and real comments)
    prefix: str = ""  # assignment: "export " or ""
    key: str = ""  # assignment
    value: str = ""  # assignment: the value, without quotes or inline comment


def _find_closing_quote(chunk: str, quote: str) -> int:
    """Index of the first unescaped closing quote in chunk, or -1."""
    escaped = False
    for index, char in enumerate(chunk):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == quote:
            return index
    return -1


def _read_quoted(
    lines: list[str], start: int, first_chunk: str, key: str
) -> tuple[str, int]:
    """Read a quoted value that may continue over several lines.

    Returns (value, index of the next unread line).
    """
    quote = first_chunk[0]
    chunk = first_chunk[1:]
    collected: list[str] = []
    index = start
    while True:
        end = _find_closing_quote(chunk, quote)
        if end != -1:
            collected.append(chunk[:end])  # anything after the closing quote is ignored
            return "\n".join(collected), index + 1
        collected.append(chunk)
        index += 1
        if index >= len(lines):
            raise EnvSyntaxError(f"unterminated quoted value for {key}", start + 1)
        chunk = lines[index]


def scan(text: str) -> Iterator[Entry]:
    """Split env file text into logical entries.

    A quoted value that spans several lines is ONE assignment, so the lines inside
    it are never mistaken for comments or other variables.
    """
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            yield Entry("raw", line=raw)
            index += 1
            continue

        body = raw.lstrip()
        prefix = ""
        if body.startswith("export "):
            prefix = "export "
            body = body[len(prefix) :]

        if "=" not in body:
            yield Entry("ignored")
            index += 1
            continue

        key, _, rest = body.partition("=")  # splits on the FIRST "=" only
        key = key.strip()
        rest = rest.lstrip()

        if rest[:1] in ('"', "'"):
            value, index = _read_quoted(lines, index, rest, key)
        else:
            value = rest.split(" #", 1)[0].strip()  # drop inline comment
            index += 1

        yield Entry("assignment", prefix=prefix, key=key, value=value)


def parse_env_text(text: str) -> dict[str, str]:
    """Parse env file text into {KEY: value}."""
    return {
        entry.key: entry.value for entry in scan(text) if entry.kind == "assignment"
    }


def parse_env_file(path: Path) -> dict[str, str]:
    """Read a .env file and return {KEY: value}."""
    return parse_env_text(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys

    for key, value in parse_env_file(Path(sys.argv[1])).items():
        print(f"{key!r} -> {value!r}")
