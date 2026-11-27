from envkeep.syncer import HEADER, sync_env


def test_appends_only_missing_keys():
    new_text, added = sync_env({"A": "1", "B": "2"}, "A=custom\n", {"A": "custom"})

    assert added == ["B"]
    assert "B=2" in new_text
    assert "A=1" not in new_text  # existing value was not replaced


def test_never_modifies_existing_content():
    env_text = "# my notes\nA=custom # keep me\n\nZ=extra\n"
    new_text, _ = sync_env({"A": "1", "B": "2"}, env_text, {"A": "custom", "Z": "extra"})

    assert new_text.startswith(env_text)


def test_nothing_missing_returns_text_unchanged():
    text = "A=1\n"
    assert sync_env({"A": "1"}, text, {"A": "1"}) == (text, [])


def test_adds_newline_when_file_does_not_end_with_one():
    new_text, _ = sync_env({"B": "2"}, "A=1", {"A": "1"})

    assert new_text.startswith("A=1\n")
    assert "B=2" in new_text


def test_empty_env_file():
    new_text, added = sync_env({"A": "1"}, "", {})

    assert added == ["A"]
    assert new_text == f"{HEADER}\nA=1\n"


def test_preserves_example_order():
    _, added = sync_env({"Z": "1", "A": "2"}, "", {})
    assert added == ["Z", "A"]


def test_quotes_values_with_spaces_or_hash():
    new_text, _ = sync_env({"MSG": "hello world", "TAG": "a#b"}, "", {})

    assert 'MSG="hello world"' in new_text
    assert 'TAG="a#b"' in new_text