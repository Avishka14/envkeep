from __future__ import annotations

import re
from urllib.parse import urlsplit

_INT = re.compile(r"[+-]?[0-9]+")
_FLOAT = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_BOOLS = {"true", "false", "yes", "no", "on", "off", "1", "0"}


def _is_str(value: str) -> bool:
    return True


def _is_int(value: str) -> bool:
    return _INT.fullmatch(value) is not None


def _is_float(value: str) -> bool:
    return _FLOAT.fullmatch(value) is not None


def _is_bool(value: str) -> bool:
    return value.lower() in _BOOLS


def _is_url(value: str) -> bool:
    if any(char.isspace() for char in value):
        return False
    try:
        parts = urlsplit(value)
        _ = parts.port  # raises ValueError for a non-numeric or out-of-range port
        hostname = parts.hostname  # None when the host part is empty, e.g. "http://:80"
    except ValueError:
        return False
    return bool(parts.scheme and hostname)


_CHECKS = {
    "str": _is_str,
    "int": _is_int,
    "float": _is_float,
    "bool": _is_bool,
    "url": _is_url,
}

_MESSAGES = {
    "int": "expected an integer",
    "float": "expected a number",
    "bool": "expected a boolean (true/false, yes/no, on/off, 1/0)",
    "url": "expected a URL such as scheme://host",
}

TYPES = tuple(_CHECKS)  # ("str", "int", "float", "bool", "url")


def check_type(type_name: str, value: str) -> str | None:
    """Return None if the value suits the type, otherwise a short problem description.

    The description never contains the value itself, because it might be a secret.
    """
    if _CHECKS[type_name](value):
        return None
    return _MESSAGES[type_name]
