from pathlib import Path

from dotenv import dotenv_values

from envkeep.parser import parse_env_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_simple_pairs(write_env):
    path = write_env("A=1\nB=two\n")
    assert parse_env_file(path) == {"A": "1", "B": "two"}


def test_skips_comments_and_blank_lines(write_env):
    path = write_env("# comment\n\nA=1\n")
    assert parse_env_file(path) == {"A": "1"}


def test_ignores_lines_without_equals(write_env):
    path = write_env("just some text\nA=1\n")
    assert parse_env_file(path) == {"A": "1"}


def test_handles_export_prefix(write_env):
    path = write_env("export A=1\n")
    assert parse_env_file(path) == {"A": "1"}


def test_strips_matching_quotes(write_env):
    path = write_env("A=\"double\"\nB='single'\n")
    assert parse_env_file(path) == {"A": "double", "B": "single"}


def test_value_may_contain_equals_signs(write_env):
    path = write_env("URL=postgres://u:p@host/db?x=1=2\n")
    assert parse_env_file(path)["URL"] == "postgres://u:p@host/db?x=1=2"


def test_empty_value(write_env):
    path = write_env("EMPTY=\n")
    assert parse_env_file(path) == {"EMPTY": ""}


def test_spaces_around_equals(write_env):
    path = write_env("SPACED = hello\n")
    assert parse_env_file(path) == {"SPACED": "hello"}


def test_strips_inline_comment_from_unquoted_value(write_env):
    path = write_env("PORT=8000 # the port\n")
    assert parse_env_file(path) == {"PORT": "8000"}


def test_hash_without_leading_space_is_kept(write_env):
    path = write_env("LINK=http://x.com/a#b\n")
    assert parse_env_file(path) == {"LINK": "http://x.com/a#b"}


def test_hash_inside_quotes_is_kept(write_env):
    path = write_env('MSG="hello # world"\n')
    assert parse_env_file(path) == {"MSG": "hello # world"}


def test_matches_python_dotenv_on_tricky_file():
    path = FIXTURES / "tricky.env"
    assert parse_env_file(path) == dict(dotenv_values(path))