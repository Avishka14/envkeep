from envkeep.generator import generate_example
from envkeep.parser import parse_env_file


def test_strips_values_and_keeps_comments():
    text = "# Database\nDATABASE_URL=postgres://u:p@h/db\n\nPORT=8000 # inline\n"
    assert generate_example(text) == "# Database\nDATABASE_URL=\n\nPORT=\n"


def test_keeps_export_prefix():
    assert generate_example('export SECRET_KEY="abc"\n') == "export SECRET_KEY=\n"


def test_uses_placeholder():
    assert generate_example("A=1\nB=2\n", placeholder="change-me") == "A=change-me\nB=change-me\n"


def test_value_with_equals_signs_is_fully_removed():
    assert generate_example("URL=a=b=c\n") == "URL=\n"


def test_drops_stray_lines_without_equals():
    assert generate_example("A=1\nsecret-token-here\n") == "A=\n"


def test_empty_input_gives_empty_output():
    assert generate_example("") == ""


def test_generated_file_has_the_same_keys_and_no_values(write_env):
    env = write_env('A=1\nexport B=2\n# note\nC="x y"\n')
    generated = write_env(generate_example(env.read_text(encoding="utf-8")), "example.env")

    values = parse_env_file(generated)
    assert list(values) == ["A", "B", "C"]
    assert set(values.values()) == {""}