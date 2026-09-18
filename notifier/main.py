from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

from .telegram import (
    format_active_call_reminder,
    format_doctor_alert,
    format_no_data_alert,
    format_overdue_escalation,
    format_relative_alert,
    poll_telegram_messages,
    send_telegram_message,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nazorat.notifier")

ALERT_COOLDOWN_HOURS = int(os.getenv("ALERT_COOLDOWN_HOURS", "6"))
NO_DATA_MINUTES = int(os.getenv("NO_DATA_MINUTES", "45"))
DATABASE_URL = os.getenv("DATABASE_URL", "")


async def check_task_escalations():
    """Job 1: Checks open tasks for 20h reminder and 24h escalation."""
    logger.info("[Job 1] Checking task escalations and reminders...")
    now = datetime.now(timezone.utc)

    # In production with DB session:
    # Query tasks where status in ('created', 'sent', 'seen')
    # If due_at - now <= 4h and reminded_at is None: send reminder
    # If now > due_at: mark overdue, send escalation


async def check_alert_signals():
    """Job 2: Observes alert level transitions (green -> amber -> red)."""
    logger.info("[Job 2] Checking latest alert level changes...")
    # Compares latest alert level with previous alert level
    # Only triggers when alert level increases
    # Creates red_alert task if level == 'red'


async def check_no_data():
    """Job 3: Observes devices with no readings > 45 minutes."""
    logger.info("[Job 3] Checking no_data devices...")


async def main():
    logger.info("NAZORAT Notifier service starting...")
    logger.info("Config: COOLDOWN=%sh, NO_DATA=%smin", ALERT_COOLDOWN_HOURS, NO_DATA_MINUTES)

    # Send startup test message / log
    await send_telegram_message(
        chat_id="demo_admin",
        text="<b>NAZORAT Notifier</b> servisi muvaffaqiyatli ishga tushdi.",
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_task_escalations, "interval", minutes=5)
    scheduler.add_job(check_alert_signals, "interval", minutes=1)
    scheduler.add_job(check_no_data, "interval", minutes=15)

    scheduler.start()
    logger.info("Scheduler started with 3 background monitoring jobs.")

    # Launch background Telegram message poller
    polling_task = asyncio.create_task(poll_telegram_messages())

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Notifier service stopped.")


if __name__ == "__main__":
    asyncio.run(main())
