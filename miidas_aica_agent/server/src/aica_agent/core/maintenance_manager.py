import asyncio
import aiohttp
import logging
import os
from utils.const import LOGGER_PREFIX

logger = logging.getLogger(f"{LOGGER_PREFIX}.{__name__}")

IS_MAINTENANCE_MODE: bool = False
MAINTENANCE_JSON_URL = os.getenv("AICA_AGENT_MAINTENANCE_JSON_URL")
POLLING_INTERVAL_SECONDS = 30

poller_task: asyncio.Task | None = None
session: aiohttp.ClientSession | None = None


async def setup_aiohttp_session():
    global session
    session = aiohttp.ClientSession()


async def shutdown_aiohttp_session():
    global session
    if session:
        await session.close()


async def startup_poller():
    global poller_task
    await setup_aiohttp_session()

    poller_task = asyncio.create_task(maintenance_flag_poller())
    logger.info("Maintenance flag poller task scheduled.")
    return poller_task


async def shutdown_poller():
    global poller_task
    if poller_task:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            pass

    await shutdown_aiohttp_session()
    logger.info("Maintenance flag poller task cancelled and aiohttp session closed.")


async def maintenance_flag_poller():
    """
    定期的にメンテナンスフラグをチェックし、グローバル変数を更新する
    """
    global IS_MAINTENANCE_MODE

    logger.info(
        "Maintenance flag poller started, checking every %d seconds.",
        POLLING_INTERVAL_SECONDS,
    )

    while True:
        new_status = await fetch_maintenance_flag()

        logger.debug("Fetched maintenance flag: %s", new_status)

        if new_status != IS_MAINTENANCE_MODE:
            logger.info(
                "Maintenance flag changed: %s -> %s",
                IS_MAINTENANCE_MODE,
                new_status,
            )

        IS_MAINTENANCE_MODE = new_status

        await asyncio.sleep(POLLING_INTERVAL_SECONDS)


async def fetch_maintenance_flag() -> bool:
    """
    JSONファイルを読み込み、isMaintenanceの状態を返す
    Returns:
        bool: メンテナンスモードが有効かどうか
    """
    if session is None:
        logger.error("aiohttp session is not initialized.")
        return IS_MAINTENANCE_MODE

    if MAINTENANCE_JSON_URL is None or MAINTENANCE_JSON_URL.strip() == "":
        logger.error("AICA_AGENT_MAINTENANCE_JSON_URL is not set. Polling is disabled.")
        return IS_MAINTENANCE_MODE

    try:
        async with session.get(
            MAINTENANCE_JSON_URL, headers={"Cache-Control": "no-cache, must-revalidate"}
        ) as response:
            response.raise_for_status()

            data = await response.json()

            return bool(data.get("isMaintenance", False))

    except aiohttp.ClientError:
        logger.exception("Failed to fetch maintenance flag (aiohttp Client Error)")
        return IS_MAINTENANCE_MODE
    except Exception:
        logger.exception("Failed to fetch maintenance flag (General Error)")
        return IS_MAINTENANCE_MODE
