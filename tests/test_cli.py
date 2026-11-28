import os

import pytest
from typer.testing import CliRunner

from envkeep.cli import app

runner = CliRunner()


def run(*args):
    return runner.invoke(app, [str(arg) for arg in args])


# check


def test_check_passes_when_files_match(write_env):
    example = write_env("A=1\nB=2\n", "example.env")
    env = write_env("A=x\nB=y\n", "good.env")

    result = run("check", "--env", env, "--example", example)

    assert result.exit_code == 0


def test_check_fails_with_exit_code_1(write_env):
    example = write_env("A=1\nSECRET_KEY=x\n", "example.env")
    env = write_env("A=1\n", "dev.env")

    result = run("check", "--env", env, "--example", example)

    assert result.exit_code == 1
    assert "SECRET_KEY" in result.output


def test_check_missing_file_exits_with_code_2(write_env, tmp_path):
    example = write_env("A=1\n", "example.env")

    result = run("check", "--env", tmp_path / "nope.env", "--example", example)

    assert result.exit_code == 2
    assert "file not found" in result.output


def test_square_brackets_in_paths_do_not_crash(write_env, tmp_path):
    # Regression test: Rich once treated "[/red]" in a path as markup and crashed.
    example = write_env("A=1\n", "example.env")

    result = run("check", "--env", tmp_path / "weird[/red].env", "--example", example)

    assert result.exit_code == 2


SCHEMA = """\
variables:
  DATABASE_URL:
    type: url
  PORT:
    type: int
    default: 8000
  SECRET_KEY:
"""


def test_check_with_schema_passes(write_env):
    schema = write_env(SCHEMA, "envkeep.yml")
    env = write_env("DATABASE_URL=postgres://u:p@h:5432/db\nSECRET_KEY=x\n")

    result = run("check", "--env", env, "--schema", schema)

    assert result.exit_code == 0


def test_check_with_schema_reports_missing_required(write_env):
    schema = write_env(SCHEMA, "envkeep.yml")
    env = write_env("DATABASE_URL=postgres://u:p@h:5432/db\n")

    result = run("check", "--env", env, "--schema", schema)

    assert result.exit_code == 1
    assert "SECRET_KEY" in result.output


def test_check_with_schema_reports_invalid_value_without_printing_it(write_env):
    schema = write_env(SCHEMA, "envkeep.yml")
    env = write_env(
        "DATABASE_URL=postgres://u:p@h/db\nPORT=supersecret\nSECRET_KEY=x\n"
    )

    result = run("check", "--env", env, "--schema", schema)

    assert result.exit_code == 1
    assert "PORT" in result.output
    assert "invalid" in result.output
    assert "supersecret" not in result.output


def test_check_with_schema_accepts_empty_value_for_variable_with_default(write_env):
    schema = write_env(SCHEMA, "envkeep.yml")
    env = write_env("DATABASE_URL=postgres://u:p@h/db\nPORT=\nSECRET_KEY=x\n")

    result = run("check", "--env", env, "--schema", schema)

    assert result.exit_code == 0


def test_check_with_invalid_schema_exits_with_code_2(write_env):
    schema = write_env("variables:\n  A:\n    type: color\n", "envkeep.yml")
    env = write_env("A=1\n")

    result = run("check", "--env", env, "--schema", schema)

    assert result.exit_code == 2
    assert "unknown type" in result.output


def test_check_with_missing_schema_file_exits_with_code_2(write_env, tmp_path):
    env = write_env("A=1\n")

    result = run("check", "--env", env, "--schema", tmp_path / "nope.yml")

    assert result.exit_code == 2
    assert "file not found" in result.output


def test_schema_replaces_example(write_env, tmp_path):
    schema = write_env(SCHEMA, "envkeep.yml")
    env = write_env("DATABASE_URL=postgres://u:p@h/db\nSECRET_KEY=x\n")

    # --example points at a file that doesn't exist; it must be ignored when --schema is used
    result = run(
        "check", "--env", env, "--schema", schema, "--example", tmp_path / "nope"
    )

    assert result.exit_code == 0


# generate


def test_generate_writes_example_file(write_env, tmp_path):
    env = write_env("# db\nA=secret\n")
    output = tmp_path / ".env.example"

    result = run("generate", "--env", env, "--output", output)

    assert result.exit_code == 0
    assert output.read_text(encoding="utf-8") == "# db\nA=\n"


def test_generate_refuses_to_overwrite_without_force(write_env, tmp_path):
    env = write_env("A=1\n")
    output = write_env("OLD=content\n", ".env.example")

    result = run("generate", "--env", env, "--output", output)

    assert result.exit_code == 2
    assert output.read_text(encoding="utf-8") == "OLD=content\n"


def test_generate_overwrites_with_force(write_env):
    env = write_env("A=1\n")
    output = write_env("OLD=content\n", ".env.example")

    result = run("generate", "--env", env, "--output", output, "--force")

    assert result.exit_code == 0
    assert output.read_text(encoding="utf-8") == "A=\n"


def test_generate_refuses_when_input_and_output_are_the_same_file(write_env):
    env = write_env("A=secret\n")

    result = run("generate", "--env", env, "--output", env, "--force")

    assert result.exit_code == 2
    assert env.read_text(encoding="utf-8") == "A=secret\n"


