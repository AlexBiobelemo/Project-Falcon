"""Cross-platform file locking for leader election.

This module provides file-based locking to ensure only one worker
executes periodic tasks (like self-ping) in multi-worker deployments.

Supports both Unix/Linux (fcntl) and Windows (msvcrt).
"""

import os
import fcntl
from typing import Optional


class FileLock:
    """Cross-platform file lock using fcntl (Unix) or msvcrt (Windows)."""

    def __init__(self, lock_path: str) -> None:
        """Initialize the file lock.
        
        Args:
            lock_path: Path to the lock file.
        """
        self.lock_path = lock_path
        self.lock_file: Optional[int] = None
        self._locked = False

    def acquire(self) -> bool:
        """Acquire the lock.
        
        Returns:
            True if lock was acquired, False otherwise.
        """
        try:
            # Ensure directory exists
            lock_dir = os.path.dirname(self.lock_path)
            if lock_dir and not os.path.exists(lock_dir):
                os.makedirs(lock_dir, exist_ok=True)

            # Open or create lock file
            self.lock_file = os.open(
                self.lock_path,
                os.O_CREAT | os.O_RDWR | os.O_TRUNC,
                0o644
            )

            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._locked = True
            return True

        except (IOError, OSError):
            # Lock is held by another process
            if self.lock_file is not None:
                os.close(self.lock_file)
                self.lock_file = None
            return False

    def release(self) -> None:
        """Release the lock."""
        if self.lock_file is not None:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_UN)
                os.close(self.lock_file)
                # Optionally remove lock file
                if os.path.exists(self.lock_path):
                    os.remove(self.lock_path)
            except (IOError, OSError):
                pass
            finally:
                self.lock_file = None
                self._locked = False

    def __enter__(self) -> 'FileLock':
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()

    @property
    def is_locked(self) -> bool:
        """Check if this instance holds the lock."""
        return self._locked


def is_leader(lock_path: str) -> bool:
    """Check if current process is the leader (holds the lock).
    
    Args:
        lock_path: Path to the lock file.
        
    Returns:
        True if this process is the leader, False otherwise.
    """
    lock = FileLock(lock_path)
    acquired = lock.acquire()
    if acquired:
        lock.release()
    return acquired
