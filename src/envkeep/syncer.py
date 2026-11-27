HEADER = "# Added by envkeep sync"


def _format_value(value: str) -> str:
    """Quote values that would be misread without quotes (spaces or #)."""
    if any(char.isspace() or char == "#" for char in value):
        quote = "'" if '"' in value else '"'
        return f"{quote}{value}{quote}"
    return value


def sync_env(
    example: dict[str, str], env_text: str, env: dict[str, str]
) -> tuple[str, list[str]]:
    """Append variables that exist in the example but not in the env file.

    Returns (new_text, added_keys). Existing content is never modified:
    the new text always starts with the old text.
    """
    added = [key for key in example if key not in env]  # keeps the example's order
    if not added:
        return env_text, added

    lines = [HEADER] + [f"{key}={_format_value(example[key])}" for key in added]

    separator = ""
    if env_text:
        separator = "\n" if env_text.endswith("\n") else "\n\n"

    return env_text + separator + "\n".join(lines) + "\n", added
