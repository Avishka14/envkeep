from pathlib import Path

from envkeep.compare import compare
from envkeep.parser import parse_env_file

example = parse_env_file(Path("tests/fixtures/example.env"))
env = parse_env_file(Path("tests/fixtures/dev.env"))

result = compare(example, env)
print("Missing:", result.missing)
print("Extra:  ", result.extra)
print("Empty:  ", result.empty)
print("OK?     ", result.ok)
