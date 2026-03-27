"""Self-ping keep-alive system for preventing platform sleep.

Periodically sends HTTP requests to the app's own health endpoint to keep
platforms (like Render) from sleeping the service due to inactivity.
"""

from __future__ import annotations

import logging
import os
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger(__name__)

# Optional dependencies - keep app booting even if these aren't installed.
try:
    from apscheduler.schedulers.background import BackgroundScheduler

    APSCHEDULER_AVAILABLE = True
except Exception:  # pragma: no cover
    APSCHEDULER_AVAILABLE = False
    logger.debug("APScheduler not available, self-ping disabled")


def _env_truthy(name: str, default: str = "0") -> bool:
    value = os.environ.get(name, default).strip().lower()
    return value in ("1", "true", "yes", "on")


def _urljoin(base: str, path: str) -> str:
    if not base.endswith("/"):
        base += "/"
    if path.startswith("/"):
        path = path[1:]
    return base + path


def start_self_ping() -> None:
    """Start the self-ping keep-alive scheduler (best-effort)."""
    if not APSCHEDULER_AVAILABLE:
        logger.debug("Self-ping skipped: APScheduler or requests not available")
        return

    # Auto-enable on Render when RENDER_EXTERNAL_URL is present.
    on_render = "RENDER" in os.environ or bool(os.environ.get("RENDER_EXTERNAL_URL", "").strip())
    enabled = _env_truthy("SELF_PING_ENABLED", "1" if on_render else "0")
    if not enabled:
        logger.debug("Self-ping disabled by configuration")
        return

    lock_path = os.environ.get(
        "SELF_PING_LOCK_PATH",
        "/tmp/falcon-self-ping.lock"
        if os.name != "nt"
        else os.path.join(os.environ.get("TEMP", ""), "falcon-self-ping.lock"),
    )

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
    full_health = _env_truthy("SELF_PING_FULL", "1" if on_render else "0")
    if full_health and path.startswith("/core/health/") and "full=" not in path:
        path = path + ("&" if "?" in path else "?") + "full=1"

    if _env_truthy("SELF_PING_FORCE_HTTPS", "1") and base_url.startswith("http://"):
        base_url = "https://" + base_url[7:]

    ping_url = _urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

    interval_minutes = int(os.environ.get("SELF_PING_INTERVAL_MINUTES", "12"))
    timeout_seconds = int(os.environ.get("SELF_PING_TIMEOUT_SECONDS", "6"))

    logger.info(
        f"Self-ping configured: URL={ping_url}, interval={interval_minutes}m, timeout={timeout_seconds}s"
    )

    def ping_self() -> None:
        from .utils.process_lock import FileLock

        lock = FileLock(lock_path)
        if not lock.acquire():
            logger.debug("Self-ping skipped: not the leader")
            return

        try:
            logger.debug(f"Sending self-ping to {ping_url}")
            req = urllib.request.Request(
                ping_url,
                headers={"User-Agent": "falcon-self-ping/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                status = getattr(resp, "status", 200)
            if 200 <= status < 400:
                logger.debug(f"Self-ping successful: {status}")
            else:
                logger.warning(f"Self-ping returned non-success status: {status}")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            logger.warning(f"Self-ping failed: {e}")
        except Exception as e:  # pragma: no cover
            logger.error(f"Self-ping unexpected error: {e}")
        finally:
            lock.release()

    try:
        scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
        scheduler.add_job(
            ping_self,
            "interval",
            minutes=interval_minutes,
            max_instances=1,
            coalesce=True,
            id="falcon_self_ping",
        )
        scheduler.start()
        logger.info(f"Self-ping scheduler started (interval: {interval_minutes} minutes)")
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to start self-ping scheduler: {e}")
