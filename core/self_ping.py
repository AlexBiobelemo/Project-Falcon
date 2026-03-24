"""Self-ping keep-alive system for preventing platform sleep.

This module implements a self-ping mechanism that periodically sends HTTP requests
to the application's own health endpoint to prevent hosting platforms (like Render)
from putting the application to sleep due to inactivity.

Features:
- Automatic activation on Render when RENDER_EXTERNAL_URL is set
- Leader election via file locking to prevent multi-worker ping storms
- Configurable ping interval, timeout, and endpoint
- HTTPS enforcement option

Usage:
    Call start_self_ping(app) during Django app initialization.
"""

import os
import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Optional dependencies - gracefully handle if not installed
try:
    import requests
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.debug("APScheduler or requests not available, self-ping disabled")


def _env_truthy(name: str, default: str = "0") -> bool:
    """Check if an environment variable is truthy.
    
    Args:
        name: Environment variable name.
        default: Default value if not set.
        
    Returns:
        True if the value is truthy ('1', 'true', 'yes', etc.).
    """
    value = os.environ.get(name, default).strip().lower()
    return value in ("1", "true", "yes", "on")


def start_self_ping() -> None:
    """Start the self-ping keep-alive scheduler.
    
    This function:
    1. Checks if self-ping is enabled (auto-enabled on Render)
    2. Constructs the ping URL from environment variables
    3. Sets up leader election via file locking
    4. Schedules periodic HTTP GET requests to the health endpoint
    
    The scheduler runs in a background thread and only one worker
    (the "leader") will send pings at any given time.
    """
    if not APSCHEDULER_AVAILABLE:
        logger.debug("Self-ping skipped: APScheduler or requests not available")
        return

    # Auto-enable on Render when RENDER_EXTERNAL_URL is present
    on_render = "RENDER" in os.environ or bool(os.environ.get("RENDER_EXTERNAL_URL", "").strip())
    enabled = _env_truthy("SELF_PING_ENABLED", "1" if on_render else "0")

    if not enabled:
        logger.debug("Self-ping disabled by configuration")
        return

    # Leader election configuration
    lock_path = os.environ.get(
        "SELF_PING_LOCK_PATH",
        "/tmp/falcon-self-ping.lock" if not os.name == "nt" else os.path.join(os.environ.get("TEMP", ""), "falcon-self-ping.lock")
    )

    # Construct ping URL
    base_url = (
        os.environ.get("SELF_PING_URL")
        or os.environ.get("RENDER_EXTERNAL_URL")
        or getattr(settings, "SELF_PING_BASE_URL", "")
        or ""
    ).strip()

    if not base_url:
        logger.warning("Self-ping enabled but no base URL configured")
        return

    path = (os.environ.get("SELF_PING_PATH") or "/core/health/").strip()
    
    # Force HTTPS if configured
    if _env_truthy("SELF_PING_FORCE_HTTPS", "1") and base_url.startswith("http://"):
        base_url = "https://" + base_url[7:]

    ping_url = _urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

    # Timing configuration
    interval_minutes = int(os.environ.get("SELF_PING_INTERVAL_MINUTES", "12"))
    timeout_seconds = int(os.environ.get("SELF_PING_TIMEOUT_SECONDS", "6"))

    logger.info(
        f"Self-ping configured: URL={ping_url}, interval={interval_minutes}m, timeout={timeout_seconds}s"
    )

    def ping_self() -> None:
        """Send a ping to the health endpoint.
        
        Only the leader (process holding the lock) will send the ping.
        """
        from .utils.process_lock import FileLock

        lock = FileLock(lock_path)
        
        if not lock.acquire():
            # Not the leader, skip this ping
            logger.debug("Self-ping skipped: not the leader")
            return

        try:
            logger.debug(f"Sending self-ping to {ping_url}")
            response = requests.get(
                ping_url,
                timeout=timeout_seconds,
                headers={"User-Agent": "falcon-self-ping/1.0"}
            )
            if response.status_code == 200:
                logger.debug(f"Self-ping successful: {response.status_code}")
            else:
                logger.warning(f"Self-ping returned non-200 status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Self-ping failed: {e}")
        except Exception as e:
            logger.error(f"Self-ping unexpected error: {e}")
        finally:
            lock.release()

    # Create and start the scheduler
    try:
        scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
        scheduler.add_job(
            ping_self,
            "interval",
            minutes=interval_minutes,
            max_instances=1,
            coalesce=True,
            id="falcon_self_ping"
        )
        scheduler.start()
        logger.info(f"Self-ping scheduler started (interval: {interval_minutes} minutes)")
    except Exception as e:
        logger.error(f"Failed to start self-ping scheduler: {e}")


def _urljoin(base: str, path: str) -> str:
    """Join base URL with path.
    
    Simple URL joining without requiring urllib.parse import.
    
    Args:
        base: Base URL.
        path: Path to append.
        
    Returns:
        Combined URL.
    """
    if not base.endswith("/"):
        base += "/"
    if path.startswith("/"):
        path = path[1:]
    return base + path
