import pytest


@pytest.fixture
def write_env(tmp_path):
    """Return a function that writes text to a temp file and returns its Path."""

    def _write(text: str, name: str = ".env"):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    return _write