from envkeep.schema import VarRule
from envkeep.validate import validate_env

RULES = {
    "DATABASE_URL": VarRule(type="url"),
    "PORT": VarRule(type="int", required=False, default="8000"),
    "SECRET_KEY": VarRule(),
    "REDIS_URL": VarRule(type="url", required=False),
}

GOOD = {"DATABASE_URL": "postgres://u:p@h:5432/db", "SECRET_KEY": "x"}


def test_valid_env_is_ok():
    assert validate_env(RULES, GOOD).ok


def test_missing_required_variable_fails():
    result = validate_env(RULES, {"SECRET_KEY": "x"})
    assert result.missing == ["DATABASE_URL"]
    assert not result.ok


def test_missing_variable_with_default_or_optional_is_fine():
    result = validate_env(RULES, GOOD)  # PORT and REDIS_URL are absent
    assert result.missing == []


def test_empty_required_variable_fails():
    result = validate_env(RULES, {**GOOD, "SECRET_KEY": ""})
    assert result.empty == ["SECRET_KEY"]
    assert not result.ok


def test_empty_optional_or_defaulted_variable_is_fine():
    result = validate_env(RULES, {**GOOD, "PORT": "", "REDIS_URL": ""})
    assert result.ok
    assert result.empty == []


def test_invalid_value_fails_and_the_message_hides_the_value():
    result = validate_env(RULES, {**GOOD, "PORT": "supersecret"})

    assert list(result.invalid) == ["PORT"]
    assert "supersecret" not in result.invalid["PORT"]
    assert not result.ok


def test_optional_variable_is_still_type_checked_when_present():
    result = validate_env(RULES, {**GOOD, "REDIS_URL": "nope"})
    assert list(result.invalid) == ["REDIS_URL"]


def test_extra_variables_are_only_warnings():
    result = validate_env(RULES, {**GOOD, "OTHER": "1"})
    assert result.extra == ["OTHER"]
    assert result.ok


def test_results_are_sorted():
    rules = {"Z": VarRule(), "A": VarRule(), "M": VarRule()}
    assert validate_env(rules, {}).missing == ["A", "M", "Z"]
