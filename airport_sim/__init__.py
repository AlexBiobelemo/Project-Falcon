"""Airport Sim project initialization.

Includes optional self-ping keep-alive for preventing platform sleep on Render.
"""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

# Optional self-ping keep-alive (auto-enabled on Render). Avoid starting it
# during common management commands (collectstatic/migrate/etc.).
try:
    _argv = " ".join(sys.argv).lower()
    _skip = any(
        cmd in _argv
        for cmd in (
            "collectstatic",
            "migrate",
            "makemigrations",
            "createsuperuser",
            "shell",
            "check",
            "test",
        )
    )
    if not _skip:
        from core.self_ping import start_self_ping

        start_self_ping()
        logger.debug("Self-ping initialization attempted")
except Exception as e:  # pragma: no cover
    logger.debug(f"Self-ping not started: {e}")
