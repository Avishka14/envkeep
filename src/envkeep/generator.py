from envkeep.parser import scan


def generate_example(text: str, placeholder: str = "") -> str:
    """Turn the text of a .env file into .env.example text.

    Genuine comments, blank lines, key order, and `export` prefixes are kept.
    Every value (including multiline quoted ones) is replaced by the placeholder.
    Lines that aren't comments or assignments are dropped, since they could
    contain a stray secret.

    Raises EnvSyntaxError for an unterminated quoted value, so nothing is written
    when we can't tell where a secret ends.
    """
    out_lines: list[str] = []
    for entry in scan(text):
        if entry.kind == "raw":
            out_lines.append(entry.line)
        elif entry.kind == "assignment":
            out_lines.append(f"{entry.prefix}{entry.key}={placeholder}")
    return "\n".join(out_lines) + "\n" if out_lines else ""
