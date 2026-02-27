"""
app/scheduler.py — Cron scheduler for the Autonomous Project Monitor

Uses APScheduler to run run_all_monitors() on a configurable interval.
Integrates with FastAPI lifespan so the scheduler starts/stops with the server.

Install: pip install apscheduler
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.monitor import run_all_monitors
from app.config import MONITOR_CRON_HOUR, MONITOR_CRON_MINUTE

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC")


async def _monitor_job():
    """Wrapper so APScheduler can call the async monitor."""
    logger.info("[Scheduler] Triggered monitor cycle")
    try:
        alerts = await run_all_monitors()
        if alerts:
            logger.warning(f"[Scheduler] {len(alerts)} alert(s) generated this cycle")
    except Exception as e:
        logger.error(f"[Scheduler] Monitor cycle failed: {e}")


def start_scheduler():
    """
    Schedules the monitor job and starts APScheduler.

    Default: runs daily at 06:00 UTC (configurable via config.py).
    Change MONITOR_CRON_HOUR / MONITOR_CRON_MINUTE in config.py.
    """
    scheduler.add_job(
        _monitor_job,
        trigger=CronTrigger(hour=MONITOR_CRON_HOUR, minute=MONITOR_CRON_MINUTE),
        id="project_monitor",
        replace_existing=True,
        misfire_grace_time=3600,  # run if missed by up to 1hr
    )
    scheduler.start()
    logger.info(
        f"[Scheduler] Project monitor scheduled daily at "
        f"{MONITOR_CRON_HOUR:02d}:{MONITOR_CRON_MINUTE:02d} UTC"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped")


# ──────────────────────────────────────────────
# FastAPI lifespan integration
# ──────────────────────────────────────────────
# In your api.py, replace the existing app = FastAPI() with:
#
#   from app.scheduler import lifespan
#   app = FastAPI(lifespan=lifespan)
#
@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager — starts scheduler on boot, stops on shutdown."""
    start_scheduler()
    yield
    stop_scheduler()


# ──────────────────────────────────────────────
# Manual trigger (for testing / admin endpoint)
# ──────────────────────────────────────────────
async def trigger_now():
    """
    Manually trigger a monitor cycle immediately.
    Called by POST /monitor/trigger in api.py.
    """
    return await run_all_monitors()