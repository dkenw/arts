"""Publish related outputs only after all their files have been written."""

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory


@contextmanager
def _writer_lock(directory):
    """Serialize the short publish step for writers targeting this directory."""
    if os.name == "nt":
        import msvcrt
        with (directory / ".sailings-writer.lock").open("a+b") as lock:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            fcntl.flock(directory_fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(directory_fd)


@contextmanager
def staged_output(directory, *, discard=(), last=None):
    """Stage a set on the same filesystem. Replace only the named outputs."""
    directory = Path(directory)
    directory.parent.mkdir(parents=True, exist_ok=True)
    if directory.exists() and not directory.is_dir():
        raise NotADirectoryError(directory)
    with TemporaryDirectory(prefix=".sailings-", dir=directory if directory.is_dir() else directory.parent) as temp:
        stage = Path(temp)
        yield stage
        names = {file.name for file in stage.iterdir()}
        names.update(discard)
        if last is not None:
            names.remove(last)
        order = sorted(names)
        if last is not None:
            order.append(last)
        directory.mkdir(exist_ok=True)
        backup = stage / ".previous"
        backup.mkdir()
        with _writer_lock(directory):
            for name in order:
                old = directory / name
                if old.exists():
                    shutil.copyfile(old, backup / name)
            installed = []
            try:
                for name in order:
                    new = stage / name
                    target = directory / name
                    if new.exists():
                        new.replace(target)
                    else:
                        target.unlink(missing_ok=True)
                    installed.append(name)
            except BaseException:
                for name in reversed(installed):
                    if (backup / name).exists():
                        (backup / name).replace(directory / name)
                    else:
                        (directory / name).unlink(missing_ok=True)
                raise
