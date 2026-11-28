import textwrap
from pathlib import Path

import pytest

from envkeep.schema import SchemaError, VarRule, load_schema, load_schema_text


def load(text):
    return load_schema_text(textwrap.dedent(text))


def problems_of(text):
    with pytest.raises(SchemaError) as excinfo:
        load(text)
    return excinfo.value.problems


def test_loads_all_rule_shapes():
    rules = load(
        """
        variables:
          DATABASE_URL:
            type: url
          PORT:
            type: int
            default: 8000
          DEBUG:
            type: bool
            default: false
          SECRET_KEY:
          REDIS_URL:
            required: false
        """
    )

    assert rules["DATABASE_URL"] == VarRule(type="url", required=True, default=None)
    assert rules["PORT"] == VarRule(type="int", required=False, default="8000")
    assert rules["DEBUG"] == VarRule(type="bool", required=False, default="false")
    assert rules["SECRET_KEY"] == VarRule(type="str", required=True, default=None)
    assert rules["REDIS_URL"] == VarRule(type="str", required=False, default=None)


def test_unknown_type_is_rejected():
    assert any(
        "unknown type" in p for p in problems_of("variables:\n  A:\n    type: color\n")
    )


def test_unknown_rule_key_catches_typos():
    problems = problems_of("variables:\n  A:\n    requried: false\n")
    assert any("unknown key" in p and "requried" in p for p in problems)


def test_required_true_with_a_default_is_rejected():
    problems = problems_of("variables:\n  A:\n    required: true\n    default: x\n")
    assert any("can't be combined" in p for p in problems)


def test_default_must_match_the_type():
    problems = problems_of("variables:\n  A:\n    type: int\n    default: abc\n")
    assert any("default is not a valid int" in p for p in problems)


def test_required_must_be_a_boolean():
    assert any(
        "'required' must be" in p
        for p in problems_of("variables:\n  A:\n    required: maybe\n")
    )


def test_default_must_be_a_plain_value():
    assert any(
        "plain value" in p
        for p in problems_of("variables:\n  A:\n    default: [1, 2]\n")
    )


def test_rules_must_be_a_mapping():
    assert any("expected rules" in p for p in problems_of("variables:\n  A: int\n"))


def test_unknown_top_level_key_is_rejected():
    assert any("top-level" in p for p in problems_of("vars:\n  A:\n"))


@pytest.mark.parametrize(
    "text", ["", "- just\n- a list\n", "variables:\n", "variables: {}\n"]
)
def test_structurally_invalid_schemas(text):
    with pytest.raises(SchemaError):
        load_schema_text(text)


def test_yaml_syntax_error_is_reported():
    assert any("invalid YAML" in p for p in problems_of("variables: [\n"))


def test_variable_name_read_as_boolean_gets_a_hint():
    problems = problems_of("variables:\n  NO:\n")
    assert any("quotes" in p for p in problems)


def test_reports_every_problem_at_once():
    problems = problems_of("variables:\n  A:\n    type: color\n  B:\n    type: shape\n")
    assert len(problems) == 2


def test_load_schema_reads_a_file(tmp_path):
    path = tmp_path / "envkeep.yml"
    path.write_text("variables:\n  A:\n    type: int\n", encoding="utf-8")

    assert load_schema(path) == {"A": VarRule(type="int", required=True, default=None)}


def test_load_schema_rejects_non_utf8_files(tmp_path):
    path = tmp_path / "envkeep.yml"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(SchemaError):
        load_schema(path)


def test_duplicate_variable_is_rejected():
    problems = problems_of(
        "variables:\n  PORT:\n    type: int\n  PORT:\n    required: false\n"
    )
    assert any("duplicate key" in p and "line 4" in p for p in problems)


def test_duplicate_rule_key_is_rejected():
    problems = problems_of("variables:\n  A:\n    type: int\n    type: str\n")
    assert any("duplicate key" in p and "line 4" in p for p in problems)


def test_duplicate_top_level_key_is_rejected():
    problems = problems_of("variables:\n  A:\nvariables:\n  B:\n")
    assert any("duplicate key" in p for p in problems)


def test_duplicate_error_includes_a_line_number():
    problems = problems_of("variables:\n  A:\n  A:\n")
    assert any("line 3" in p for p in problems)


def test_unique_keys_are_still_valid():
    rules = load("variables:\n  A:\n    type: int\n  B:\n    type: bool\n")
    assert set(rules) == {"A", "B"}


def test_merge_keys_may_still_be_overridden():
    rules = load(
        """
        variables:
          A: &base
            type: int
            required: false
          B:
            <<: *base
            type: str
        """
    )
    assert rules["A"].type == "int"
    assert rules["B"].type == "str"
    assert rules["B"].required is False


def test_syntax_error_reports_position_but_not_source_text():
    problems = problems_of('variables:\n  A:\n    default: "supersecret\n')

    assert any("line" in p and "column" in p for p in problems)
    assert not any("supersecret" in p for p in problems)


def test_undefined_alias_name_is_not_echoed():
    problems = problems_of("variables:\n  A:\n    default: *supersecret\n")

    assert problems
    assert not any("supersecret" in p for p in problems)


def test_yaml_error_is_not_chained_to_the_original_exception():
    with pytest.raises(SchemaError) as excinfo:
        load_schema_text('variables:\n  A:\n    default: "supersecret\n')

    assert excinfo.value.__cause__ is None
    assert "supersecret" not in str(excinfo.value)


def test_odd_duplicate_key_is_reported_without_echoing_it():
    problems = problems_of('variables:\n  A:\n  "my secret key":\n  "my secret key":\n')

    assert any("duplicate key" in p and "line 4" in p for p in problems)
    assert not any("secret" in p for p in problems)


def test_unreadable_schema_file_raises_schema_error(tmp_path, monkeypatch):
    path = tmp_path / "envkeep.yml"
    path.write_text("variables:\n  A:\n", encoding="utf-8")

    def deny(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "read_text", deny)

    with pytest.raises(SchemaError) as excinfo:
        load_schema(path)

    assert "could not read the file" in str(excinfo.value)
    assert "Permission denied" in str(excinfo.value)


def test_schema_path_that_is_a_directory_raises_schema_error(tmp_path):
    with pytest.raises(SchemaError):
        load_schema(tmp_path)
