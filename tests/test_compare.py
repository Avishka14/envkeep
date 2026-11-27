from envkeep.compare import compare


def test_reports_missing_extra_and_empty():
    example = {"PORT": "8000", "DEBUG": "false", "SECRET": "x"}
    env = {"PORT": "", "DEBUG": "true", "REDIS": "localhost"}

    result = compare(example, env)

    assert result.missing == ["SECRET"]
    assert result.extra == ["REDIS"]
    assert result.empty == ["PORT"]
    assert not result.ok


def test_identical_files_are_ok():
    values = {"A": "1", "B": "2"}
    result = compare(values, dict(values))
    assert result.ok
    assert result.missing == result.extra == result.empty == []


def test_extra_variables_are_only_warnings():
    result = compare({"A": "1"}, {"A": "1", "B": "2"})
    assert result.extra == ["B"]
    assert result.ok


def test_missing_variable_fails():
    assert not compare({"A": "1"}, {}).ok


def test_empty_variable_fails():
    assert not compare({"A": "1"}, {"A": ""}).ok


def test_results_are_sorted():
    result = compare({"Z": "1", "A": "1", "M": "1"}, {})
    assert result.missing == ["A", "M", "Z"]
