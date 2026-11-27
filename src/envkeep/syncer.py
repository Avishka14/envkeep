HEADER = "# Added by envkeep sync"


_ESCAPES = str.maketrans({"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r"})


def _needs_quotes(value: str) -> bool:
    """Whitespace, '#', or a quote character would be misread in an unquoted value."""
    return any(char.isspace() or char in "#'\"" for char in value)


def _format_value(value: str) -> str:
    """Serialize a value so both envkeep and python-dotenv read back the same string."""
    if not _needs_quotes(value):
        return value
    return '"' + value.translate(_ESCAPES) + '"'


def _detect_newline(text: str) -> str:
    """Return the line ending the text already uses (the first one found), default LF."""
    index = text.find("\n")
    if index > 0 and text[index - 1] == "\r":
        return "\r\n"
    return "\n"


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

    newline = _detect_newline(env_text)
    lines = [HEADER] + [f"{key}={_format_value(example[key])}" for key in added]

    separator = ""
    if env_text:
        separator = newline if env_text.endswith("\n") else newline * 2

    return env_text + separator + newline.join(lines) + newline, added
