import textwrap

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
