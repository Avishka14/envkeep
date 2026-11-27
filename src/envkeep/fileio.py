import os
import shutil
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    """Replace the contents of an existing file without ever leaving it half-written.

    The text goes into a temporary file in the same directory first. The original
    is replaced only after that write has been flushed to disk. If anything fails,
    the temporary file is removed and the original is left as it was.
    Newlines are written exactly as given (no translation).
    """
    target = (
        path.resolve()
    )  # follow symlinks, so we replace the real file, not the link
    fd, tmp_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())  # make sure the bytes are on disk before swapping
        if target.exists():
            shutil.copymode(
                target, tmp_path
            )  # mkstemp creates 0600; restore the original mode
        os.replace(tmp_path, target)  # atomic on the same filesystem
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
