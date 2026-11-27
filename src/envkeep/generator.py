def generate_example(text: str, placeholder: str = "") -> str:
    """Turn the text of a .env file into .env.example text.

    Comments, blank lines, key order, and `export` prefixes are kept.
    Every value, and any inline comment after it, is replaced by the placeholder.
    Lines that are neither comments nor KEY=VALUE are dropped, since the parser
    ignores them and they could contain a stray secret.
    """
    out_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        if not stripped or stripped.startswith("#"):
            out_lines.append(raw_line)  # keep blank lines and comments
            continue
        if "=" not in stripped:
            continue  # not a variable: drop it

        prefix = ""
        if stripped.startswith("export "):
            prefix = "export "
            stripped = stripped[len("export ") :]

        key, _, _ = stripped.partition("=")
        out_lines.append(f"{prefix}{key.strip()}={placeholder}")

    return "\n".join(out_lines) + "\n" if out_lines else ""
