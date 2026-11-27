import os
import stat

import pytest

from envkeep.fileio import atomic_write_text


def test_replaces_content(tmp_path):
    path = tmp_path / ".env"
    path.write_text("old", encoding="utf-8")

    atomic_write_text(path, "new")

    assert path.read_text(encoding="utf-8") == "new"


def test_does_not_translate_newlines(tmp_path):
    path = tmp_path / ".env"
    path.write_bytes(b"A=1\r\n")

    atomic_write_text(path, "A=1\r\nB=2\r\n")

    assert path.read_bytes() == b"A=1\r\nB=2\r\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_preserves_permissions(tmp_path):
    path = tmp_path / ".env"
    path.write_text("old", encoding="utf-8")
    path.chmod(0o640)

    atomic_write_text(path, "new")

    assert stat.S_IMODE(path.stat().st_mode) == 0o640


def test_failure_keeps_original_and_removes_temp_file(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("old", encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("envkeep.fileio.os.replace", boom)

    with pytest.raises(OSError):
        atomic_write_text(path, "new")

    assert path.read_text(encoding="utf-8") == "old"
    assert [p.name for p in tmp_path.iterdir()] == [".env"]  # no leftover .tmp file


@pytest.mark.skipif(os.name == "nt", reason="symlinks need extra privileges on Windows")
def test_writes_through_symlink(tmp_path):
    real = tmp_path / "real.env"
    real.write_text("old", encoding="utf-8")
    link = tmp_path / "link.env"
    link.symlink_to(real)

    atomic_write_text(link, "new")

    assert link.is_symlink()
    assert real.read_text(encoding="utf-8") == "new"
