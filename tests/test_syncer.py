import io

import pytest
from dotenv import dotenv_values

from envkeep.parser import parse_env_text
from envkeep.syncer import HEADER, sync_env


def test_appends_only_missing_keys():
    new_text, added = sync_env({"A": "1", "B": "2"}, "A=custom\n", {"A": "custom"})

    assert added == ["B"]
    assert "B=2" in new_text
    assert "A=1" not in new_text  # existing value was not replaced


def test_never_modifies_existing_content():
    env_text = "# my notes\nA=custom # keep me\n\nZ=extra\n"
    new_text, _ = sync_env(
        {"A": "1", "B": "2"}, env_text, {"A": "custom", "Z": "extra"}
    )

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


def test_appended_lines_use_crlf_when_file_uses_crlf():
    env_text = "A=1\r\n"
    new_text, _ = sync_env({"B": "2"}, env_text, {"A": "1"})

    assert new_text.startswith(env_text)
    assert new_text == f"A=1\r\n\r\n{HEADER}\r\nB=2\r\n"
    assert "\n" not in new_text.replace("\r\n", "")  # no bare LF anywhere


def test_lf_file_stays_lf():
    new_text, _ = sync_env({"B": "2"}, "A=1\n", {"A": "1"})
    assert "\r" not in new_text


def test_trailing_comment_after_quoted_value_is_not_copied():
    example = parse_env_text('NAME="hello" # note\n')

    new_text, _ = sync_env(example, "", {})

    assert "NAME=hello\n" in new_text
    assert "# note" not in new_text


def test_hash_inside_quotes_is_kept_and_trailing_comment_dropped():
    example = parse_env_text("TAG='a # b' # note\n")

    new_text, _ = sync_env(example, "", {})

    assert 'TAG="a # b"\n' in new_text
    assert "# note" not in new_text


def test_apostrophe_and_double_quotes_are_escaped():
    value = 'it\'s "ready now"'

    new_text, _ = sync_env({"MESSAGE": value}, "", {})

    assert 'MESSAGE="it\'s \\"ready now\\""' in new_text


@pytest.mark.parametrize(
    "value",
    [
        "hello world",
        "a#b",
        "it's",
        'say "hi"',
        'it\'s "ready now"',
        r"C:\dir\file name",
        "line1\nline2",
        " padded ",
        '"starts with a quote',
        "tab\there",
        "'token'",
        '"token"',
        "'",
        '"',
        "ab'cd",
    ],
)
def test_synced_values_round_trip(value):
    new_text, _ = sync_env({"KEY": value}, "", {})

    assert parse_env_text(new_text)["KEY"] == value
    assert dotenv_values(stream=io.StringIO(new_text))["KEY"] == value


def test_multiline_value_is_written_on_one_line():
    new_text, _ = sync_env({"KEY": "a\nb"}, "A=1\r\n", {"A": "1"})

    assert 'KEY="a\\nb"' in new_text
    assert "a\nb" not in new_text


def test_value_that_starts_with_a_quote_is_quoted():
    new_text, _ = sync_env({"A": "'token'"}, "", {})

    assert new_text.endswith("A=\"'token'\"\n")


def test_ordinary_values_stay_unquoted():
    new_text, _ = sync_env({"A": "token", "PORT": "8000", "PATH_X": r"C:\dir"}, "", {})

    assert "A=token\n" in new_text
    assert "PORT=8000\n" in new_text
    assert "PATH_X=C:\\dir\n" in new_text
