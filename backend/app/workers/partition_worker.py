from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy import text

from app.core.db import get_db_context, get_engine

logger = logging.getLogger("wmax.workers.partition_worker")


async def ensure_readings_partitions() -> None:
    """Ensures readings partitions for current, past, and upcoming 3 months exist."""
    engine = get_engine()
    if engine.dialect.name != "postgresql":
        return

    now = datetime.now(timezone.utc)
    # Check from -1 month to +3 months
    months_to_check = [now + relativedelta(months=i) for i in range(-1, 4)]

    async with get_db_context() as session:
        try:
            # Ensure default partition exists
            await session.execute(text("CREATE TABLE IF NOT EXISTS readings_default PARTITION OF readings DEFAULT;"))
        except Exception as e:
            logger.debug(f"Default partition check: {e}")

        for dt in months_to_check:
            start_date = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + relativedelta(months=1))
            part_name = f"readings_{start_date.strftime('%Y_%m')}"
            
            try:
                exists_check = await session.execute(text(f"SELECT to_regclass('{part_name}');"))
                if exists_check.scalar():
                    continue

                sql = f"""
                CREATE TABLE IF NOT EXISTS {part_name}
                PARTITION OF readings
                FOR VALUES FROM ('{start_date.strftime('%Y-%m-%d %H:%M:%S%z')}')
                TO ('{end_date.strftime('%Y-%m-%d %H:%M:%S%z')}');
                """
                await session.execute(text(sql))
                await session.commit()
                logger.debug(f"Ensured partition: {part_name}")
            except Exception as err:
                await session.rollback()
                logger.debug(f"Partition {part_name} creation skipped: {err}")


async def run_partition_worker(interval_seconds: int = 86400) -> None:
    """Periodically runs partition maintenance once every day."""
    logger.info("Partition maintenance worker started.")
    while True:
        try:
            await ensure_readings_partitions()
        except Exception as e:
            logger.error(f"Partition maintenance error: {e}")
        await asyncio.sleep(interval_seconds)
