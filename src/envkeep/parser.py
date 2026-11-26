from pathlib import Path


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_env_file(path: Path) -> dict[str, str]:
    """Read a .env file and return {KEY: value}."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue  # skip blanks and comments
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue  # not a KEY=VALUE line
        key, _, value = line.partition("=")  # splits on the FIRST "=" only
        key = key.strip()
        value = value.strip()
        if value and value[0] not in "\"'":
            value = value.split(" #", 1)[0].strip()  # drop inline comment
        values[key] = _strip_quotes(value)
    return values


if __name__ == "__main__":
    import sys

    for key, value in parse_env_file(Path(sys.argv[1])).items():
        print(f"{key!r} -> {value!r}")