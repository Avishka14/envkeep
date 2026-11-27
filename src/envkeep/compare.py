from envkeep.models import CheckResult


def compare(example: dict[str, str], env: dict[str, str]) -> CheckResult:
    """Compare parsed env values against the example (source of truth)."""
    example_keys = set(example)
    env_keys = set(env)

    return CheckResult(
        missing=sorted(example_keys - env_keys),
        extra=sorted(env_keys - example_keys),
        empty=sorted(key for key, value in env.items() if value == ""),
    )
