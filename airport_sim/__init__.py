"""Airport Sim project initialization.

This module handles project-level initialization including optional
self-ping keep-alive for preventing platform sleep on Render.
"""

import logging

logger = logging.getLogger(__name__)

# Optional self-ping keep-alive (auto-enabled on Render)
try:
    from core.self_ping import start_self_ping
    start_self_ping()
    logger.debug("Self-ping initialization attempted")
except Exception as e:
    logger.debug(f"Self-ping not started: {e}")