def test_generate_refuses_when_output_is_a_hard_link_to_env(write_env, tmp_path):
    env = write_env("A=secret\n")
    link = tmp_path / "linked.env.example"
    try:
        os.link(env, link)
    except (OSError, NotImplementedError):
        pytest.skip("hard links are not supported on this filesystem")

    result = run("generate", "--env", env, "--output", link, "--force")

    assert result.exit_code == 2
    assert env.read_text(encoding="utf-8") == "A=secret\n"


# sync


def test_sync_appends_missing_variables(write_env):
    example = write_env("A=1\nB=2\n", "example.env")
    env = write_env("A=custom\n")

    result = run("sync", "--env", env, "--example", example)

    text = env.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert text.startswith("A=custom\n")
    assert "B=2" in text


def test_sync_dry_run_does_not_write(write_env):
    example = write_env("A=1\nB=2\n", "example.env")
    env = write_env("A=custom\n")

    result = run("sync", "--env", env, "--example", example, "--dry-run")

    assert result.exit_code == 0
    assert "Would add" in result.output
    assert env.read_text(encoding="utf-8") == "A=custom\n"


def test_sync_makes_check_stop_reporting_missing(write_env):
    example = write_env("A=1\nB=2\n", "example.env")
    env = write_env("A=custom\n")

    run("sync", "--env", env, "--example", example)
    result = run("check", "--env", env, "--example", example)

    assert result.exit_code == 0


def test_sync_preserves_crlf_line_endings(write_env, tmp_path):
    example = write_env("A=1\nB=2\n", "example.env")
    env = tmp_path / ".env"
    env.write_bytes(b"A=custom\r\n")

    result = run("sync", "--env", env, "--example", example)

    data = env.read_bytes()
    assert result.exit_code == 0
    assert data.startswith(b"A=custom\r\n")  # existing line untouched
    assert b"B=2\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b"")  # no bare LF anywhere


def test_sync_write_failure_leaves_original_intact(write_env, monkeypatch):
    example = write_env("A=1\nB=2\n", "example.env")
    env = write_env("A=custom\n")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("envkeep.fileio.os.replace", boom)

    result = run("sync", "--env", env, "--example", example)

    assert result.exit_code == 2
    assert "could not write" in result.output
    assert env.read_text(encoding="utf-8") == "A=custom\n"


def test_generate_rejects_unterminated_quote_and_writes_nothing(write_env, tmp_path):
    env = write_env('A=1\nB="oops\nC=3\n')
    output = tmp_path / ".env.example"

    result = run("generate", "--env", env, "--output", output)

    assert result.exit_code == 2
    assert "unterminated" in result.output
    assert not output.exists()


def test_check_reports_unterminated_quote_with_exit_code_2(write_env):
    example = write_env("A=1\n", "example.env")
    env = write_env('A="oops\n')

    result = run("check", "--env", env, "--example", example)

    assert result.exit_code == 2


def test_sync_does_not_copy_trailing_comments_after_quoted_values(write_env):
    example = write_env('NAME="hello" # note\nTAG="a # b" # other\n', "example.env")
    env = write_env("A=1\n")

    result = run("sync", "--env", env, "--example", example)

    text = env.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "NAME=hello\n" in text
    assert 'TAG="a # b"\n' in text
    assert "# note" not in text
    assert "# other" not in text


# diff


def test_diff_identical_files_exit_0(write_env):
    a = write_env("A=1\n", "a.env")
    b = write_env("A=1\n", "b.env")

    result = run("diff", a, b)

    assert result.exit_code == 0
    assert "identical" in result.output


def test_diff_reports_differences_with_exit_code_1(write_env):
    a = write_env("ONLY_A=1\nSAME=1\n", "a.env")
    b = write_env("ONLY_B=1\nSAME=1\n", "b.env")

    result = run("diff", a, b)

    assert result.exit_code == 1
    assert "ONLY_A" in result.output
    assert "ONLY_B" in result.output
    assert "only in A" in result.output


def test_diff_hides_values_by_default(write_env):
    a = write_env("TOKEN=supersecret1\n", "a.env")
    b = write_env("TOKEN=supersecret2\n", "b.env")

    result = run("diff", a, b)

    assert result.exit_code == 1
    assert "TOKEN" in result.output
    assert "supersecret" not in result.output


def test_diff_show_values_prints_them(write_env):
    a = write_env("TOKEN=supersecret1\n", "a.env")
    b = write_env("TOKEN=supersecret2\n", "b.env")

    result = run("diff", a, b, "--show-values")

    assert "supersecret1" in result.output
    assert "supersecret2" in result.output


def test_diff_keys_only_ignores_value_differences(write_env):
    a = write_env("A=1\n", "a.env")
    b = write_env("A=2\n", "b.env")

    result = run("diff", a, b, "--keys-only")

    assert result.exit_code == 0
    assert "same variables" in result.output


def test_diff_missing_file_exits_with_code_2(write_env, tmp_path):
    a = write_env("A=1\n", "a.env")

    result = run("diff", a, tmp_path / "nope.env")

    assert result.exit_code == 2
