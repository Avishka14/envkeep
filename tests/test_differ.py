from envkeep.differ import diff_envs


def test_reports_only_in_each_side_and_changed():
    result = diff_envs({"A": "1", "B": "2", "C": "x"}, {"B": "2", "C": "y", "D": "4"})

    assert result.only_in_a == ["A"]
    assert result.only_in_b == ["D"]
    assert result.changed == ["C"]
    assert not result.identical


def test_identical_files():
    assert diff_envs({"A": "1"}, {"A": "1"}).identical


def test_keys_only_ignores_value_differences():
    result = diff_envs({"A": "1"}, {"A": "2"}, keys_only=True)
    assert result.identical


def test_keys_only_still_reports_missing_keys():
    result = diff_envs({"A": "1"}, {"B": "1"}, keys_only=True)
    assert result.only_in_a == ["A"]
    assert result.only_in_b == ["B"]


def test_empty_value_is_different_from_a_missing_variable():
    assert diff_envs({"A": ""}, {}).only_in_a == ["A"]


def test_empty_value_differs_from_non_empty_value():
    assert diff_envs({"A": ""}, {"A": "1"}).changed == ["A"]
