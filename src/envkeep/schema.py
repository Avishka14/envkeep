from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from envkeep.checks import TYPES, check_type

_RULE_KEYS = {"type", "required", "default"}


class SchemaError(ValueError):
    """Raised when a schema file is unreadable or invalid. Carries every problem found."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class VarRule:
    type: str = "str"
    required: bool = True
    default: str | None = None  # always stored as text, like an env value


def _parse_rule(name: str, spec: Any, problems: list[str]) -> VarRule | None:
    """Turn one variable's YAML into a VarRule, or record what is wrong with it."""
    if spec is None:
        return VarRule()  # a bare "NAME:" means a required string
    if not isinstance(spec, dict):
        problems.append(
            f"{name}: expected rules (type/required/default), not a plain value"
        )
        return None

    unknown = sorted(str(key) for key in spec if key not in _RULE_KEYS)
    if unknown:
        problems.append(
            f"{name}: unknown key(s) {', '.join(unknown)} (allowed: default, required, type)"
        )
        return None

    var_type = spec.get("type", "str")
    if var_type not in TYPES:
        problems.append(
            f"{name}: unknown type {var_type!r} (choose one of: {', '.join(TYPES)})"
        )
        return None

    required = spec.get("required")
    if required is not None and not isinstance(required, bool):
        problems.append(f"{name}: 'required' must be true or false")
        return None

    raw_default = spec.get("default")
    default: str | None = None
    if raw_default is not None:
        if isinstance(raw_default, bool):  # check bool first: bool is a subclass of int
            default = "true" if raw_default else "false"
        elif isinstance(raw_default, (int, float, str)):
            default = str(raw_default)
        else:
            problems.append(f"{name}: 'default' must be a single plain value")
            return None
        message = check_type(var_type, default)
        if message is not None:
            problems.append(
                f"{name}: the default is not a valid {var_type} ({message})"
            )
            return None

    if required is True and default is not None:
        problems.append(f"{name}: 'required: true' can't be combined with a default")
        return None

    return VarRule(
        type=var_type,
        required=(default is None) if required is None else required,
        default=default,
    )


def load_schema_text(text: str) -> dict[str, VarRule]:
    """Parse schema text into {variable name: rule}. Raises SchemaError if it's invalid."""
    try:
        data = yaml.safe_load(text)  # safe_load never builds arbitrary Python objects
    except yaml.YAMLError as exc:
        raise SchemaError([f"invalid YAML: {' '.join(str(exc).split())}"]) from exc

    if not isinstance(data, dict):
        raise SchemaError(["expected a mapping with a top-level 'variables' key"])
    unknown = sorted(str(key) for key in data if key != "variables")
    if unknown:
        raise SchemaError(
            [
                f"unknown top-level key(s): {', '.join(unknown)} (only 'variables' is allowed)"
            ]
        )

    variables = data.get("variables")
    if not isinstance(variables, dict) or not variables:
        raise SchemaError(["'variables' must be a non-empty mapping of NAME to rules"])

    problems: list[str] = []
    rules: dict[str, VarRule] = {}
    for name, spec in variables.items():
        if not isinstance(name, str):
            problems.append(
                f"variable name {name!r} was read as a non-text value; "
                'put it in quotes, e.g. "NO":'
            )
            continue
        rule = _parse_rule(name, spec, problems)
        if rule is not None:
            rules[name] = rule

    if problems:
        raise SchemaError(problems)
    return rules


def load_schema(path: Path) -> dict[str, VarRule]:
    """Read and parse a schema file."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SchemaError(["the file is not valid UTF-8"]) from exc
    return load_schema_text(text)
