from envkeep.checks import check_type
from envkeep.models import CheckResult
from envkeep.schema import VarRule


def validate_env(rules: dict[str, VarRule], env: dict[str, str]) -> CheckResult:
    """Check parsed env values against schema rules.

    - a required variable that is absent is "missing"; if it is blank, "empty"
    - an optional variable (required: false, or one with a default) may be absent or blank
    - any non-blank value must pass its type check, otherwise it is "invalid"
    - variables the schema doesn't mention are reported as "extra" (a warning)
    """
    missing: list[str] = []
    empty: list[str] = []
    invalid: dict[str, str] = {}

    for name, rule in rules.items():
        if name not in env:
            if rule.required:
                missing.append(name)
            continue

        value = env[name]
        if value == "":
            if rule.required:
                empty.append(name)
            continue

        problem = check_type(rule.type, value)
        if problem is not None:
            invalid[name] = problem

    return CheckResult(
        missing=sorted(missing),
        extra=sorted(set(env) - set(rules)),
        empty=sorted(empty),
        invalid=dict(sorted(invalid.items())),
    )
