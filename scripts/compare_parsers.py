from pathlib import Path

from dotenv import dotenv_values

from envkeep.parser import parse_env_file

path = Path("tests/fixtures/tricky.env")
mine = parse_env_file(path)
reference = dict(dotenv_values(path))

print("Identical:", mine == reference)
for key in sorted(set(mine) | set(reference)):
    if mine.get(key) != reference.get(key):
        print(f"  {key}: mine={mine.get(key)!r}  dotenv={reference.get(key)!r}")
