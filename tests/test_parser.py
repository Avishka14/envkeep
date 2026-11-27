from pathlib import Path

import pytest
from dotenv import dotenv_values

from envkeep.parser import EnvSyntaxError, parse_env_file, parse_env_text

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


def test_multiline_quoted_value_is_one_variable():
    text = 'TOKEN="line1\n# not-a-comment\nline3"\nB=2\n'
    assert parse_env_text(text) == {"TOKEN": "line1\n# not-a-comment\nline3", "B": "2"}


def test_lines_inside_a_multiline_value_are_not_variables():
    text = 'PRIVATE="-----BEGIN\nFAKE=leak\n-----END"\n'
    assert list(parse_env_text(text)) == ["PRIVATE"]


def test_escaped_quote_does_not_end_the_value():
    text = 'A="say \\"hi\\""\nB=2\n'
    assert list(parse_env_text(text)) == ["A", "B"]


def test_quoted_value_followed_by_inline_comment():
    assert parse_env_text('A="x" # note\n') == {"A": "x"}


def test_unterminated_quote_raises_with_line_number():
    with pytest.raises(EnvSyntaxError, match="line 2"):
        parse_env_text('A=1\nB="never closed\nC=3\n')


def test_multiline_matches_python_dotenv(write_env):
    path = write_env('KEY="line1\n# inside value\nline3"\nOTHER=2\n')
    assert parse_env_file(path) == dict(dotenv_values(path))


def test_double_quoted_escapes_are_decoded():
    text = r'A="x\"y\\z\nw"' + "\n"
    assert parse_env_text(text) == {"A": 'x"y\\z\nw'}


def test_single_quoted_only_decodes_backslash_and_quote():
    text = r"B='it\'s \\ \n'" + "\n"
    assert parse_env_text(text) == {"B": "it's \\ \\n"}  # \n stays two characters


def test_escapes_match_python_dotenv(write_env):
    path = write_env(r"""A="x\"y\\z\nw"
B='it\'s \\ \n'
""")
    assert parse_env_file(path) == dict(dotenv_values(path))
