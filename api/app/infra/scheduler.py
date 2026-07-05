"""APScheduler setup for month-end snapshots and optional price fetching."""
from __future__ import annotations

import datetime
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Register jobs and start the scheduler."""
    # Month-end net-worth snapshot: runs at 23:55 on the last day of every month
    scheduler.add_job(
        _run_month_end_snapshot,
        CronTrigger(day="last", hour=23, minute=55),
        id="month_end_snapshot",
        replace_existing=True,
    )

    # Daily price fetch: runs at 18:30 UTC (after European market close) if configured
    scheduler.add_job(
        _run_daily_price_fetch,
        CronTrigger(hour=18, minute=30),
        id="daily_price_fetch",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)


async def _run_month_end_snapshot() -> None:
    """Import here to avoid circular imports."""
    from app.domains.networth.service import NetWorthService
    from app.infra.db import async_session_factory

    logger.info("Running month-end net-worth snapshot…")
    async with async_session_factory() as session:
        svc = NetWorthService(session)
        await svc.take_snapshot()
    logger.info("Month-end snapshot complete.")


async def _run_daily_price_fetch() -> None:
    """
    Fetch EOD prices for all instruments in the DB if a price provider is configured.
    No-op if PRICE_PROVIDER_URL is not set (default).
    Never sends user holdings — only ISIN codes + date.
    """
    from app.domains.investments.service import InvestmentService
    from app.infra.db import async_session_factory
    from app.infra.price_provider import get_price_provider

    today = datetime.date.today()

    async with async_session_factory() as session:
        provider = await get_price_provider(session)
        if provider is None:
            return  # Price provider disabled (default)

        logger.info("Daily price fetch: fetching EOD prices for %s…", today)
        svc = InvestmentService(session)
        instruments = await svc.list_instruments()
        if not instruments:
            logger.info("No instruments found — skipping price fetch.")
            return

        isins = [i.isin for i in instruments if i.isin]
        if not isins:
            return

        try:
            prices = await provider.fetch_prices(isins, today)
        except Exception as exc:
            logger.warning("Price fetch failed: %s", exc)
            return

        count = 0
        for isin, price in prices.items():
            # Find instrument by ISIN
            instr = next((i for i in instruments if i.isin == isin), None)
            if instr is None:
                continue
            from app.domains.investments.schemas import PriceCreateIn
            try:
                await svc.create_price(PriceCreateIn(
                    instrument_id=instr.id,
                    date=today,
                    close=price,
                ))
                count += 1
            except Exception:
                pass  # Duplicate date — already have price for today

        logger.info("Daily price fetch complete: %d prices stored.", count)
