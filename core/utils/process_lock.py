"""Cross-platform file locking for leader election.

Used to ensure only one worker process executes periodic background tasks
(e.g. self-ping keep-alive) in multi-worker deployments.
"""

from __future__ import annotations

import os
from typing import Optional


class FileLock:
    """Cross-platform non-blocking file lock.

    - POSIX: uses `fcntl.flock`
    - Windows: uses `msvcrt.locking`
    """

    def __init__(self, lock_path: str) -> None:
        self.lock_path = lock_path
        self._fh: Optional[object] = None
        self._locked = False

    def acquire(self) -> bool:
        """Attempt to acquire the lock (non-blocking)."""
        if self._locked:
            return True

        try:
            lock_dir = os.path.dirname(self.lock_path)
            if lock_dir and not os.path.exists(lock_dir):
                os.makedirs(lock_dir, exist_ok=True)

            # Use a file handle so Windows locking works properly.
            self._fh = open(self.lock_path, "a+b")

            if os.name == "nt":
                import msvcrt

                # Lock 1 byte at the start of file.
                try:
                    msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    self._fh.close()
                    self._fh = None
                    return False
            else:
                import fcntl

                try:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    self._fh.close()
                    self._fh = None
                    return False

            self._locked = True
            return True
        except OSError:
            if self._fh is not None:
                try:
                    self._fh.close()
                except OSError:
                    pass
                self._fh = None
            return False

    def release(self) -> None:
        """Release the lock (best-effort)."""
        if self._fh is None:
            self._locked = False
            return

        try:
            if os.name == "nt":
                import msvcrt

                try:
                    self._fh.seek(0)
                    msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                try:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
        finally:
            try:
                self._fh.close()
            except OSError:
                pass
            self._fh = None
            self._locked = False

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    @property
    def is_locked(self) -> bool:
        return self._locked


def is_leader(lock_path: str) -> bool:
    """Return True if this process can acquire the lock."""
    lock = FileLock(lock_path)
    acquired = lock.acquire()
    if acquired:
        lock.release()
    return acquired

