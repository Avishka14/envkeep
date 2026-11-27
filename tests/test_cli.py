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
